# ChatFlow

ChatFlow is a simple real-time chat application built with Python, Flask and Socket.IO.

## Features

- Choose a display name
- Send and receive messages in real time
- Display message timestamps
- Responsive homepage
- Health-check endpoint
- No password required

## Technologies

- Python
- Flask
- Flask-SocketIO
- HTML
- CSS
- JavaScript
- Socket.IO

## Project structure

```text
simple-chat-app/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── style.css
    ├── images/
    │   └── chat-illustration.svg
    └── js/
        └── chat.js
```

## Run locally on macOS

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Start ChatFlow:

```bash
python app.py
```

Open in your browser:

```text
http://127.0.0.1:5000
```

## Health check

Open:

```text
http://127.0.0.1:5000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

## DevSecOps roadmap

This project will include:

- Automated tests
- Docker containerization
- GitHub Actions CI/CD
- Secret scanning
- Dependency scanning
- Container vulnerability scanning
- Kubernetes deployment
- New Relic monitoring
