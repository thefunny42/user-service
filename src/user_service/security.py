import argparse
import datetime
import logging
from typing import Annotated

import httpx
import jwt
import jwt.exceptions
from fastapi import Depends, HTTPException, Request, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from .settings import Settings, get_settings

logger = logging.getLogger("user_service.security")
client = httpx.AsyncClient()

ALGORITHM = "HS256"


class Auth:

    def __init__(self, settings: Annotated[Settings, Depends(get_settings)]):
        self.settings = settings

    def generate_token(self, *roles: str):
        return jwt.encode(
            {
                "roles": list(roles),
                "iss": self.settings.user_service_issuer,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                + datetime.timedelta(seconds=180),
            },
            self.settings.user_service_key,
            algorithm=ALGORITHM,
        )

    def authenticate(self, token: str) -> list[str] | None:
        try:
            payload = jwt.decode(
                token,
                self.settings.user_service_key,
                algorithms=[ALGORITHM],
                issuer=self.settings.user_service_issuer,
                options={"requires": ["exp", "iss", "roles"]},
            )
        except jwt.exceptions.InvalidTokenError:
            return None
        return payload.get("roles", [])

    async def authorize(
        self, method: str, path: list[str], roles: list[str]
    ) -> bool:
        response = await client.post(
            f"{self.settings.authorization_endpoint}"
            f"/v1/data/{self.settings.authorization_policy}",
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


async def validate_token(
    request: Request,
    auth: Annotated[Auth, Depends()],
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(HTTPBearer())
    ],
):
    roles = auth.authenticate(credentials.credentials)
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
    if not await auth.authorize(**query):
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
    print(Auth(get_settings()).generate_token(*args.role))
