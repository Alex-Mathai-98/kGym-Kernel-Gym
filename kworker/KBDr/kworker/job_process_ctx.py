# job_process_ctx.py
from typing import Callable
import asyncio, traceback

class JobProcessorContext:

    current_task: asyncio.Task | None = None
    cleanup_handler: Callable | None = None
    variables: dict = dict()

    def __init__(self, worker: 'WorkerContext', job_ctx: dict, processor: Callable):
        self.worker = worker
        self.job_ctx = job_ctx
        self.processor = processor

    def register_cleanup_handler(self, handler: Callable):
        self.cleanup_handler = handler

    async def run(self) -> tuple[bool, (dict | None)]:
        success, result = False, None
        try:
            self.current_task = asyncio.create_task(self.processor(self, self.job_ctx))
            success, result = await self.current_task
        except asyncio.exceptions.CancelledError as e:
            await self.worker.report_job_log_async(
                self.job_ctx['job-id'],
                'Job cancelled'
            )
        except Exception as e:
            await self.worker.report_job_log_async(
                self.job_ctx['job-id'],
                f'Python exception: {e} \n' + traceback.format_exc()
            )
        self.current_task = None
        return success, result
