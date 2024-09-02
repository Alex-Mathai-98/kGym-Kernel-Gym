# main.py
import uvicorn
from contextlib import asynccontextmanager
from .utils import ISOTimeRegex, ISOTimeDefaultStart, ISOTimeDefaultEnd
from typing import Annotated
from fastapi import FastAPI, APIRouter, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from .jobs import create_job_api_router
from . import db, mq

def create_system_api_router() -> APIRouter:
    router = APIRouter(prefix='/system')

    @router.get('/workers/types/{worker_name}/log')
    async def get_sys_log_by_worker(
        worker_name: Annotated[str, Path()],
        start_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultStart,
        end_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultEnd,
        start: Annotated[int, Query(ge=0)]=0,
        limit: Annotated[int, Query(ge=0, le=50)]=20):
        result = await db.get_sys_log_by_worker(worker_name, start_time, end_time, start, limit)
        return result

    @router.get('/workers/instances/{worker_hostname}/log')
    async def get_sys_log_by_worker_hostname(
        worker_hostname: Annotated[str, Path()],
        start_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultStart,
        end_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultEnd,
        start: Annotated[int, Query(ge=0)]=0,
        limit: Annotated[int, Query(ge=0, le=50)]=20):
        result = await db.get_sys_log_by_worker_hostname(worker_hostname, start_time, end_time, start, limit)
        return result

    @router.get('/displays/workers/log')
    async def display_workers_log(
        start_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultStart,
        end_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultEnd,
        start: Annotated[int, Query(ge=0)]=0,
        limit: Annotated[int, Query(ge=0, le=50)]=20):
        result = await db.get_sys_log_display(start_time, end_time, start, limit)
        return result

    @router.get('/displays/jobs/log')
    async def display_jobs_log(
        start_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultStart,
        end_time: Annotated[str, Query(pattern=ISOTimeRegex)]=ISOTimeDefaultEnd,
        start: Annotated[int, Query(ge=0)]=0,
        limit: Annotated[int, Query(ge=0, le=50)]=20):
        result = await db.get_job_log_display(start_time, end_time, start, limit)
        return result

    return router

def create_scheduler_app() -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await db.connect_db()
        await mq.init_mq()
        yield
        await mq.close_mq()
        await db.close_db()

    app = FastAPI(lifespan=lifespan)

    app.include_router(create_job_api_router())
    app.include_router(create_system_api_router())

    origins = [
        "http://localhost:3000"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

def scheduler_entrypoint():
    uvicorn.run(create_scheduler_app(), host="0.0.0.0", port=8000)
