import secrets

import fastapi.testclient
import httpx
import pydantic_core
import pytest
import pytest_asyncio
import respx
import whtft.security

from user_service import api, database, main, models
from user_service.settings import Settings

# This contains the private key so we can generate tokens.
TEST_JWKS_URL = "http://somewhere/.well-known/jwks.json"
TEST_JWKS_KEYS = {
    "keys": [
        {
            "kty": "EC",
            "use": "sig",
            "kid": "d3171680f32140de8edd65c149fc7d61",
            "crv": "P-256",
            "x": "cFA_15qaK0MB3o1DcTHqlkYMcfP1jUB1qusS5jxbyEE",
            "y": "7FpW69s-Zg9Yz3jalWfw5iGVfDYG5FAU2TtismVLucU",
            "d": "IDQe5LK0uQebPEU5zGWwL4x0z5P7tJjRAsFcEQcMeSM",
        }
    ]
}


class MockUserRepository(models.Users):

    async def add(self, user: models.User):
        if user.name == "Tonio":
            return None
        added_user = models.IdentifiedUser(
            id=str(len(self.users)), **user.model_dump()
        )
        self.users.append(added_user)
        return added_user.model_dump()

    async def get(self, id: str):
        for user in self.users:
            if user.id == id:
                return user.model_dump()

    async def delete(self, id: str):
        for user in self.users:
            if user.id == id:
                self.users.remove(user)
                return True
        return False

    async def list(self):
        return [user.model_dump() for user in self.users]


@pytest.fixture(scope="module")
def checker():
    return whtft.security.Checker(Settings())


@pytest.fixture(scope="module")
def jwks_checker():
    return whtft.security.Checker(
        Settings(
            authentication_key=None,
            authentication_jwks_url=pydantic_core.Url(TEST_JWKS_URL),
        )
    )


@pytest.fixture(scope="module")
def invalid_token():
    return whtft.security.BearerAuth(secrets.token_urlsafe(16))


@pytest_asyncio.fixture()
async def token(checker):
    return await checker.generate_token()


@pytest_asyncio.fixture()
async def jwks_token(mocked_jwks, jwks_checker):
    return await jwks_checker.generate_token()


@pytest_asyncio.fixture()
async def admin_token(checker):
    return await checker.generate_token("admin")


@pytest_asyncio.fixture()
async def jwks_admin_token(mocked_jwks, jwks_checker):
    return await jwks_checker.generate_token("admin")


@pytest.fixture()
def mocked_users():
    yield MockUserRepository(users=[])


@pytest_asyncio.fixture
async def connection():
    yield database.connector.connect()
    database.connector.close()


@pytest_asyncio.fixture
async def users():
    collection = await database.get_collection()
    yield database.UserRepository(collection)
    await collection.drop()
    database.connector.close()


@pytest_asyncio.fixture
async def client():
    main.app.dependency_overrides.clear()
    with fastapi.testclient.TestClient(main.app) as client:
        yield client


@pytest_asyncio.fixture
async def mocked_client(mocked_users, checker):
    "This client will use a mocked user source and not mongoDB"
    main.app.dependency_overrides[api.security] = checker
    main.app.dependency_overrides[database.UserRepository] = (
        lambda: mocked_users
    )
    with fastapi.testclient.TestClient(main.app) as client:
        yield client


@pytest_asyncio.fixture
async def jwks_mocked_client(mocked_users, jwks_checker):
    """This client will use a mocked user source and not mongoDB and use jwks
    keys"""
    main.app.dependency_overrides[api.security] = jwks_checker
    main.app.dependency_overrides[database.UserRepository] = (
        lambda: mocked_users
    )
    with fastapi.testclient.TestClient(main.app) as client:
        yield client


@pytest.fixture
def mocked_jwks():
    with respx.mock(base_url=TEST_JWKS_URL, assert_all_called=False) as mock:
        mocked_jwks = mock.get(name="jwks")
        mocked_jwks.return_value = httpx.Response(200, json=TEST_JWKS_KEYS)
        yield mocked_jwks


@pytest.fixture
def mocked_opa(checker):
    with respx.mock(base_url=checker.settings.authorization_url) as mock:
        yield mock.post(name="opa")


@pytest.fixture
def mocked_opa_allow(mocked_opa):
    mocked_opa.return_value = httpx.Response(
        200, json={"result": {"allow": True}}
    )
    yield mocked_opa


@pytest.fixture
def mocked_opa_disallow(mocked_opa):
    mocked_opa.return_value = httpx.Response(
        200, json={"result": {"allow": False}}
    )
    yield mocked_opa


@pytest.fixture
def mocked_opa_fail(mocked_opa):
    mocked_opa.return_value = httpx.Response(500)
    yield mocked_opa
