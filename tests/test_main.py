from pymongo.errors import PyMongoError


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.content == b"{}"


def test_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.text.splitlines()
    assert "# TYPE added_users_created gauge" in metrics
    assert "# TYPE added_users_failures_created gauge" in metrics
    assert "# TYPE list_users_created gauge" in metrics


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
