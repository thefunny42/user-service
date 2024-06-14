from typing import Annotated

import motor.motor_asyncio
import pydantic
import pymongo.errors
from fastapi import Depends

from .models import User
from .settings import Settings, get_settings

COLLECTIONS: dict[str, motor.motor_asyncio.AsyncIOMotorCollection] = {}
CLIENTS: dict[str, motor.motor_asyncio.AsyncIOMotorClient] = {}


def _prepare_schema(schema):
    "Prepare a jsonSchema for MongoDB validation out of pydantic."
    # https://www.mongodb.com/docs/manual/reference/operator/query/jsonSchema/
    if schema["type"] == "object":
        updated = schema.copy()
        updated["properties"] = {
            name: _prepare_schema(properties)
            for name, properties in schema["properties"].items()
        }
        return updated
    if "format" in schema:
        # MongoDB does not support format.
        updated = schema.copy()
        updated.pop("format")
        return updated
    return schema


class UnavailableError(ValueError):
    pass


class Database[T: type[pydantic.BaseModel]]:

    def __init__(self, settings: Settings, model: T):
        self.settings = settings
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            self.settings.user_service_database,
        )
        self.database = self.client.get_default_database()
        self.collection = None
        self.model = model

    @property
    def name(self):
        return self.model.__name__

    async def get(self):
        if self.collection is None:
            self.collection = await self.ready()
        return self.collection

    async def create(self):
        return await self.database.create_collection(
            name=self.name,
            capped=True,
            size=self.settings.user_service_size,
            writeConcern={"w": 1, "j": True, "wtimeout": 10},
            validator={
                "$jsonSchema": _prepare_schema(self.model.model_json_schema())
            },
        )

    async def ready(self):
        try:
            if self.name in await self.database.list_collection_names():
                return self.database.get_collection(self.name)
            return await self.create()
        except pymongo.errors.PyMongoError:
            raise UnavailableError()

    def close(self):
        self.client.close()


class Connector[T: type[pydantic.BaseModel]]:
    database: Database[T] | None = None
    model: T

    def __init__(self, settings: Annotated[Settings, Depends(get_settings)]):
        self.settings = settings

    def connect(self):
        if self.database is None:
            self.database = Database[T](self.settings, self.model)
        return self.database

    def close(self):
        if self.database is not None:
            self.database.close()
        self.database = None


class UserConnector(Connector):
    model = User


connector = UserConnector(get_settings())


async def get_collection():
    return await connector.connect().get()


class UserRepository:

    def __init__(
        self,
        collection: Annotated[
            motor.motor_asyncio.AsyncIOMotorCollection, Depends(get_collection)
        ],
    ):
        self.collection = collection

    async def list(self):
        return [
            {"name": user["name"], "email": user["email"]}
            async for user in self.collection.find()
        ]

    async def add(self, user: User):
        result = await self.collection.insert_one(user.model_dump())
        return result.acknowledged
