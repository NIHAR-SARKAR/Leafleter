"""Authentication endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    """Test user registration and login flow."""
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "organization_name": "Test Org",
        },
    )
    assert register_response.status_code == 201
    data = register_response.json()
    assert data["email"] == "test@example.com"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test login with invalid credentials returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nope@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
