import pytest
from pymongo.errors import PyMongoError

from user_service import security


@pytest.mark.asyncio
async def test_print_generated_token(capsys, settings):
    await security.print_generated_token("admin")
    capured = capsys.readouterr()

    auth = security.Auth(settings)
    roles = await auth.authenticate(capured.out.strip())
    assert roles == ["admin"]


def test_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.text.splitlines()
    assert "# TYPE userservice_added_users_created gauge" in metrics
    assert "# TYPE userservice_added_users_failures_created gauge" in metrics
    assert "# TYPE userservice_list_users_created gauge" in metrics


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.content == b"{}"


def test_health_ready(client):
    response = client.get("/health?ready=true")
    assert response.status_code == 200
    assert response.json() == {}


def test_health_not_ready(client, mocker):
    mocker.patch(
        "motor.motor_asyncio.AsyncIOMotorDatabase.list_collection_names",
        side_effect=PyMongoError,
    )
    response = client.get("/health?ready=true")
    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
