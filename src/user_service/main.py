from contextlib import asynccontextmanager

import prometheus_client
import uvicorn
from fastapi import FastAPI, HTTPException, status

from . import api, database, settings

__version__ = "0.2.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connector.connect().ready(autocreate=True)
    yield
    database.connector.close()


app = FastAPI(lifespan=lifespan)

app.mount("/metrics", prometheus_client.make_asgi_app())


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
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        server_header=False,
        log_config=settings.get_settings().user_service_log,
    )
