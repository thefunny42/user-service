from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, status

from . import api, database
from .settings import get_settings

__version__ = "0.2.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connector.connect().ready(autocreate=True)
    yield
    database.connector.close()


app = FastAPI(lifespan=lifespan)

app.mount("/metrics", api.metrics.app)


@app.get("/health")
async def get_health(ready: bool = False):
    if ready:
        try:
            await database.connector.connect().ready()
        except database.UnavailableError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    return {}


app.include_router(api.router)


def main():  # pragma: no cover
    settings = get_settings()
    log_config = None
    if settings.user_service_log_config is not None:
        log_config = str(settings.user_service_log_config)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        server_header=False,
        log_config=log_config,
    )
