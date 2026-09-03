from datetime import datetime

from flask import Flask, render_template
from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.config["SECRET_KEY"] = "development-secret-key"

socketio = SocketIO(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


@socketio.on("send_message")
def handle_message(data):
    if not isinstance(data, dict):
        return

    username = data.get("username", "Guest")
    message = data.get("message", "")

    if not isinstance(username, str):
        username = "Guest"

    if not isinstance(message, str):
        return

    username = username.strip()[:20] or "Guest"
    message = message.strip()[:500]

    if not message:
        return

    message_data = {
        "username": username,
        "message": message,
        "timestamp": datetime.now().strftime("%I:%M %p"),
    }

    emit("receive_message", message_data, broadcast=True)


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
    )