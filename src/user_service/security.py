import datetime
from typing import Annotated

import argparse
import logging

import httpx
import jwt
import jwt.exceptions
import pydantic
from fastapi import Depends, HTTPException, Request, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from . import utils

logger = logging.getLogger("user_service.security")
client = httpx.AsyncClient()

ALGORITHM = "HS256"


class Settings(utils.Settings):
    user_service_key: str = pydantic.Field(default=...)
    user_service_issuer: str | None = pydantic.Field(default=None)
    user_service_log: str | None = pydantic.Field(default=None)
    authorization_endpoint: str = pydantic.Field(default=...)
    authorization_policy: str = pydantic.Field(default="userservice")

    def generate_token(self, *roles: str):
        return jwt.encode(
            {
                "roles": list(roles),
                "iss": self.user_service_issuer,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                + datetime.timedelta(seconds=180),
            },
            self.user_service_key,
            algorithm=ALGORITHM,
        )

    def authenticate(self, token: str) -> list[str] | None:
        try:
            payload = jwt.decode(
                token,
                self.user_service_key,
                algorithms=[ALGORITHM],
                issuer=self.user_service_issuer,
                options={"requires": ["exp", "iss", "roles"]},
            )
        except jwt.exceptions.InvalidTokenError:
            return None
        return payload.get("roles", [])

    async def authorize(
        self, method: str, path: list[str], roles: list[str]
    ) -> bool:
        response = await client.post(
            f"{self.authorization_endpoint}/v1/data/{self.authorization_policy}",
            json={
                "input": {
                    "method": method,
                    "path": path,
                    "roles": roles,
                },
            },
        )
        if response.status_code != 200:
            logger.error("Invalid response from authorization endpoint.")
            return False
        result = response.json().get("result", {})
        return (
            result.get("allow", False) if isinstance(result, dict) else False
        )


settings = Settings()


def get_settings():  # pragma: no cover
    return settings


async def validate_token(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(HTTPBearer())
    ],
):
    roles = settings.authenticate(credentials.credentials)
    if roles is None:
        logger.info("Could not authenticate request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = {
        "roles": roles,
        "method": request.method,
        "path": request.url.path.strip("/").split("/"),
    }
    if not await settings.authorize(**query):
        logger.info(f"Could not authorize request with: {query} ")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Authorized request with: {query} ")


def main():  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="new-user-service-token",
        description="Generate token for testing purpose",
    )
    parser.add_argument("role", nargs="*")
    args = parser.parse_args()
    print(settings.generate_token(*args.role))
