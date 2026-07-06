let chatHistory = [];

function initChatbot() {
    const sendBtn = document.getElementById("chat-send");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    const clearBtn = document.getElementById("chat-clear");
    const suggestions = document.querySelectorAll(".chat-suggestion-chip");

    if (!messages || !input) return;

    if (!messages.querySelector(".chat-message")) {
        const lang = document.documentElement.lang || "en";
        const greeting =
            lang === "ta"
                ? "வணக்கம்! நான் AI விவசாய உதவியாளர். தமிழ்நாட்டில் விவசாயம் பற்றி உங்கள் கேள்விகளைக் கேளுங்கள்."
                : "Hello! I am your AI Agriculture Assistant. Ask me anything about farming in Tamil Nadu.";
        addMessage(greeting, "bot");
    }

    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }
    if (input) {
        input.addEventListener("keypress", function (e) {
            if (e.key === "Enter") sendMessage();
        });
    }
    if (clearBtn) {
        clearBtn.addEventListener("click", function () {
            messages.innerHTML = "";
            chatHistory = [];
            const lang = document.documentElement.lang || "en";
            const greeting =
                lang === "ta"
                    ? "வணக்கம்! நான் AI விவசாய உதவியாளர். தமிழ்நாட்டில் விவசாயம் பற்றி உங்கள் கேள்விகளைக் கேளுங்கள்."
                    : "Hello! I am your AI Agriculture Assistant. Ask me anything about farming in Tamil Nadu.";
            addMessage(greeting, "bot");
        });
    }

    suggestions.forEach((chip) => {
        chip.addEventListener("click", function () {
            input.value = this.textContent;
            sendMessage();
        });
    });
}

function sendMessage() {
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    const prompt = input.value.trim();
    if (!prompt) return;

    addMessage(prompt, "user");
    input.value = "";

    const loadingDiv = document.createElement("div");
    loadingDiv.className = "chat-message bot loading";
    loadingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    messages.appendChild(loadingDiv);
    messages.scrollTop = messages.scrollHeight;

    fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
    })
        .then((r) => r.json())
        .then((res) => {
            loadingDiv.remove();
            if (res.success) {
                addMessage(res.response, "bot");
                chatHistory.push({ role: "user", content: prompt });
                chatHistory.push({ role: "assistant", content: res.response });
            } else {
                addMessage(res.message || "Error occurred", "bot");
            }
        })
        .catch(() => {
            loadingDiv.remove();
            const lang = document.documentElement.lang || "en";
            const errMsg =
                lang === "ta"
                    ? "மன்னிக்கவும், பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்."
                    : "Sorry, an error occurred. Please try again.";
            addMessage(errMsg, "bot");
        });
}

function addMessage(text, type) {
    const messages = document.getElementById("chat-messages");
    if (!messages) return;
    const div = document.createElement("div");
    div.className = `chat-message ${type}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("chat-messages")) {
        initChatbot();
    }
});
