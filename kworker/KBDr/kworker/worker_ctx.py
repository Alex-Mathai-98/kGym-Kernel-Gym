# kworker.py
import asyncio, json, platform
from signal import SIGTERM
import aio_pika, uuid
# from jsonschema import validate, ValidationError
from datetime import datetime
from typing import Callable, MutableMapping
from .job_process_ctx import JobProcessorContext

class WorkerContext:

    mq_conn: aio_pika.abc.AbstractRobustConnection | None = None
    job_queue: aio_pika.abc.AbstractRobustQueue | None = None
    control_queue: aio_pika.abc.AbstractRobustQueue | None = None
    callback_queue: aio_pika.abc.AbstractRobustQueue | None = None
    current_job: JobProcessorContext | None = None
    futures: MutableMapping[str, asyncio.Future] = {}

    def __init__(
        self,
        worker_name: str,
        conn_url: str,
        job_processor: Callable,
        argument_schema: dict
    ):
        self.worker_name = worker_name
        self.worker_hostname = platform.node()
        self.conn_url = conn_url
        self.job_processor = job_processor
        self.argument_schema = argument_schema

        self.__blocker_lock = asyncio.Lock()

    async def report_sys_log_async(self, message: str):
        """ Report system log to kscheduler """
        async with self.mq_conn.channel() as chan:
            msg = {
                "log-time": datetime.utcnow().isoformat(),
                "worker": self.worker_name,
                "worker-hostname": self.worker_hostname,
                "log": message
            }
            await chan.default_exchange.publish(
                aio_pika.Message(body=json.dumps(msg).encode()),
                routing_key='sys_log',
            )

    async def report_job_log_async(self, job_id: str, message: str):
        """ Report job log to kscheduler """
        async with self.mq_conn.channel() as chan:
            msg = {
                "job-id": job_id,
                "log-time": datetime.utcnow().isoformat(),
                "worker": self.worker_name,
                "worker-hostname": self.worker_hostname,
                "log": message
            }
            await chan.default_exchange.publish(
                aio_pika.Message(body=json.dumps(msg).encode()),
                routing_key='job_log',
            )

    async def callback_on_response(self, message: aio_pika.abc.AbstractIncomingMessage):
        future = self.futures.pop(message.correlation_id)
        future.set_result(json.loads(message.body.decode('utf-8')).get('job-ctx', None))

    async def focus_job(self, job_id: str) -> dict | None:
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.futures[correlation_id] = future

        async with self.mq_conn.channel() as chan:
            await chan.default_exchange.publish(
                aio_pika.Message(
                    json.dumps({
                        'job-id': job_id,
                        'worker-hostname': self.worker_hostname
                    }).encode(),
                    correlation_id=correlation_id,
                    reply_to=self.callback_queue.name,
                ),
                routing_key="job_focus",
            )

        return (await future)

    async def __consume_job(self, message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process(requeue=True):
            job_id = message.body.decode('utf-8')
            job_ctx = await self.focus_job(job_id)
            if isinstance(job_ctx, dict):
                # focus the job first;
                self.current_job = JobProcessorContext(self, job_ctx, self.job_processor)
                success, result = await self.current_job.run()
                self.current_job = None
                job_ctx['modified-time'] = datetime.utcnow().isoformat()
                async with self.mq_conn.channel() as chan:
                    await chan.default_exchange.publish(
                        aio_pika.Message(body=json.dumps({
                            'worker-hostname': self.worker_hostname,
                            'job-id': job_ctx['job-id'],
                            'success': success,
                            'result': result
                        }).encode()),
                        routing_key='job_update',
                    )

    async def __consume_control(self, message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process(requeue=False):
            payload = json.loads(message.body.decode('utf-8'))
            if payload['command'] == 'abort':
                if isinstance(self.current_job, JobProcessorContext) and \
                    self.current_job.job_ctx['job-id'] == payload['argument']['job-id'] and \
                    isinstance(self.current_job.current_task, asyncio.Task):
                    self.current_job.current_task.cancel()
                    await self.current_job.cleanup_handler(self.current_job)

    async def __signal_handler(self):
        # stop the task and async connection;
        await self.mq_conn.close()
        # restore connection for cleanup only;
        self.mq_conn = await aio_pika.connect_robust(self.conn_url)
        # ask job process to clean up;
        if isinstance(self.current_job, JobProcessorContext) and \
            isinstance(self.current_job.cleanup_handler, Callable):
            await self.current_job.cleanup_handler(self.current_job)
        await self.report_sys_log_async('Signal received: SIGTERM, terminating')
        await self.mq_conn.close()
        # let go;
        self.__blocker_lock.release()

    async def __blocker(self):
        await self.__blocker_lock.acquire()

    async def __main(self):
        self.mq_conn = await aio_pika.connect_robust(self.conn_url)

        await self.report_sys_log_async(f'{self.worker_name}@{self.worker_hostname} is listening')

        # job channel;
        job_chan = await self.mq_conn.channel()
        await job_chan.set_qos(prefetch_count=1)
        self.job_queue = await job_chan.get_queue(self.worker_name)

        # control channel;
        control_chan = await self.mq_conn.channel()
        await control_chan.set_qos(prefetch_count=1)
        self.control_queue = await job_chan.declare_queue(
            f'workers.{self.worker_hostname}', exclusive=True)

        # callback channel;
        callback_chan = await self.mq_conn.channel()
        await callback_chan.set_qos(prefetch_count=1)
        self.callback_queue = await callback_chan.declare_queue(exclusive=True)

        await self.callback_queue.consume(self.callback_on_response, no_ack=True)

        await self.control_queue.consume(self.__consume_control)
        await self.report_sys_log_async(
            f'Binded to queue `workers.{self.worker_hostname} and started to consume')

        await self.job_queue.consume(self.__consume_job)
        await self.report_sys_log_async(
            f'Binded to queue `{self.worker_name} and started to consume')

        # signal handler;
        asyncio.get_event_loop().add_signal_handler(
            SIGTERM,
            lambda: asyncio.create_task(self.__signal_handler())
        )

        # for blocker;
        await self.__blocker_lock.acquire()
        try:
            await self.__blocker()
        finally:
            pass

    def run(self):
        asyncio.run(self.__main())
