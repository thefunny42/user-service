import uvicorn
from fastapi import FastAPI

from . import api, security

__version__ = "0.1.0"

app = FastAPI()


@app.get("/health")
def get_health():
    return {}


app.include_router(api.router)


def main():  # pragma: no cover
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        server_header=False,
        log_config=security.get_settings().user_service_log,
    )
