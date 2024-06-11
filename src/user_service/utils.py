import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", secrets_dir="/var/run"
    )

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
