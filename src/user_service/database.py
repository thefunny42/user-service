from typing import Annotated, Type

import motor.motor_asyncio
import pydantic
from fastapi import Depends

from .models import User
from .settings import Settings, get_settings

CACHE: dict[str, motor.motor_asyncio.AsyncIOMotorCollection] = {}


def _prepare_property(property):
    # MongoDb does not support format in its schema so we massage the schema.
    if "format" in property:
        updated = property.copy()
        updated.pop("format")
        return updated
    return property


async def _create_collection(
    database: motor.motor_asyncio.AsyncIOMotorDatabase,
    model: Type[pydantic.BaseModel],
):
    """Create a validated collection based on the pydantic model."""
    # Note: We limit the size of the collection since we currently load all
    # items in memory while returning them. If the use-case is refined we can
    # change that behavior, but in that case we should implement batching and
    # modify how the API works to the outside, since working with large JSON
    # objects is not recommanded either.
    name = model.__name__
    if name in await database.list_collection_names():  # pragma: no cover
        return database.get_collection(name)
    schema = model.model_json_schema()
    return await database.create_collection(
        name=name,
        capped=True,
        size=10000,
        writeConcern={"w": 1, "j": True, "wtimeout": 10},
        validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": schema["required"],
                "properties": {
                    name: _prepare_property(properties)
                    for name, properties in schema["properties"].items()
                },
            }
        },
    )


async def get_collection(settings: Annotated[Settings, Depends(get_settings)]):
    collection = CACHE.get(settings.user_service_database)
    if collection is None:
        database = motor.motor_asyncio.AsyncIOMotorClient(
            settings.user_service_database
        ).get_default_database()
        collection = await _create_collection(database, User)
        CACHE[settings.user_service_database] = collection
    return collection


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
