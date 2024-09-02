# mq.py
import os, json, aio_pika
from aio_pika import Message
from . import db

mq_conn: aio_pika.abc.AbstractRobustConnection = None

async def consume_sys_log(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        await db.insert_sys_log(json.loads(message.body.decode()))

async def consume_job_log(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        await db.insert_job_log(json.loads(message.body.decode()))

async def consume_job_update(message: aio_pika.abc.AbstractIncomingMessage):
    """
    Handling job update

    Message format:
    ```json
    {
        "worker-hostname": "",
        "job-id": "",
        "success": true|false
        "result": { ... }
    }
    ```
    """
    async with message.process():
        payload = json.loads(message.body.decode())
        # update the result whatsoever;
        success = payload.get('success', False)
        next_worker = await db.append_job_result(
            payload['job-id'], payload['worker-hostname'], success, payload.get('result', None))
        # hit the next worker;
        if success and isinstance(next_worker, str):
            await publish_job_id(payload['job-id'], next_worker)
        else:
            # abort;
            await db.abort_job(payload['job-id'])

async def consume_job_focus(message: aio_pika.abc.AbstractIncomingMessage):
    """
    Handling job focus change

    Message format:
    ```json
    {
        "job-id": "",
        "worker-hostname": ""
    }
    ```
    """
    async with message.process():
        focus = json.loads(message.body.decode())
        job_id = focus['job-id']
        worker_hostname = focus['worker-hostname']
        result = await db.focus_job(job_id, worker_hostname)
        receipt = {
            'result': 'focused' if result else 'reject'
        }
        if result:
            receipt['job-ctx'] = await db.get_job(job_id)
        async with mq_conn.channel() as chan:
            await chan.default_exchange.publish(
                Message(
                    body=json.dumps(receipt).encode('utf-8'),
                    correlation_id=message.correlation_id,
                ),
                routing_key=message.reply_to,
            )

async def abort_job(worker_hostname: str, job_id: str):
    async with mq_conn.channel() as chan:
        await chan.default_exchange.publish(
            aio_pika.Message(body=json.dumps({
                'command': 'abort',
                'argument': {
                    'job-id': job_id
                }
            }).encode()),
            routing_key=f"workers.{worker_hostname}",
        )

async def publish_job_id(job_id: str, worker_name: str):
    async with mq_conn.channel() as chan:
        await chan.default_exchange.publish(
            aio_pika.Message(body=job_id.encode()),
            routing_key=worker_name,
        )

async def init_mq():
    global mq_conn
    mq_conn = await aio_pika.connect_robust(os.environ['KBDR_SCHEDULER_RABBITMQ_CONN_URL'])
    channel = await mq_conn.channel()
    await channel.set_qos(prefetch_count=10)

    sys_log_queue = await channel.get_queue('sys_log')
    job_log_queue = await channel.get_queue('job_log')
    job_update_queue = await channel.get_queue('job_update')
    job_focus_queue = await channel.get_queue('job_focus')

    await sys_log_queue.consume(consume_sys_log)
    await job_log_queue.consume(consume_job_log)
    await job_update_queue.consume(consume_job_update)
    await job_focus_queue.consume(consume_job_focus)

async def close_mq():
    await mq_conn.close()
