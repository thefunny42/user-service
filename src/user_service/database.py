from typing import Annotated

import bson
import motor.motor_asyncio
import pydantic
import pymongo.errors
from fastapi import Depends

from . import models
from .settings import Settings, settings

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
            if not (name == "id" and properties.get("type") == "string")
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
            str(self.settings.default_database_url),
        )
        self.database = self.client.get_default_database()
        self.collection = None
        self.model = model

    @property
    def name(self):
        return self.model.__name__

    async def get(self):
        if self.collection is None:
            self.collection = await self.ready(autocreate=True)
        return self.collection

    async def create(self):
        return await self.database.create_collection(
            name=self.name,
            capped=True,
            size=self.settings.default_database_size,
            writeConcern={"w": 1, "j": True, "wtimeout": 10},
            validator={
                "$jsonSchema": _prepare_schema(self.model.model_json_schema())
            },
        )

    async def ready(self, autocreate=False):
        try:
            if self.name in await self.database.list_collection_names():
                return self.database.get_collection(self.name)
            if autocreate:
                return await self.create()
        except pymongo.errors.PyMongoError:
            raise UnavailableError()
        raise UnavailableError()

    def close(self):
        self.client.close()


class Connector[T: type[pydantic.BaseModel]]:
    database: Database[T] | None = None
    model: T

    def __init__(self, settings: Settings):
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
    model = models.User


connector = UserConnector(settings)


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

    @staticmethod
    def _convert(document):
        return {
            "name": document["name"],
            "email": document["email"],
            "id": str(document["_id"]),
        }

    async def list(self):
        return [
            self._convert(document)
            async for document in self.collection.find()
        ]

    async def get(self, id: str | bson.ObjectId):
        document = await self.collection.find_one({"_id": bson.ObjectId(id)})
        if document is None:
            return None
        return self._convert(document)

    async def delete(self, id: str | bson.ObjectId):
        result = await self.collection.delete_one({"_id": bson.ObjectId(id)})
        return result.acknowledged and result.deleted_count == 1

    async def add(self, user: models.User):
        result = await self.collection.insert_one(user.model_dump())
        if result.acknowledged:
            return await self.get(result.inserted_id)
