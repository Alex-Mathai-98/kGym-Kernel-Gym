# utils.py
from typing import Any, Callable
import asyncio, functools

job_ctx_schema = {
    "type": "object",
    "properties": {
        "job-id": { "type": "string" },
        "created-time": { "type": "string" },
        "job-workers": {
            "type": "array",
            "items": { "type": "string" }
        },
        "current-worker": { "type": "number" },
        "status": { "type": "string" },
        "worker-results": {
            "type": "array",
            "items": { "type": "object" }
        },
        "worker-arguments": {
            "type": "array",
            "items": { "type": "object" }
        },
        "modified-time": { "type": "string" },
        "kv": { "type": "object" }
    },
    "required": [
        "job-id", "created-time", "job-workers", "current-worker",
        "status", "worker-results", "worker-arguments", "modified-time", "kv"
    ]
}

async def run_async(func: Callable, *args: Any, **kwargs: Any):
    return await asyncio.get_running_loop().run_in_executor(
        None,
        functools.partial(func, *args, **kwargs)
    )
