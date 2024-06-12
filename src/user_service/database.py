from typing import Annotated, Type

import motor.motor_asyncio
import pydantic
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


async def _create_collection(
    database: motor.motor_asyncio.AsyncIOMotorDatabase,
    model: Type[pydantic.BaseModel],
    size=10000,
):
    "Create a validated collection based on the pydantic model."
    # Note: We limit the size of the collection since we currently load all
    # items in memory while returning them. If the use-case is refined we can
    # change that behavior, but in that case we should implement batching and
    # modify how the API works to the outside, since working with large JSON
    # objects is not recommanded either.
    name = model.__name__
    if name in await database.list_collection_names():  # pragma: no cover
        return database.get_collection(name)
    return await database.create_collection(
        name=name,
        capped=True,
        size=size,
        writeConcern={"w": 1, "j": True, "wtimeout": 10},
        validator={"$jsonSchema": _prepare_schema(model.model_json_schema())},
    )


async def get_collection(settings: Annotated[Settings, Depends(get_settings)]):
    key = settings.user_service_database
    collection = COLLECTIONS.get(key)
    if collection is None:
        client = CLIENTS.get(key)
        if client is None:
            client = motor.motor_asyncio.AsyncIOMotorClient(key)
            CLIENTS[key] = client
        database = client.get_default_database()
        collection = await _create_collection(
            database, User, size=settings.user_service_size
        )
        COLLECTIONS[key] = collection
    return collection


def close():
    "Terminate all clients"
    COLLECTIONS.clear()
    for client in CLIENTS.values():
        client.close()
    CLIENTS.clear()


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
