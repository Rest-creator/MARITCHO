async def test_login_with_worker_role_creates_a_worker_account(client):
    phone = "+263771234567"

    response = await client.post(
        "/token", data={"username": phone, "password": "", "role": "WORKER"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["phone"] == phone
    assert me.json()["role"] == "WORKER"


async def test_login_without_role_still_defaults_to_buyer(client):
    phone = "+263771234568"

    response = await client.post("/token", data={"username": phone, "password": ""})
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["role"] == "BUYER"


async def test_a_second_login_with_a_different_role_does_not_change_existing_account(client):
    phone = "+263771234569"

    first = await client.post(
        "/token", data={"username": phone, "password": "", "role": "WORKER"}
    )
    assert first.json()["access_token"]

    second = await client.post(
        "/token", data={"username": phone, "password": "", "role": "BUYER"}
    )
    token = second.json()["access_token"]

    me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["role"] == "WORKER"


async def test_login_rejects_invalid_role(client):
    response = await client.post(
        "/token", data={"username": "+263771234570", "password": "", "role": "NOT_A_ROLE"}
    )
    assert response.status_code == 422
