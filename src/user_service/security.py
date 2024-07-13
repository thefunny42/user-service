import argparse
import asyncio
import datetime
import logging
from typing import Annotated, Any, NamedTuple

import async_lru
import httpx
import jwt
import jwt.exceptions
from fastapi import Depends, HTTPException, Request, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from .settings import Settings, get_settings

logger = logging.getLogger("user_service.security")
client = httpx.AsyncClient()


@async_lru.alru_cache()
async def get_keys(url: str) -> dict[str, jwt.PyJWK]:
    response = await client.get(url=url)
    if response.status_code != 200:
        return {}
    data = response.json()
    key_set = jwt.PyJWKSet.from_dict(data)
    return {
        key.key_id: key
        for key in key_set.keys
        if key.public_key_use in {"sig", None} and key.key_id
    }


class TokenInformation(NamedTuple):
    algorithm: str
    key: str | Any
    headers: dict | None = None


class Auth:

    def __init__(self, settings: Annotated[Settings, Depends(get_settings)]):
        self.settings = settings

    async def __get_information(self, token: str | None = None):
        if self.settings.user_service_jwks_url is None:
            if self.settings.user_service_key is None:  # pragma: no cover
                return None
            key = self.settings.user_service_key.get_secret_value()
            return TokenInformation(key=key, algorithm="HS256")
        url = str(self.settings.user_service_jwks_url)
        keys = await get_keys(url)
        if token:
            header = jwt.get_unverified_header(token)
            if "kid" not in header:  # pragma: no cover
                return None
            if header["kid"] not in keys:
                get_keys.cache_invalidate(url)
                keys = await get_keys(url)
                if header["kid"] not in keys:
                    return None
            return TokenInformation(
                key=keys[header["kid"]].key, algorithm=header["alg"]
            )
        for key in keys.values():
            if key.key_type == "EC":
                # XXX We assume ES256 for the moment.
                return TokenInformation(
                    headers={"kid": key.key_id}, key=key.key, algorithm="ES256"
                )
        return None

    async def generate_token(self, *roles: str):
        information = await self.__get_information()
        if information is None:
            return ""
        return jwt.encode(
            {
                "roles": list(roles),
                "iss": self.settings.user_service_issuer,
                "aud": self.settings.user_service_audience,
                "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                + datetime.timedelta(seconds=180),
            },
            information.key,
            algorithm=information.algorithm,
            headers=information.headers,
        )

    async def authenticate(self, token: str) -> list[str] | None:
        information = await self.__get_information(token)
        if information is None:
            return None
        try:
            payload = jwt.decode(
                token,
                information.key,
                algorithms=[information.algorithm],
                issuer=self.settings.user_service_issuer,
                audience=self.settings.user_service_audience or None,
                options={"requires": ["exp", "iss", "roles"]},
            )
        except jwt.exceptions.InvalidTokenError as error:
            logger.error(f"Error while validating token {error}")
            return None
        return payload.get("roles", [])

    async def authorize(
        self, method: str, path: list[str], roles: list[str]
    ) -> bool:
        response = await client.post(
            self.settings.authorization_url,
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
    roles = await auth.authenticate(credentials.credentials)
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


async def print_generated_token(*roles: str):
    print(await Auth(get_settings()).generate_token(*roles))


def main():  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="new-user-service-token",
        description="Generate token for testing purpose",
    )
    parser.add_argument("role", nargs="*")
    args = parser.parse_args()
    asyncio.run(print_generated_token(*args.role))
