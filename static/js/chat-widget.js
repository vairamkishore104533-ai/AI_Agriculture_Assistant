document.addEventListener('DOMContentLoaded', function() {
    const fab = document.getElementById('chat-widget-fab');
    if (!fab) return;
    const panel = document.getElementById('chat-widget-panel');
    const icon = fab.querySelector('i');
    const dot = fab.querySelector('.unread-dot');
    const body = document.getElementById('chat-widget-body');
    const input = document.getElementById('chat-widget-input');
    const sendBtn = document.getElementById('chat-widget-send');
    const suggestions = document.querySelectorAll('.chat-panel-suggestion');
    let hasOpened = false;

    fab.addEventListener('click', () => {
        panel.classList.toggle('open');
        if (panel.classList.contains('open')) {
            icon.classList.remove('fa-comment-dots');
            icon.classList.add('fa-times');
            if (!hasOpened) {
                if (dot) dot.style.display = 'none';
                hasOpened = true;
            }
            input.focus();
        } else {
            icon.classList.remove('fa-times');
            icon.classList.add('fa-comment-dots');
        }
    });

    function appendMessage(role, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `widget-chat-bubble ${role}`;
        
        let htmlText = text;
        if (typeof marked !== 'undefined') {
            htmlText = marked.parse(text);
        } else {
            htmlText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        }
        
        msgDiv.innerHTML = htmlText;
        body.appendChild(msgDiv);
        body.scrollTop = body.scrollHeight;
    }

    async function sendMessage(text) {
        if (!text.trim()) return;
        
        appendMessage('user', text);
        input.value = '';
        input.disabled = true;
        sendBtn.disabled = true;

        const lang = document.documentElement.getAttribute('data-lang') || 'en';
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'widget-chat-bubble bot loading';
        loadingDiv.innerHTML = '<i class="fas fa-ellipsis-h"></i>';
        body.appendChild(loadingDiv);
        body.scrollTop = body.scrollHeight;

        try {
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, language: lang })
            });
            const data = await response.json();
            
            body.removeChild(loadingDiv);
            if (data.success) {
                appendMessage('bot', data.reply);
            } else {
                appendMessage('bot', 'Error: ' + (data.message || 'Could not reach AI.'));
            }
        } catch (err) {
            body.removeChild(loadingDiv);
            appendMessage('bot', 'Network error. Please try again.');
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    sendBtn.addEventListener('click', () => sendMessage(input.value));
    
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input.value);
        }
    });

    suggestions.forEach(s => {
        s.addEventListener('click', () => {
            const text = s.getAttribute('data-text') || s.textContent;
            sendMessage(text);
        });
    });
});
