document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    const homeSection = document.getElementById("home-section");
    const chatSection = document.getElementById("chat-section");

    const usernameInput = document.getElementById("username-input");
    const startButton = document.getElementById("start-button");
    const nameError = document.getElementById("name-error");
    const currentUsername = document.getElementById("current-username");

    const messages = document.getElementById("messages");
    const messageForm = document.getElementById("message-form");
    const messageInput = document.getElementById("message-input");
    const leaveButton = document.getElementById("leave-button");

    let username = "";

    function startChat() {
        const enteredName = usernameInput.value.trim();

        if (enteredName === "") {
            nameError.textContent = "Please enter your display name.";
            usernameInput.focus();
            return;
        }

        username = enteredName;
        nameError.textContent = "";
        currentUsername.textContent = username;

        homeSection.classList.add("hidden");
        chatSection.classList.remove("hidden");

        messageInput.focus();
    }

    function displayMessage(sender, message, timestamp) {
        const messageBox = document.createElement("div");
        messageBox.classList.add("message");

        if (sender === username) {
            messageBox.classList.add("own-message");
        }

        const messageHeader = document.createElement("div");
        messageHeader.classList.add("message-header");

        const senderName = document.createElement("strong");
        senderName.textContent = sender;

        const messageTime = document.createElement("span");
        messageTime.textContent =
            timestamp ||
            new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit"
            });

        const messageText = document.createElement("p");
        messageText.textContent = message;

        messageHeader.appendChild(senderName);
        messageHeader.appendChild(messageTime);

        messageBox.appendChild(messageHeader);
        messageBox.appendChild(messageText);

        messages.appendChild(messageBox);
        messages.scrollTop = messages.scrollHeight;
    }

    startButton.addEventListener("click", startChat);

    usernameInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            startChat();
        }
    });

    messageForm.addEventListener("submit", (event) => {
        event.preventDefault();

        const message = messageInput.value.trim();

        if (message === "") {
            messageInput.focus();
            return;
        }

        socket.emit("send_message", {
            username: username,
            message: message
        });

        messageInput.value = "";
        messageInput.focus();
    });

    socket.on("receive_message", (data) => {
        if (!data || typeof data !== "object") {
            return;
        }

        const sender = String(data.username || "Unknown user");
        const message = String(data.message || "").trim();

        if (message === "") {
            return;
        }

        displayMessage(sender, message, data.timestamp);
    });

    leaveButton.addEventListener("click", () => {
        username = "";
        currentUsername.textContent = "";
        usernameInput.value = "";
        messageInput.value = "";

        messages.innerHTML = `
            <div class="welcome-message">
                Welcome! Send your first message.
            </div>
        `;

        chatSection.classList.add("hidden");
        homeSection.classList.remove("hidden");

        usernameInput.focus();
    });
});