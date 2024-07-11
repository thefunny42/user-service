import json

import pytest

from user_service import models


@pytest.mark.asyncio
async def test_get_users(mocked_client, mocked_users, mocked_opa_allow, token):
    await mocked_users.add(
        models.User(name="Arthur Accroc", email="arthur@example.com")
    )

    response = mocked_client.get("/api/users", auth=token)
    assert response.status_code == 200
    assert response.json() == {
        "users": [{"name": "Arthur Accroc", "email": "arthur@example.com"}]
    }
    assert mocked_opa_allow.called
    assert len(mocked_opa_allow.calls) == 1
    assert json.loads(mocked_opa_allow.calls[0].request.content) == {
        "input": {
            "method": "GET",
            "path": ["api", "users"],
            "roles": [],
        }
    }


@pytest.mark.asyncio
async def test_get_users_jwks(
    jwks_mocked_client, mocked_users, mocked_opa_allow, mocked_jwks, jwks_token
):
    await mocked_users.add(
        models.User(name="Arthur Accroc", email="arthur@example.com")
    )

    response = jwks_mocked_client.get("/api/users", auth=jwks_token)
    assert response.status_code == 200
    assert response.json() == {
        "users": [{"name": "Arthur Accroc", "email": "arthur@example.com"}]
    }
    assert mocked_opa_allow.called
    assert len(mocked_opa_allow.calls) == 1
    assert json.loads(mocked_opa_allow.calls[0].request.content) == {
        "input": {
            "method": "GET",
            "path": ["api", "users"],
            "roles": [],
        }
    }


def test_get_users_empty(mocked_client, mocked_users, mocked_opa_allow, token):
    assert mocked_users.users == []

    response = mocked_client.get("/api/users", auth=token)
    assert response.status_code == 200
    assert response.json() == {"users": []}
    assert mocked_opa_allow.called


@pytest.mark.asyncio
async def test_get_users_admin(
    mocked_client, mocked_users, mocked_opa_allow, admin_token
):
    await mocked_users.add(
        models.User(name="Arthur Accroc", email="arthur@example.com")
    )

    response = mocked_client.get("/api/users", auth=admin_token)
    assert response.status_code == 200
    assert response.json() == {
        "users": [{"name": "Arthur Accroc", "email": "arthur@example.com"}]
    }
    assert mocked_opa_allow.called


@pytest.mark.asyncio
async def test_get_users_jwks_admin(
    jwks_mocked_client,
    mocked_users,
    mocked_opa_allow,
    mocked_jwks,
    jwks_admin_token,
):
    await mocked_users.add(
        models.User(name="Arthur Accroc", email="arthur@example.com")
    )

    response = jwks_mocked_client.get("/api/users", auth=jwks_admin_token)
    assert response.status_code == 200
    assert response.json() == {
        "users": [{"name": "Arthur Accroc", "email": "arthur@example.com"}]
    }
    assert mocked_opa_allow.called


def test_get_users_no_token(mocked_client):
    response = mocked_client.get("/api/users")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}


def test_get_users_invalid_token(mocked_client, invalid_token):
    response = mocked_client.get("/api/users", auth=invalid_token)
    assert response.status_code == 401
    assert response.json() == {"detail": "Insufficient credentials"}


def test_get_users_unauthorized_token(
    mocked_client, mocked_opa_disallow, token
):
    response = mocked_client.get("/api/users", auth=token)
    assert response.status_code == 401
    assert response.json() == {"detail": "Insufficient credentials"}
    assert mocked_opa_disallow.called


def test_get_users_failed_token(mocked_client, mocked_opa_fail, token):
    response = mocked_client.get("/api/users", auth=token)
    assert response.status_code == 401
    assert response.json() == {"detail": "Insufficient credentials"}
    assert mocked_opa_fail.called


def test_add_users(mocked_client, mocked_opa_allow, mocked_users, admin_token):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": "Ford Perfect", "email": "ford@example.com"},
        auth=admin_token,
    )
    assert response.status_code == 201
    assert mocked_users.users == [
        models.User(name="Ford Perfect", email="ford@example.com")
    ]
    assert mocked_opa_allow.called
    assert len(mocked_opa_allow.calls) == 1
    assert json.loads(mocked_opa_allow.calls[0].request.content) == {
        "input": {
            "method": "POST",
            "path": ["api", "users"],
            "roles": ["admin"],
        }
    }


def test_add_users_but_not_tonio(
    mocked_client, mocked_opa_allow, mocked_users, admin_token
):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": "Tonio", "email": "tonio@example.com"},
        auth=admin_token,
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Could not add user."}
    assert mocked_users.users == []
    assert mocked_opa_allow.called


def test_add_users_invalid_token(mocked_client, mocked_users, invalid_token):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": "Ford Perfect", "email": "ford@example.com"},
        auth=invalid_token,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Insufficient credentials"}
    assert mocked_users.users == []


def test_add_users_no_token(mocked_client, mocked_users):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": "Ford Perfect", "email": "ford@example.com"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}
    assert mocked_users.users == []


def test_add_users_unauthorized_token(
    mocked_client, mocked_opa_disallow, mocked_users, token
):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": "Ford Perfect", "email": "ford@example.com"},
        auth=token,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Insufficient credentials"}
    assert mocked_users.users == []
    assert mocked_opa_disallow.called


def test_add_users_failed_token(
    mocked_client, mocked_opa_fail, mocked_users, admin_token
):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": "Ford Perfect", "email": "ford@example.com"},
        auth=admin_token,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Insufficient credentials"}
    assert mocked_users.users == []
    assert mocked_opa_fail.called


def test_add_users_no_name(
    mocked_client, mocked_opa_allow, mocked_users, admin_token
):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users", json={"email": "ford@example.com"}, auth=admin_token
    )
    assert response.status_code == 422
    assert mocked_users.users == []
    assert mocked_opa_allow.called


def test_add_users_no_email(
    mocked_client, mocked_opa_allow, mocked_users, admin_token
):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users", json={"name": "Ford Perfect"}, auth=admin_token
    )
    assert response.status_code == 422
    assert mocked_users.users == []
    assert mocked_opa_allow.called


def test_add_users_invalid_name(
    mocked_client, mocked_opa_allow, mocked_users, admin_token
):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": 42, "email": "ford@example.com"},
        auth=admin_token,
    )
    assert response.status_code == 422
    assert mocked_users.users == []
    assert mocked_opa_allow.called


def test_add_users_long_name(
    mocked_client, mocked_opa_allow, mocked_users, admin_token
):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": "Hello!" * 1024, "email": "ford@example.com"},
        auth=admin_token,
    )
    assert response.status_code == 422
    assert mocked_users.users == []
    assert mocked_opa_allow.called


def test_add_users_invalid_email(
    mocked_client, mocked_opa_allow, mocked_users, admin_token
):
    assert mocked_users.users == []

    response = mocked_client.post(
        "/api/users",
        json={"name": "Ford Perfect", "email": "ford@example.com" * 1024},
        auth=admin_token,
    )
    assert response.status_code == 422
    assert mocked_users.users == []
    assert mocked_opa_allow.called
