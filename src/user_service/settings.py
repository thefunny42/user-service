import functools
import urllib.parse
from typing import Any

import pydantic
import whtft.app


class Settings(whtft.app.Settings):
    user_service_key: pydantic.SecretStr | None = pydantic.Field(default=None)
    user_service_jwks_url: pydantic.HttpUrl | None = pydantic.Field(
        default=None
    )
    user_service_issuer: str = pydantic.Field(default="")
    user_service_audience: str = pydantic.Field(default="")
    user_service_database: pydantic.MongoDsn = pydantic.Field(default=...)
    user_service_size: pydantic.PositiveInt = pydantic.Field(default=10000)
    authorization_endpoint: pydantic.HttpUrl = pydantic.Field(default=...)
    authorization_policy: str = pydantic.Field(default="userservice")

    @pydantic.computed_field
    @functools.cached_property
    def authorization_url(self) -> str:
        return urllib.parse.urljoin(
            str(self.authorization_endpoint),
            f"/v1/data/{self.authorization_policy}",
        )

    @pydantic.model_validator(mode="before")
    @classmethod
    def check_key_or_jwks_url(cls, data: Any) -> Any:
        if isinstance(data, dict):
            assert data.get("user_service_key") or data.get(
                "user_service_jwks_url"
            ), "Set either user_service_key or user_service_jwks_url"
        return data


settings = Settings()


def get_settings():
    return settings
