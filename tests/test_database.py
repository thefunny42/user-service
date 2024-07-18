import pytest

from user_service import models
from user_service.database import UnavailableError


@pytest.mark.asyncio
async def test_user_repository(users, mocker):
    assert await users.list() == []

    added = await users.add(
        models.User(name="Arthur Accroc", email="arthur@example.com")
    )
    assert added == {
        "name": "Arthur Accroc",
        "email": "arthur@example.com",
        "id": mocker.ANY,
    }
    assert await users.list() == [
        {
            "name": "Arthur Accroc",
            "email": "arthur@example.com",
            "id": added["id"],
        }
    ]
    assert await users.get(added["id"]) == added
    assert await users.delete(added["id"]) is True
    assert await users.list() == []
    assert await users.get(added["id"]) is None
    assert await users.delete(added["id"]) is False


@pytest.mark.asyncio
async def test_database_ready(connection):
    collection = await connection.ready(autocreate=True)
    assert collection.name == "User"

    collection = await connection.ready()
    assert collection.name == "User"

    collection.drop()
    with pytest.raises(UnavailableError):
        await connection.ready(autocreate=False)


@pytest.mark.asyncio
async def test_mocked_user_repository(mocked_users):
    assert await mocked_users.list() == []

    added = await mocked_users.add(
        models.User(name="Arthur Accroc", email="arthur@example.com")
    )
    assert added == {
        "name": "Arthur Accroc",
        "email": "arthur@example.com",
        "id": "0",
    }
    assert await mocked_users.list() == [
        {"name": "Arthur Accroc", "email": "arthur@example.com", "id": "0"}
    ]

    assert await mocked_users.get(added["id"]) == added
    assert await mocked_users.delete(added["id"]) is True
    assert await mocked_users.list() == []
    assert await mocked_users.get(added["id"]) is None
    assert await mocked_users.delete(added["id"]) is False
