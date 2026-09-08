from app import app, socketio


def test_home_page_loads():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Talk freely" in response.data


def test_chat_requires_username():
    client = app.test_client()
    response = client.get("/chat")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_join_accepts_valid_username():
    client = app.test_client()
    response = client.post("/join", data={"username": "Hari Ram"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/chat")


def test_socket_broadcasts_message():
    flask_client = app.test_client()
    with flask_client.session_transaction() as user_session:
        user_session["username"] = "Hari"

    socket_client = socketio.test_client(app, flask_test_client=flask_client)
    assert socket_client.is_connected()
    socket_client.get_received()  # Clear the initial join and presence events.

    socket_client.emit("send_message", {"message": "Hello!"})
    events = socket_client.get_received()
    received = [event for event in events if event["name"] == "receive_message"]

    assert received[0]["args"][0]["username"] == "Hari"
    assert received[0]["args"][0]["message"] == "Hello!"
    socket_client.disconnect()
