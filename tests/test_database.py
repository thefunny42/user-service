import pytest

from user_service import models
from user_service.database import UnavailableError


@pytest.mark.asyncio
async def test_user_repository(users):
    assert await users.list() == []

    await users.add(
        models.User(name="Arthur Accroc", email="arthur@example.com")
    )
    assert await users.list() == [
        {"name": "Arthur Accroc", "email": "arthur@example.com"}
    ]


@pytest.mark.asyncio
async def test_read(database):
    collection = await database.ready(autocreate=True)
    assert collection.name == "User"

    collection = await database.ready()
    assert collection.name == "User"

    collection.drop()
    with pytest.raises(UnavailableError):
        await database.ready(autocreate=False)


@pytest.mark.asyncio
async def test_mocked_user_repository(mocked_users):
    assert await mocked_users.list() == []

    await mocked_users.add(
        models.User(name="Arthur Accroc", email="arthur@example.com")
    )
    assert await mocked_users.list() == [
        {"name": "Arthur Accroc", "email": "arthur@example.com"}
    ]
