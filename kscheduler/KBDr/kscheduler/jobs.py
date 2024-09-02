# jobs.py
from typing import Annotated
from datetime import datetime
import os
from fastapi import APIRouter, Path, Query
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from google.cloud.storage import Client
from . import db
from .utils import ISOTimeRegex, JobIDRegex, ISOTimeDefaultStart, ISOTimeDefaultEnd, run_async
from . import mq

class RawJobArgument(BaseModel):
    job_workers: list[str]
    worker_arguments: list[dict]
    kv: dict[str, str]

def create_job_api_router() -> APIRouter:
    router = APIRouter(prefix='/jobs')

    @router.get('/')
    async def get_jobs(
        mode: Annotated[str, Query(pattern="^(by_modified_time|by_created_time)$")],
        start_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultStart,
        end_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultEnd,
        start: Annotated[int, Query(ge=0)]=0,
        limit: Annotated[int, Query(ge=0, le=50)]=20):
        if mode == 'by_created_time':
            result = await db.get_jobs_by_created_time(start_time, end_time, start, limit)
        elif mode == 'by_modified_time':
            result = await db.get_jobs_by_modified_time(start_time, end_time, start, limit)
        return result

    @router.get('/{job_id}')
    async def get_job(job_id: Annotated[str, Path(pattern=JobIDRegex)]):
        res = await db.get_job(job_id)
        if isinstance(res, dict):
            return res
        else:
            raise HTTPException(404, 'No such job')

    @router.get('/{job_id}/log')
    async def get_job_log(
        job_id: Annotated[str, Path(pattern=JobIDRegex)],
        start: Annotated[int, Query(ge=0)]=0,
        limit: Annotated[int, Query(ge=0, le=50)]=20):
        result = await db.get_job_log(job_id, start, limit)
        return result

    @router.post('/{job_id}/abort')
    async def abort_job_api(
        job_id: Annotated[str, Path(pattern=JobIDRegex)]
    ):
        host_to_notify = await db.abort_job(job_id)
        if isinstance(host_to_notify, str):
            if host_to_notify != '':
                await mq.abort_job(host_to_notify, job_id)
        else:
            raise HTTPException(500)

    @router.post('/{job_id}/restart')
    async def restart_job_api(
        job_id: Annotated[str, Path(pattern=JobIDRegex)],
        # allows implicit specification of restart_from, keep the current-worker as it is;
        restart_from: Annotated[int, Query(ge=-1)]=-1):
        is_sucess = await restart_job(job_id, restart_from)
        if not is_sucess:
            raise HTTPException(500)

    @router.post('/{job_id}/reset')
    async def reset_job_api(
        job_id: Annotated[str, Path(pattern=JobIDRegex)],
        arg: RawJobArgument,
        # requires explicit specification of restart_from;
        restart_from: Annotated[int, Query(ge=0)]=0):
        is_sucess = await reset_job(
            job_id, arg.job_workers, arg.worker_arguments, arg.kv, restart_from)
        if not is_sucess:
            raise HTTPException(500)

    @router.post('/new_raw_job')
    async def create_raw_job(arg: RawJobArgument):
        return await create_job(arg.job_workers, arg.worker_arguments, arg.kv)

    @router.get('/{job_id}/keys')
    async def get_job_kv_keys(
        job_id: Annotated[str, Path(pattern=JobIDRegex)],
        with_values: Annotated[bool, Query()]=False):
        if with_values:
            return await db.get_job_kv_entries(job_id)
        else:
            return await db.get_job_kv_keys(job_id)

    @router.get('/{job_id}/keys/{key}')
    async def get_job_kv_value(
        job_id: Annotated[str, Path(pattern=JobIDRegex)],
        key: Annotated[str, Path()]):
        return await db.get_job_kv_value(job_id, key)

    @router.post('/{job_id}/keys')
    async def update_job_kv_value(
        job_id: Annotated[str, Path(pattern=JobIDRegex)],
        kv: dict[str, str]):
        await db.update_job_kv_value(job_id, kv)

    @router.get('/kv/{key}')
    async def get_key_entries(key: str):
        return await db.get_key_entries(key)

    return router

# worker_field: 4_kbuilder
async def clean_job_bucket(job_id: str, worker_field: str=""):
    gcs = Client()
    bucket = gcs.bucket(os.environ['GCS_BUCKET_NAME'])
    blobs = list(await run_async(bucket.list_blobs, prefix=f'jobs/{job_id}/{worker_field}/'))
    await run_async(bucket.delete_blobs, blobs=blobs)

async def create_job(job_workers: list[str], worker_arguments: list[dict], kv: dict[str, str]):
    if len(job_workers) != len(worker_arguments) or len(job_workers) == 0:
        raise ValueError('Invalid length of workers or arguments')
    job_ctx = {
        'created-time': datetime.utcnow().isoformat(),
        'job-workers': job_workers,
        'current-worker': 0,
        'status': 'pending',
        'worker-results': [],
        'worker-arguments': worker_arguments,
        'modified-time': datetime.utcnow().isoformat(),
        'kv': kv
    }
    job_ctx['job-id'] = await db.insert_job(job_ctx)
    # insert it into the queue;
    await mq.publish_job_id(job_ctx['job-id'], job_workers[0])
    return job_ctx['job-id']

async def reset_job(job_id: str, job_workers: list[str], worker_arguments: list[dict], kv: dict[str, str], restart_from: int=0):
    job_ctx = await db.get_job(job_id)
    if (job_ctx['status'] not in ('aborted', 'finished')) or (restart_from not in range(len(job_workers))):
        raise ValueError(job_ctx['status'], restart_from, len(job_workers))
    if len(job_workers) != len(worker_arguments) or len(job_workers) == 0:
        raise ValueError('Invalid length for arguments or workers')
    for i in range(restart_from, len(job_ctx['job-workers'])):
        await clean_job_bucket(job_id, f"{i}_{job_ctx['job-workers'][i]}")
    job_ctx['status'] = 'pending'
    job_ctx['current-worker'] = restart_from
    job_ctx['job-workers'] = job_workers
    job_ctx['worker-results'] = job_ctx['worker-results'][:min(len(job_ctx['worker-results']), restart_from)]
    job_ctx['worker-arguments'] = worker_arguments
    job_ctx['modified-time'] = datetime.utcnow().isoformat()
    job_ctx['kv'].update(kv)
    if await db.reset_job(job_ctx):
        await mq.publish_job_id(job_id, job_ctx['job-workers'][restart_from])
        return True
    else:
        return False

async def restart_job(job_id: str, restart_from: int=-1):
    job_ctx = await db.get_job(job_id)
    if restart_from == -1:
        restart_from = job_ctx['current-worker']
    if (job_ctx['status'] not in ('aborted', 'finished')) or (restart_from not in range(len(job_ctx['job-workers']))):
        raise ValueError(job_ctx['status'], restart_from, len(job_ctx['job-workers']))
    for i in range(restart_from, len(job_ctx['job-workers'])):
        await clean_job_bucket(job_id, f"{i}_{job_ctx['job-workers'][i]}")
    job_ctx['status'] = 'pending'
    job_ctx['current-worker'] = restart_from
    job_ctx['worker-results'] = job_ctx['worker-results'][:min(len(job_ctx['worker-results']), restart_from)]
    job_ctx['modified-time'] = datetime.utcnow().isoformat()
    if await db.reset_job(job_ctx):
        await mq.publish_job_id(job_id, job_ctx['job-workers'][restart_from])
        return True
    else:
        return False
