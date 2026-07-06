let currentConvId = null;
let isStreaming = false;
let isFirstMessage = true;

function initChatbot() {
    const messages = document.getElementById("chat-messages");
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send");
    const newBtn = document.getElementById("chat-new-btn");
    const exportBtn = document.getElementById("chat-export-btn");

    if (!messages) return;

    updateConvIdFromActive();
    if (!messages.querySelector(".chat-bubble")) {
        showWelcome();
    } else {
        isFirstMessage = false;
    }

    if (sendBtn && input) {
        sendBtn.addEventListener("click", sendMessage);
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (newBtn) {
        newBtn.addEventListener("click", newConversation);
    }

    if (exportBtn) {
        exportBtn.addEventListener("click", showExportModal);
    }

    document.querySelectorAll(".chat-suggestion-chip").forEach(function (chip) {
        chip.addEventListener("click", function () {
            if (input) {
                input.value = this.getAttribute("data-text") || this.textContent;
                sendMessage();
            }
        });
    });

    document.querySelectorAll(".chat-conv-item").forEach(function (item) {
        item.addEventListener("click", function (e) {
            if (e.target.closest(".chat-conv-delete")) return;
            loadConversation(this.getAttribute("data-conv-id"));
        });
    });

    document.querySelectorAll(".chat-conv-delete").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            deleteConversation(this.getAttribute("data-conv-id"));
        });
    });

    document.querySelectorAll(".chat-export-option").forEach(function (btn) {
        btn.addEventListener("click", function () {
            exportChat(this.getAttribute("data-format"));
        });
    });

    document.querySelector(".chat-export-cancel").addEventListener("click", hideExportModal);
    document.querySelector(".chat-export-overlay").addEventListener("click", hideExportModal);
}

function updateConvIdFromActive() {
    var active = document.querySelector(".chat-conv-item.active");
    if (active) {
        currentConvId = active.getAttribute("data-conv-id");
    } else {
        var first = document.querySelector(".chat-conv-item");
        currentConvId = first ? first.getAttribute("data-conv-id") : null;
    }
}

function showWelcome() {
    var messages = document.getElementById("chat-messages");
    if (!messages) return;
    var suggestions = document.getElementById("chat-suggestions");
    if (suggestions) suggestions.style.display = "block";
}

function addBubble(text, role) {
    var messages = document.getElementById("chat-messages");
    if (!messages) return;
    var div = document.createElement("div");
    div.className = "chat-bubble " + role;

    var content = document.createElement("div");
    content.className = "chat-bubble-content";
    content.innerHTML = renderMarkdown(text);
    div.appendChild(content);

    var actions = document.createElement("div");
    actions.className = "chat-bubble-actions";
    var copyBtn = document.createElement("button");
    copyBtn.className = "chat-copy-btn";
    copyBtn.title = "Copy";
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.addEventListener("click", function () {
        copyToClipboard(text);
    });
    actions.appendChild(copyBtn);
    div.appendChild(actions);

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    var suggestions = document.getElementById("chat-suggestions");
    if (suggestions) suggestions.style.display = "none";
}

function renderMarkdown(text) {
    var html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    html = html.replace(/###\s*(.+?)(\n|$)/g, '<h3>$1</h3>');
    html = html.replace(/##\s*(.+?)(\n|$)/g, '<h2>$1</h2>');
    html = html.replace(/#\s*(.+?)(\n|$)/g, '<h1>$1</h1>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    html = html.replace(/\n/g, '<br>');
    return html;
}

function createStreamBubble() {
    var messages = document.getElementById("chat-messages");
    var div = document.createElement("div");
    div.className = "chat-bubble bot";
    var content = document.createElement("div");
    content.className = "chat-bubble-content";
    content.id = "stream-content";
    div.appendChild(content);
    var actions = document.createElement("div");
    actions.className = "chat-bubble-actions";
    var copyBtn = document.createElement("button");
    copyBtn.className = "chat-copy-btn";
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.addEventListener("click", function () {
        copyToClipboard(content.textContent || content.innerText);
    });
    actions.appendChild(copyBtn);
    div.appendChild(actions);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return content;
}

function sendMessage() {
    if (isStreaming) return;
    var input = document.getElementById("chat-input");
    var prompt = input.value.trim();
    if (!prompt) return;

    var suggestions = document.getElementById("chat-suggestions");
    if (suggestions) suggestions.style.display = "none";

    addBubble(prompt, "user");
    input.value = "";
    setLoading(true);

    var sseUrl = "/api/chat/stream";
    var params = new URLSearchParams();
    fetch(sseUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt, conv_id: currentConvId }),
    })
    .then(function (resp) {
        if (!resp.ok) throw new Error("Network error");
        var reader = resp.body.getReader();
        var decoder = new TextDecoder();
        var streamContent = createStreamBubble();
        var fullText = "";
        isStreaming = true;

        function readChunk() {
            reader.read().then(function (result) {
                if (result.done) {
                    isStreaming = false;
                    setLoading(false);
                    return;
                }
                var text = decoder.decode(result.value, { stream: true });
                var lines = text.split("\n");
                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i].trim();
                    if (line.startsWith("data: ")) {
                        try {
                            var data = JSON.parse(line.substring(6));
                            if (data.chunk) {
                                fullText += data.chunk;
                                streamContent.innerHTML = renderMarkdown(fullText);
                                document.getElementById("chat-messages").scrollTop =
                                    document.getElementById("chat-messages").scrollHeight;
                            }
                            if (data.done) {
                                if (data.conv_id) {
                                    currentConvId = data.conv_id;
                                }
                                var finalContent = document.createElement("div");
                                finalContent.className = "chat-bubble-content";
                                finalContent.innerHTML = renderMarkdown(fullText);
                                streamContent.parentNode.replaceChild(finalContent, streamContent);
                                finalContent.id = "stream-content-final";
                                addConversationToList(data.conv_id, data.title);
                                isStreaming = false;
                                setLoading(false);
                                updateExportBtn();
                            }
                        } catch (e) {
                        }
                    }
                }
                if (isStreaming) {
                    readChunk();
                }
            }).catch(function () {
                isStreaming = false;
                setLoading(false);
                showToast("Error reading response", "error");
            });
        }
        readChunk();
    })
    .catch(function () {
        isStreaming = false;
        setLoading(false);
        showToast("Sorry, an error occurred. Please try again.", "error");
    });
}

function setLoading(loading) {
    var sendBtn = document.getElementById("chat-send");
    var input = document.getElementById("chat-input");
    var typing = document.getElementById("chat-typing");
    if (sendBtn) sendBtn.disabled = loading;
    if (input) input.disabled = loading;
    if (typing) typing.style.display = loading ? "flex" : "none";
}

function newConversation() {
    fetch("/api/chat/new", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            window.location.href = "/ai-chat?conv=" + res.conversation.id;
        }
    });
}

function loadConversation(convId) {
    window.location.href = "/ai-chat?conv=" + convId;
}

function deleteConversation(convId) {
    if (!confirm("Delete this conversation?")) return;
    fetch("/api/chat/conversation/" + convId, { method: "DELETE" })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            var item = document.querySelector('.chat-conv-item[data-conv-id="' + convId + '"]');
            if (item) item.remove();
            if (currentConvId === convId) {
                window.location.href = "/ai-chat";
            }
        }
    });
}

function addConversationToList(convId, title) {
    var existing = document.querySelector('.chat-conv-item[data-conv-id="' + convId + '"]');
    if (!existing) {
        var list = document.getElementById("chat-conversations");
        var empty = list.querySelector(".chat-conv-empty");
        if (empty) empty.remove();
        var div = document.createElement("div");
        div.className = "chat-conv-item active";
        div.setAttribute("data-conv-id", convId);
        div.innerHTML =
            '<div class="chat-conv-title">' + (title || "New Chat") + '</div>' +
            '<div class="chat-conv-meta"><span>—</span>' +
            '<button class="chat-conv-delete" data-conv-id="' + convId + '"><i class="fas fa-trash"></i></button></div>';
        div.addEventListener("click", function () {
            loadConversation(convId);
        });
        div.querySelector(".chat-conv-delete").addEventListener("click", function (e) {
            e.stopPropagation();
            deleteConversation(convId);
        });
        list.insertBefore(div, list.firstChild);
        document.querySelectorAll(".chat-conv-item").forEach(function (item) {
            item.classList.remove("active");
        });
        div.classList.add("active");
    }
    updateExportBtn();
}

function showExportModal() {
    document.getElementById("chat-export-modal").style.display = "block";
}

function hideExportModal() {
    document.getElementById("chat-export-modal").style.display = "none";
}

function exportChat(format) {
    if (!currentConvId) return;
    fetch("/api/chat/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conv_id: currentConvId, format: format }),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            var blob = new Blob([res.export], { type: res.mime });
            var url = URL.createObjectURL(blob);
            var a = document.createElement("a");
            a.href = url;
            a.download = res.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            hideExportModal();
            showToast("Exported successfully!", "success");
        }
    });
}

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
            showToast("Copied!", "success");
        }).catch(function () {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
        document.execCommand("copy");
        showToast("Copied!", "success");
    } catch (e) {
    }
    document.body.removeChild(ta);
}

function showToast(msg, type) {
    var toast = document.getElementById("chat-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.className = "chat-toast " + (type || "");
    toast.style.display = "block";
    setTimeout(function () {
        toast.style.display = "none";
    }, 2500);
}

function updateExportBtn() {
    var btn = document.getElementById("chat-export-btn");
    if (!btn) return;
    var bubbles = document.querySelectorAll("#chat-messages .chat-bubble");
    btn.style.display = bubbles.length > 0 ? "flex" : "none";
}

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("chat-messages")) {
        initChatbot();
    }
});
