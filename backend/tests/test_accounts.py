async def test_signup_creates_a_worker_account(client):
    phone = "+263771234567"

    response = await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "correct-horse", "name": "Tendai", "role": "WORKER"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["phone"] == phone
    assert me.json()["role"] == "WORKER"
    assert me.json()["display_name"] == "Tendai"


async def test_signup_without_role_defaults_to_buyer(client):
    phone = "+263771234568"

    response = await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "correct-horse", "name": "Rudo"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["role"] == "BUYER"


async def test_signup_rejects_a_phone_that_already_has_an_account(client):
    phone = "+263771234569"
    await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "correct-horse", "name": "Tapiwa", "role": "WORKER"},
    )

    second = await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "another-password", "name": "Tapiwa", "role": "BUYER"},
    )
    assert second.status_code == 409


async def test_signup_rejects_invalid_role(client):
    response = await client.post(
        "/auth/signup",
        json={
            "phone": "+263771234570",
            "password": "correct-horse",
            "name": "Blessing",
            "role": "NOT_A_ROLE",
        },
    )
    assert response.status_code == 422


async def test_signin_with_correct_password_succeeds(client):
    phone = "+263771234571"
    await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "correct-horse", "name": "Farai", "role": "WORKER"},
    )

    response = await client.post(
        "/auth/signin", json={"phone": phone, "password": "correct-horse"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["phone"] == phone


async def test_signin_with_wrong_password_is_rejected(client):
    phone = "+263771234572"
    await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "correct-horse", "name": "Chipo", "role": "WORKER"},
    )

    response = await client.post(
        "/auth/signin", json={"phone": phone, "password": "wrong-password"}
    )
    assert response.status_code == 401


async def test_signin_with_unknown_phone_is_rejected(client):
    response = await client.post(
        "/auth/signin", json={"phone": "+263771234573", "password": "correct-horse"}
    )
    assert response.status_code == 401


async def test_signin_token_lasts_the_configured_seven_days(client):
    from datetime import datetime, timezone

    from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, decode_access_token

    phone = "+263771234574"
    await client.post(
        "/auth/signup",
        json={"phone": phone, "password": "correct-horse", "name": "Nyasha", "role": "WORKER"},
    )
    response = await client.post(
        "/auth/signin", json={"phone": phone, "password": "correct-horse"}
    )
    claims = decode_access_token(response.json()["access_token"])

    remaining_minutes = (claims["exp"] - datetime.now(timezone.utc).timestamp()) / 60
    assert remaining_minutes > ACCESS_TOKEN_EXPIRE_MINUTES - 5
