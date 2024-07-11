import functools
import urllib.parse
from typing import Any

import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        secrets_dir="/app/conf",
    )

    user_service_key: pydantic.SecretStr | None = pydantic.Field(default=None)
    user_service_jwks_url: pydantic.HttpUrl | None = pydantic.Field(
        default=None
    )
    user_service_issuer: str = pydantic.Field(default="")
    user_service_audience: str = pydantic.Field(default="")
    user_service_log_config: pydantic.FilePath | None = pydantic.Field(
        default=None
    )
    user_service_database: pydantic.MongoDsn = pydantic.Field(default=...)
    user_service_size: pydantic.PositiveInt = pydantic.Field(default=10000)
    authorization_endpoint: pydantic.HttpUrl = pydantic.Field(default=...)
    authorization_policy: str = pydantic.Field(default="userservice")

    @pydantic.computed_field
    @functools.cached_property
    def authorization_url(self) -> str:
        return urllib.parse.urljoin(
            str(self.authorization_endpoint),
            "/v1/data/{self.authorization_policy}",
        )

    @pydantic.model_validator(mode="before")
    @classmethod
    def check_key_or_jwks_url(cls, data: Any) -> Any:
        if isinstance(data, dict):
            assert data.get("user_service_key") or data.get(
                "user_service_jwks_url"
            ), "Set either user_service_key or user_service_jwks_url"
        return data

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[pydantic_settings.BaseSettings],
        init_settings: pydantic_settings.PydanticBaseSettingsSource,
        env_settings: pydantic_settings.PydanticBaseSettingsSource,
        dotenv_settings: pydantic_settings.PydanticBaseSettingsSource,
        file_secret_settings: pydantic_settings.PydanticBaseSettingsSource,
    ) -> tuple[pydantic_settings.PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            file_secret_settings,
            env_settings,
            dotenv_settings,
        )


settings = Settings()


def get_settings():
    return settings
