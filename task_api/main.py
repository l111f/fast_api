from contextlib import asynccontextmanager
from fastapi import FastAPI
from task_api.database import init_db
from task_api.routers import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.include_router(tasks.router)
