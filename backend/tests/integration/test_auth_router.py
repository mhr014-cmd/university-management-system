"""
Integration tests: POST /auth/login, /auth/refresh, /auth/logout, PUT /auth/password.

Full request -> DB -> response cycle against a disposable test database
(see tests/conftest.py). Requires TEST_DATABASE_URL — skipped otherwise.
"""

from tests.conftest import requires_test_database

pytestmark = requires_test_database


def test_login_success_returns_tokens_and_user(client, make_user):
    make_user("student@example.com", "correct-password", "student")

    response = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == "student@example.com"
    assert body["user"]["role"] == "student"


def test_login_wrong_password_returns_401(client, make_user):
    make_user("student@example.com", "correct-password", "student")

    response = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert "error" in response.json()


def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert response.status_code == 401


def test_login_deactivated_account_returns_403(client, make_user):
    # BR-006: a deactivated account must fail login even with correct credentials.
    make_user("inactive@example.com", "correct-password", "student", is_active=False)

    response = client.post(
        "/api/v1/auth/login", json={"email": "inactive@example.com", "password": "correct-password"}
    )

    assert response.status_code == 403


def test_refresh_success_rotates_tokens(client, make_user):
    make_user("student@example.com", "correct-password", "student")
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
    )
    original_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh_token})

    assert refresh_response.status_code == 200
    assert refresh_response.json()["refresh_token"] != original_refresh_token


def test_refresh_reuse_of_rotated_token_is_rejected(client, make_user):
    make_user("student@example.com", "correct-password", "student")
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
    )
    original_refresh_token = login_response.json()["refresh_token"]
    client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh_token})

    reuse_response = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh_token})

    assert reuse_response.status_code == 401


def test_refresh_invalid_token_returns_401(client):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_logout_requires_authentication(client):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 401


def test_logout_success_invalidates_refresh_token(client, make_user):
    make_user("student@example.com", "correct-password", "student")
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
    )
    tokens = login_response.json()

    logout_response = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert logout_response.status_code == 204

    refresh_after_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_after_logout.status_code == 401


def test_change_password_wrong_current_password_returns_401(client, make_user):
    make_user("student@example.com", "correct-password", "student")
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
    )
    access_token = login_response.json()["access_token"]

    response = client.put(
        "/api/v1/auth/password",
        json={"current_password": "wrong-password", "new_password": "brand-new-password"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 401


def test_change_password_success_allows_login_with_new_password(client, make_user):
    make_user("student@example.com", "correct-password", "student")
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
    )
    access_token = login_response.json()["access_token"]

    change_response = client.put(
        "/api/v1/auth/password",
        json={"current_password": "correct-password", "new_password": "brand-new-password"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert change_response.status_code == 200

    new_login = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "brand-new-password"}
    )
    assert new_login.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
    )
    assert old_login.status_code == 401


def test_change_password_new_equal_to_current_returns_422(client, make_user):
    # VR-002, enforced at the schema layer.
    make_user("student@example.com", "correct-password", "student")
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "correct-password"}
    )
    access_token = login_response.json()["access_token"]

    response = client.put(
        "/api/v1/auth/password",
        json={"current_password": "correct-password", "new_password": "correct-password"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 422
