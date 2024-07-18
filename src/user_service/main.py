from contextlib import asynccontextmanager

import whtft.app
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
    whtft.app.main(app, get_settings())
