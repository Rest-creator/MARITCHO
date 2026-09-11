async def test_list_suburbs_is_public_and_returns_seeded_data(client):
    response = await client.get("/suburbs")

    assert response.status_code == 200
    names = {s["name"] for s in response.json()}
    assert {"Nkulumane", "Hillside", "Njube", "Entumbane", "Luveve", "Kumalo"} <= names


async def test_list_suburbs_respects_limit_and_offset(client):
    full = (await client.get("/suburbs")).json()
    assert len(full) > 1

    first_page = (await client.get("/suburbs", params={"limit": 1})).json()
    assert len(first_page) == 1
    assert first_page[0]["name"] == full[0]["name"]

    second_page = (await client.get("/suburbs", params={"limit": 1, "offset": 1})).json()
    assert len(second_page) == 1
    assert second_page[0]["name"] == full[1]["name"]


async def test_list_suburbs_rejects_limit_above_the_cap(client):
    response = await client.get("/suburbs", params={"limit": 201})
    assert response.status_code == 422
