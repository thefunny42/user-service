import secrets

import fastapi.testclient
import httpx
import pydantic_core
import pytest
import pytest_asyncio
import respx

from user_service import main, models, security
from user_service.database import UserRepository, connector, get_collection
from user_service.settings import Settings, get_settings

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
            return False
        self.users.append(user)
        return True

    async def list(self):
        return [user.model_dump() for user in self.users]


class BearerAuth(httpx.Auth):

    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


@pytest.fixture(scope="module")
def settings():
    return Settings()


@pytest.fixture(scope="module")
def jwks_settings():
    return Settings(
        user_service_key=None,
        user_service_jwks_url=pydantic_core.Url(TEST_JWKS_URL),
    )


@pytest.fixture(scope="module")
def invalid_token():
    return BearerAuth(secrets.token_urlsafe(16))


@pytest_asyncio.fixture()
async def token(settings):
    return BearerAuth(await security.Auth(settings).generate_token())


@pytest_asyncio.fixture()
async def jwks_token(mocked_jwks, jwks_settings):
    return BearerAuth(await security.Auth(jwks_settings).generate_token())


@pytest_asyncio.fixture()
async def admin_token(settings):
    return BearerAuth(await security.Auth(settings).generate_token("admin"))


@pytest_asyncio.fixture()
async def jwks_admin_token(mocked_jwks, jwks_settings):
    return BearerAuth(
        await security.Auth(jwks_settings).generate_token("admin")
    )


@pytest.fixture()
def mocked_users():
    yield MockUserRepository(users=[])


@pytest_asyncio.fixture
async def database():
    yield connector.connect()
    connector.close()


@pytest_asyncio.fixture
async def users():
    collection = await get_collection()
    yield UserRepository(collection)
    await collection.drop()
    connector.close()


@pytest_asyncio.fixture
async def client():
    main.app.dependency_overrides.clear()
    with fastapi.testclient.TestClient(main.app) as client:
        yield client


@pytest_asyncio.fixture
async def mocked_client(mocked_users, settings):
    "This client will use a mocked user source and not mongoDB"
    main.app.dependency_overrides[get_settings] = lambda: settings
    main.app.dependency_overrides[UserRepository] = lambda: mocked_users
    with fastapi.testclient.TestClient(main.app) as client:
        yield client


@pytest_asyncio.fixture
async def jwks_mocked_client(mocked_users, jwks_settings):
    """This client will use a mocked user source and not mongoDB and use jwks
    keys"""
    main.app.dependency_overrides[get_settings] = lambda: jwks_settings
    main.app.dependency_overrides[UserRepository] = lambda: mocked_users
    with fastapi.testclient.TestClient(main.app) as client:
        yield client


@pytest.fixture
def mocked_jwks():
    with respx.mock(base_url=TEST_JWKS_URL, assert_all_called=False) as mock:
        mocked_jwks = mock.get(name="jwks")
        mocked_jwks.return_value = httpx.Response(200, json=TEST_JWKS_KEYS)
        yield mocked_jwks


@pytest.fixture
def mocked_jwks_failed(mocked_jwks):
    mocked_jwks.return_value = httpx.Response(500)
    security.get_keys.cache_clear()
    yield mocked_jwks
    security.get_keys.cache_clear()


@pytest.fixture
def mocked_opa(settings):
    with respx.mock(base_url=settings.authorization_url) as mock:
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
