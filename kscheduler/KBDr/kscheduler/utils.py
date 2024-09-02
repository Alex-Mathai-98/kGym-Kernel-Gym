# utils.py
import asyncio
from typing import Callable, Any
from functools import partial

ISOTimeDefaultStart = '0000-00-00T00:00:00.000000'
ISOTimeDefaultEnd = '9999-99-99T99:99:99.999999'
ISOTimeRegex = "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6}$"
JobIDRegex = "^[0-9a-f]{8}$"

async def run_async(func: Callable, *args: Any, **kwargs: Any):
    return await asyncio.get_running_loop().run_in_executor(
        None,
        partial(func, *args, **kwargs)
    )

def paginated_response(total: int, result: list, start: int, limit: int):
    return {
        'result': result,
        'size': len(result),
        'next': -1 if len(result) == 0 or len(result) < limit else start + limit,
        'total': total
    }

def int2job_id(x: int):
    ret = hex(x)[2:]
    ret = ('0' * (8 - len(ret))) + ret
    return ret

def job_id2int(x: str):
    return int('0x' + x, 16)
