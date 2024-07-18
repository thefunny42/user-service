import pydantic
import whtft.security


class Settings(whtft.security.Settings):
    user_service_database: pydantic.MongoDsn = pydantic.Field(default=...)
    user_service_size: pydantic.PositiveInt = pydantic.Field(default=10000)


settings = Settings()
