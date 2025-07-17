import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from api.models import Room
from asgiref.sync import sync_to_async
from chat.asgi import application


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def client(user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.mark.django_db
def test_create_room(client):
    response = client.post("/api/createroom/", {"name": "room1", "password": "secret"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "room1"
    assert "id" in data


@pytest.mark.django_db
def test_join_room_with_correct_password(client, user):
    room = Room.objects.create(name="secure_room", owner=user)
    room.set_password("secret")
    room.save()
    response = client.post(f"/api/joinroom/{room.name}/", {"password": "secret"})
    assert response.status_code == 200
    # Обновляем room из базы, чтобы проверить пользователей
    room.refresh_from_db()
    assert user in room.users.all()


@pytest.mark.django_db
def test_join_room_with_wrong_password(client):
    user2 = User.objects.create_user(username="another", password="123")
    room = Room.objects.create(name="secure_room2", owner=user2)
    room.set_password("rightpass")
    room.save()
    response = client.post(f"/api/joinroom/{room.name}/", {"password": "wrongpass"})
    assert response.status_code == 400
    assert "Неверный пароль" in response.json()["non_field_errors"][0]


@pytest.mark.django_db
def test_create_room_without_password(client):
    response = client.post("/api/createroom/", {"name": "nopassroom"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "nopassroom"


@pytest.mark.django_db
def test_room_owner_auto_assigned(client, user):
    response = client.post("/api/createroom/", {"name": "owner_test"})
    assert response.status_code == 201
    data = response.json()
    room = Room.objects.get(id=data["id"])
    assert room.owner == user



@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_connection():
    user = await sync_to_async(User.objects.create_user)(username="testuser", password="testpass")
    token, _ = await sync_to_async(Token.objects.get_or_create)(user=user)

    room_name = "room_name"
    room = await sync_to_async(Room.objects.create)(name=room_name, owner=user)
    await sync_to_async(room.users.add)(user)
    await sync_to_async(room.save)()

    communicator = WebsocketCommunicator(application, f"/ws/chat/{room_name}/?token={token.key}")
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({"message": "Hello"})
    response = await communicator.receive_json_from()
    assert response["message"] == "Hello"
    assert response["user"] == user.username

    await communicator.disconnect()