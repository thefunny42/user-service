import secrets

import fastapi.testclient
import httpx
import pytest
import respx

from user_service import database, main, models, security

settings = security.Settings(
    user_service_key=secrets.token_hex(16),
    user_service_issuer="test",
    authorization_endpoint="http://localhost:8181",
)


class UserRepository(models.Users):

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


def get_test_settings():
    return settings


@pytest.fixture(scope="module")
def invalid_token():
    return BearerAuth(secrets.token_urlsafe(16))


@pytest.fixture(scope="module")
def token():
    return BearerAuth(security.Auth(settings).generate_token())


@pytest.fixture(scope="module")
def admin_token():
    return BearerAuth(security.Auth(settings).generate_token("admin"))


@pytest.fixture
def users():
    yield UserRepository(users=[])


@pytest.fixture()
def client(users):
    main.app.dependency_overrides[security.get_settings] = get_test_settings
    main.app.dependency_overrides[database.UserRepository] = lambda: users
    yield fastapi.testclient.TestClient(main.app)


@pytest.fixture
def mocked_opa():
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
