import pytest

from app import app, socketio


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def socket_client():
    return socketio.test_client(app)


def test_home_route_renders_index(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<html" in response.data.lower()


def test_health_route_returns_healthy(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


def test_send_message_broadcasts_valid_payload(socket_client):
    socket_client.emit("send_message", {"username": "alice", "message": "hi there"})

    received = socket_client.get_received()

    assert len(received) == 1
    event = received[0]
    assert event["name"] == "receive_message"
    payload = event["args"][0]
    assert payload["username"] == "alice"
    assert payload["message"] == "hi there"
    assert "timestamp" in payload


def test_send_message_defaults_missing_username_to_guest(socket_client):
    socket_client.emit("send_message", {"message": "no username here"})

    received = socket_client.get_received()

    assert received[0]["args"][0]["username"] == "Guest"


def test_send_message_falls_back_to_guest_for_non_string_username(socket_client):
    socket_client.emit("send_message", {"username": 12345, "message": "hello"})

    received = socket_client.get_received()

    assert received[0]["args"][0]["username"] == "Guest"


def test_send_message_trims_and_truncates_username_and_message(socket_client):
    long_username = "  " + ("u" * 30) + "  "
    long_message = "m" * 600

    socket_client.emit("send_message", {"username": long_username, "message": long_message})

    payload = socket_client.get_received()[0]["args"][0]
    assert payload["username"] == "u" * 20
    assert payload["message"] == "m" * 500


def test_send_message_ignores_non_dict_payload(socket_client):
    socket_client.emit("send_message", "not-a-dict")

    assert socket_client.get_received() == []


def test_send_message_ignores_non_string_message(socket_client):
    socket_client.emit("send_message", {"username": "bob", "message": 42})

    assert socket_client.get_received() == []


def test_send_message_ignores_blank_message(socket_client):
    socket_client.emit("send_message", {"username": "bob", "message": "   "})

    assert socket_client.get_received() == []


def test_send_message_ignores_empty_message(socket_client):
    socket_client.emit("send_message", {"username": "bob", "message": ""})

    assert socket_client.get_received() == []
