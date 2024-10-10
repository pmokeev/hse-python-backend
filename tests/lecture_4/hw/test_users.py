import pytest
from http import HTTPStatus
from faker import Faker
from fastapi.testclient import TestClient
import base64
import pytest_asyncio
import httpx
from asgi_lifespan import LifespanManager
from typing import List

from lecture_4.demo_service.api.main import create_app

app = create_app()
faker = Faker()

@pytest_asyncio.fixture()
async def client():
    transport = httpx.ASGITransport(app=app)

    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://localhost:8000"
        ) as client:
            yield client


@pytest.fixture()
def existing_users() -> list[int]:
    users = [
        {
            "username": f"username_{i}", 
            "name": "name", 
            "birthdate": "2024-10-09T00:00:00", 
            "password": "password123",
        }
        for i in range(2, 10)
    ]

    uid = []

    with TestClient(app) as client:
        for user in users:
            uid.append(client.post("/user-register", json=user).json()["uid"])

    return uid


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("request_body", "status_code", "response_body"),
    [
        (
            {"username": "username", "name": "name", "birthdate": "2024-10-09T00:00:00", "password": "password123"}, 
            HTTPStatus.OK,
            {"uid": 2, "username": "username", "name": "name", "birthdate": "2024-10-09T00:00:00", "role": "user"}, 
        ),
        (
            {"username": "admin", "name": "name", "birthdate": "2024-10-09T00:00:00", "password": "password123"}, 
            HTTPStatus.BAD_REQUEST,
            {"detail": "username is already taken"},
        ),
        (
            {"username": "username", "birthdate": "2024-10-09T00:00:00", "password": "password123"}, 
            HTTPStatus.UNPROCESSABLE_ENTITY,
            {"detail": [{"type": "missing", "loc": ["body", "name"], "msg": "Field required", "input": {"username": "username", "birthdate": "2024-10-09T00:00:00", "password": "password123"}}]},
        ),
        (
            {"username": "username", "name": "name", "birthdate": "2024-10-09T00:00:00", "password": "password"}, 
            HTTPStatus.BAD_REQUEST,
            {"detail": "invalid password"},
        ),
    ],
)
async def test_register_user(
    client,
    request_body: dict,
    status_code: int,
    response_body: dict,
):
    response = await client.post("/user-register", json=request_body)

    print(response)

    assert response.status_code == status_code
    data = response.json()

    assert data == response_body


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("uids"),
    [
        ("existing_users"),
    ],
)
async def test_get_user_by_id(
    client,
    request,
    uids: List[int]
):
    request.getfixturevalue(uids)

    for ind in range(2, 10):
        credentials = base64.b64encode(f"username_{ind}:password123".encode("ascii")).decode("utf-8")

        response = await client.post(
            f"/user-get?id={ind}",
            headers={"Authorization": "Basic " + credentials},
        )

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert f"username_{ind}" == data["username"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("uids"),
    [
        ("existing_users"),
    ],
)
async def test_get_user_by_username(
    client,
    request,
    uids: List[int]
):
    request.getfixturevalue(uids)

    for ind in range(2, 10):
        credentials = base64.b64encode(f"username_{ind}:password123".encode("ascii")).decode("utf-8")

        response = await client.post(
            f"/user-get?username=username_{ind}",
            headers={"Authorization": "Basic " + credentials},
        )

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert f"username_{ind}" == data["username"]


@pytest.mark.asyncio
async def test_get_user_unauthorized(
    client,
):
    response = await client.post(
        f"/user-get?username=username",
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_user_both_query_provided(
    client,
):
    credentials = base64.b64encode(f"admin:superSecretAdminPassword123".encode("ascii")).decode("utf-8")

    response = await client.post(
        f"/user-get?username=username&id=2",
        headers={"Authorization": "Basic " + credentials},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "both id and username are provided"}

@pytest.mark.asyncio
async def test_get_user_neither_query_provided(
    client,
):
    credentials = base64.b64encode(f"admin:superSecretAdminPassword123".encode("ascii")).decode("utf-8")

    response = await client.post(
        f"/user-get",
        headers={"Authorization": "Basic " + credentials},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "neither id nor username are provided"}


@pytest.mark.asyncio
async def test_get_user_user_not_found(
    client,
):
    credentials = base64.b64encode(f"admin:superSecretAdminPassword123".encode("ascii")).decode("utf-8")

    response = await client.post(
        f"/user-get?username=not_found",
        headers={"Authorization": "Basic " + credentials},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "Not Found"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("uids"),
    [
        ("existing_users"),
    ],
)
async def test_get_promote_user(
    client,
    request,
    uids: List[int],
):
    request.getfixturevalue(uids)

    credentials = base64.b64encode(f"admin:superSecretAdminPassword123".encode("ascii")).decode("utf-8")

    response = await client.post(
        f"/user-promote?id=2",
        headers={"Authorization": "Basic " + credentials},
    )

    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("uids"),
    [
        ("existing_users"),
    ],
)
async def test_get_promote_user_not_found(
    client,
    request,
    uids: List[int],
):
    user_uids = request.getfixturevalue(uids)

    credentials = base64.b64encode(f"admin:superSecretAdminPassword123".encode("ascii")).decode("utf-8")

    response = await client.post(
        f"/user-promote?id={max(user_uids) + 1}",
        headers={"Authorization": "Basic " + credentials},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "user not found"}

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("uids"),
    [
        ("existing_users"),
    ],
)
async def test_get_promote_user_unauthorized(
    client,
    request,
    uids: List[int],
):
    request.getfixturevalue(uids)

    credentials = base64.b64encode(f"admin:admin".encode("ascii")).decode("utf-8")

    response = await client.post(
        f"/user-promote?id=2",
        headers={"Authorization": "Basic " + credentials},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Unauthorized"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("uids"),
    [
        ("existing_users"),
    ],
)
async def test_get_promote_user_forbidden(
    client,
    request,
    uids: List[int],
):
    request.getfixturevalue(uids)

    credentials = base64.b64encode(f"username_2:password123".encode("ascii")).decode("utf-8")

    response = await client.post(
        f"/user-promote?id=2",
        headers={"Authorization": "Basic " + credentials},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": "Forbidden"}
