/**
 * chat.js - Chat Interface for Natural Language Control
 *
 * Provides a simple chat UI that communicates with Ollama Mistral
 * for natural language control of the simulation.
 */

const API_BASE = 'http://127.0.0.1:8000';

class ChatInterface {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.messages = [];
        this.init();
    }

    init() {
        console.log('[Chat] Initializing chat interface...');

        // Create chat elements if they exist in DOM
        this.messageList = document.getElementById('chat-messages');
        this.input = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('chat-send');

        if (!this.messageList || !this.input || !this.sendBtn) {
            console.error('[Chat] Chat elements not found in DOM');
            return;
        }

        // Event listeners
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        console.log('[Chat] Chat interface initialized');
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        // Add user message to UI
        this.addMessage('user', message);
        this.input.value = '';
        this.input.disabled = true;
        this.sendBtn.disabled = true;

        try {
            // Send to backend
            const response = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Add assistant response
            this.addMessage('assistant', data.response);

            // If there's an action executed, show feedback
            if (data.action_executed) {
                this.addMessage('system', `✓ Executed: ${data.action_executed}`);
            }

        } catch (error) {
            console.error('[Chat] Error:', error);
            this.addMessage('error', `Error: ${error.message}`);
        } finally {
            this.input.disabled = false;
            this.sendBtn.disabled = false;
            this.input.focus();
        }
    }

    addMessage(role, content) {
        this.messages.push({ role, content, timestamp: Date.now() });

        // Create message element
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message chat-${role}`;

        const roleLabel = document.createElement('div');
        roleLabel.className = 'chat-role';
        roleLabel.textContent = role === 'user' ? 'You' :
                               role === 'assistant' ? 'Assistant' :
                               role === 'system' ? 'System' : 'Error';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'chat-content';
        contentDiv.textContent = content;

        msgDiv.appendChild(roleLabel);
        msgDiv.appendChild(contentDiv);
        this.messageList.appendChild(msgDiv);

        // Scroll to bottom
        this.messageList.scrollTop = this.messageList.scrollHeight;
    }

    clear() {
        this.messages = [];
        this.messageList.innerHTML = '';
    }
}

// Initialize chat when DOM is ready
let chatInterface = null;

document.addEventListener('DOMContentLoaded', () => {
    chatInterface = new ChatInterface('chat-container');

    // Add welcome message
    setTimeout(() => {
        chatInterface.addMessage('system', 'Chat interface ready. Try: "Show Chicago status" or "Increase production to 20"');
    }, 500);
});

export { ChatInterface };
