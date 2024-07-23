import pydantic
import whtft.security


class Settings(whtft.security.Settings):
    default_database_url: pydantic.MongoDsn = pydantic.Field(default=...)
    default_database_size: pydantic.PositiveInt = pydantic.Field(default=10000)


settings = Settings()
