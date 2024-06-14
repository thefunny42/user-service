from pymongo.errors import PyMongoError


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {}


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
