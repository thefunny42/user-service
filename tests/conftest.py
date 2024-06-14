import secrets

import fastapi.testclient
import httpx
import pytest
import pytest_asyncio
import respx

from user_service import main, models, security
from user_service.database import UserRepository, connector, get_collection
from user_service.settings import get_settings


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
    return get_settings()


@pytest.fixture(scope="module")
def invalid_token():
    return BearerAuth(secrets.token_urlsafe(16))


@pytest.fixture(scope="module")
def token(settings):
    return BearerAuth(security.Auth(settings).generate_token())


@pytest.fixture(scope="module")
def admin_token(settings):
    return BearerAuth(security.Auth(settings).generate_token("admin"))


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
async def mocked_client(mocked_users):
    "This client will use a mocked user source and not mongoDB"
    main.app.dependency_overrides[UserRepository] = lambda: mocked_users
    with fastapi.testclient.TestClient(main.app) as client:
        yield client


@pytest.fixture
def mocked_opa(settings):
    with respx.mock(base_url=settings.authorization_endpoint) as mock:
        yield mock.post(
            f"/v1/data/{settings.authorization_policy}", name="opa"
        )


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
