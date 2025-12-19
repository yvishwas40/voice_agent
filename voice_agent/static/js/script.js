// Get DOM elements
console.log("Voice Agent Script Loaded Successfully");
const statusText = document.getElementById('status-text');
const statusDot = document.querySelector('.status-dot');
const chatMessages = document.getElementById('chat-messages');
const terminal = document.getElementById('terminal');
const micButton = document.getElementById('mic-button');
const textInput = document.getElementById('text-input');
const textSendBtn = document.getElementById('text-send');
const recordingIndicator = document.getElementById('recording-indicator');

// WebSocket connection
const ws = new WebSocket("ws://" + window.location.host + "/ws");

let isListening = false;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// Status translations
const statusTranslations = {
    'IDLE': 'సిద్ధంగా ఉన్నది',
    'LISTENING': 'వినడం జరుగుతోంది...',
    'THINKING': 'విచారణ చేస్తోంది...',
    'SPEAKING': 'మాట్లాడుతోంది...',
    'CONNECTED': 'కనెక్ట్ అయ్యింది',
    'DISCONNECTED': 'కనెక్ట్ కాలేదు'
};

ws.onopen = () => {
    console.log("Connected to Agent");
    updateStatus('CONNECTED');
    reconnectAttempts = 0;
    addLog('వెబ్‌సాకెట్ కనెక్షన్ స్థాపించబడింది');
};

ws.onclose = () => {
    console.log("Disconnected from Agent");
    updateStatus('DISCONNECTED');
    addLog('కనెక్షన్ తెగిపోయింది. తిరిగి కనెక్ట్ చేస్తోంది...');

    // Auto-reconnect logic
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        setTimeout(() => {
            connectWebSocket();
        }, 2000 * reconnectAttempts);
    }
};

ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    addLog('దోషం: ' + error.message);
};

ws.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);

        if (data.type === 'status') {
            updateStatus(data.payload);
        }
        else if (data.type === 'transcript') {
            addMessage(data.payload.role, data.payload.text);
        }
        else if (data.type === 'thought') {
            addLog(data.payload);
        }
        else if (data.type === 'control') {
            handleControl(data.payload);
        }
    } catch (error) {
        console.error("Error parsing WebSocket message:", error);
    }
};

function connectWebSocket() {
    if (ws.readyState === WebSocket.CLOSED) {
        location.reload(); // Simple reconnect by reloading
    }
}

function updateStatus(status) {
    const translatedStatus = statusTranslations[status] || status;
    statusText.textContent = translatedStatus;

    // Update status dot
    statusDot.className = 'status-dot';
    if (status === 'LISTENING') {
        statusDot.classList.add('listening');
        micButton.classList.add('recording');
        recordingIndicator.style.display = 'flex';
    } else if (status === 'THINKING') {
        statusDot.classList.add('thinking');
        micButton.classList.remove('recording');
        recordingIndicator.style.display = 'none';
    } else if (status === 'SPEAKING') {
        statusDot.classList.add('speaking');
        micButton.classList.remove('recording');
        recordingIndicator.style.display = 'none';
    } else {
        statusDot.classList.remove('listening', 'thinking', 'speaking');
        micButton.classList.remove('recording');
        recordingIndicator.style.display = 'none';
    }
}

function addMessage(role, text) {
    // Remove welcome message if it exists
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg && chatMessages.children.length > 1) {
        welcomeMsg.remove();
    }

    const messageContainer = document.createElement('div');
    messageContainer.className = role === 'user' ? 'user-msg' : 'agent-msg';

    if (role === 'agent') {
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message';

        const avatar = document.createElement('div');
        avatar.className = 'agent-avatar';
        avatar.innerHTML = '<i class="fas fa-user-tie"></i>';

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message agent-msg';

        const p = document.createElement('p');
        p.textContent = text;

        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = getCurrentTime();

        messageDiv.appendChild(p);
        messageDiv.appendChild(timeSpan);

        welcomeDiv.appendChild(avatar);
        welcomeDiv.appendChild(messageDiv);

        chatMessages.appendChild(welcomeDiv);
    } else {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-msg';

        const p = document.createElement('p');
        p.textContent = text;

        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = getCurrentTime();

        messageDiv.appendChild(p);
        messageDiv.appendChild(timeSpan);

        chatMessages.appendChild(messageDiv);
    }

    // Auto-scroll to bottom
    scrollToBottom();
}

function addLog(text) {
    const div = document.createElement('div');
    div.className = 'line';
    div.textContent = `> ${text}`;
    terminal.appendChild(div);
    terminal.scrollTop = terminal.scrollHeight;
}

function getCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

function scrollToBottom() {
    // Smooth scroll to bottom
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

function handleControl(payload) {
    if (payload === 'listening_on') {
        isListening = true;
        micButton.classList.add('recording');
        recordingIndicator.style.display = 'flex';
    } else if (payload === 'listening_off') {
        isListening = false;
        micButton.classList.remove('recording');
        recordingIndicator.style.display = 'none';
    }
}

// Mic button click handler - Toggle listening
micButton.addEventListener('click', () => {
    if (ws.readyState !== WebSocket.OPEN) {
        alert('కనెక్షన్ లేదు. దయచేసి పేజీని రిఫ్రెష్ చేయండి.');
        return;
    }

    if (isListening) {
        // Stop listening
        ws.send(JSON.stringify({ type: 'listen_stop' }));
        micButton.classList.remove('recording');
        recordingIndicator.style.display = 'none';
        isListening = false;
    } else {
        // Start listening
        ws.send(JSON.stringify({ type: 'listen_start' }));
        micButton.classList.add('recording');
        recordingIndicator.style.display = 'flex';
        isListening = true;
    }
});

// Send button click handler
textSendBtn.addEventListener('click', sendTypedMessage);

// Enter key handler
textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendTypedMessage();
    }
});

// Debounce mechanism to prevent duplicate sends
let isSending = false;

// Send typed message function
function sendTypedMessage() {
    const value = textInput.value.trim();
    if (!value || isSending) return; // Prevent duplicate sends

    isSending = true;

    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'text', payload: value }));
        textInput.value = '';
        // Reset sending flag after a short delay to prevent rapid duplicate sends
        setTimeout(() => {
            isSending = false;
        }, 500);
        textInput.focus();
    } else {
        isSending = false;
        alert('కనెక్షన్ లేదు. దయచేసి కొద్దిసేపు వేచి ఉండండి.');
    }
}

// Focus input on load
window.addEventListener('load', () => {
    textInput.focus();
});

// Keep input focused when clicking in chat area
chatMessages.addEventListener('click', () => {
    textInput.focus();
});

// Prevent form submission on Enter
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
        });
    }
});

// Handle page visibility - pause/resume when tab is hidden/visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden && isListening) {
        // Optionally stop listening when tab is hidden
        // ws.send(JSON.stringify({ type: 'listen_stop' }));
    }
});
