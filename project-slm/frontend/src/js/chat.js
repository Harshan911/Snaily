/**
 * Chat Module — Message rendering, input handling, streaming.
 */

const Chat = {
    conversationId: null,
    isGenerating: false,
    welcomeVisible: true,

    init() {
        this.input = document.getElementById('chat-input');
        this.btnSend = document.getElementById('btn-send');
        this.messagesEl = document.getElementById('messages');
        this.welcomeScreen = document.getElementById('welcome-screen');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.chatContainer = document.getElementById('chat-container');
        this.tokenCounter = document.getElementById('token-counter');
        this.topbarStatus = document.getElementById('topbar-status');

        this._bindEvents();
    },

    _bindEvents() {
        // Send on Enter
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.send();
            }
        });

        // Enable/disable send button
        this.input.addEventListener('input', () => {
            this.btnSend.disabled = !this.input.value.trim();
            this._autoResize();
        });

        // Send button click
        this.btnSend.addEventListener('click', () => this.send());

        // New chat button
        document.getElementById('btn-new-chat').addEventListener('click', () => {
            this.newChat();
        });
    },

    _autoResize() {
        this.input.style.height = 'auto';
        this.input.style.height = Math.min(this.input.scrollHeight, 150) + 'px';
    },

    async send() {
        const message = this.input.value.trim();
        if (!message || this.isGenerating) return;

        // Hide welcome screen
        if (this.welcomeVisible) {
            this.welcomeScreen.classList.add('hidden');
            this.welcomeVisible = false;
        }

        // Add user message
        this._addMessage('user', message);

        // Clear input
        this.input.value = '';
        this.input.style.height = 'auto';
        this.btnSend.disabled = true;

        // Show typing indicator
        this._setGenerating(true);

        try {
            // Stream response
            let assistantEl = this._addMessage('assistant', '', true);
            let fullResponse = '';

            await API.chatStream(
                message,
                this.conversationId,
                // onToken
                (token, convId) => {
                    this.conversationId = convId;
                    fullResponse += token;
                    this._updateStreamingMessage(assistantEl, fullResponse);
                    this._scrollToBottom();
                },
                // onDone
                (data) => {
                    if (data && data.tools_used && data.tools_used.length > 0) {
                        this._addToolBadges(assistantEl, data.tools_used);
                    }
                    this._setGenerating(false);
                    Sidebar.refreshMemory();
                }
            );
        } catch (error) {
            this._addMessage('assistant', `⚠️ Error: ${error.message}. Make sure the backend is running (\`python main.py\`).`);
            this._setGenerating(false);
        }
    },

    _addMessage(role, content, isStreaming = false) {
        const div = document.createElement('div');
        div.className = `message message-${role}`;

        const avatar = role === 'user' ? '👤' : '🐉';
        const roleName = role === 'user' ? 'You' : 'Blue Dragon';

        div.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-role">${roleName}</div>
                <div class="message-text">${isStreaming ? '<span class="streaming-cursor">▊</span>' : this._renderMarkdown(content)}</div>
            </div>
        `;

        this.messagesEl.appendChild(div);
        this._scrollToBottom();

        return div;
    },

    _updateStreamingMessage(el, content) {
        const textEl = el.querySelector('.message-text');
        textEl.innerHTML = this._renderMarkdown(content) + '<span class="streaming-cursor">▊</span>';
    },

    _addToolBadges(el, tools) {
        const contentEl = el.querySelector('.message-content');
        const toolsDiv = document.createElement('div');
        toolsDiv.className = 'message-tools';
        tools.forEach(t => {
            toolsDiv.innerHTML += `<span class="tool-badge">🔧 ${t}</span>`;
        });
        contentEl.appendChild(toolsDiv);
    },

    _renderMarkdown(text) {
        // Lightweight markdown rendering
        let html = text
            // Code blocks
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
            // Inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Bold
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            // Headers
            .replace(/^### (.+)$/gm, '<h4>$1</h4>')
            .replace(/^## (.+)$/gm, '<h3>$1</h3>')
            .replace(/^# (.+)$/gm, '<h2>$1</h2>')
            // Unordered lists
            .replace(/^- (.+)$/gm, '<li>$1</li>')
            // Ordered lists
            .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
            // Links
            .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Line breaks → paragraphs
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Wrap in paragraph
        html = '<p>' + html + '</p>';

        // Wrap consecutive <li> in <ul>
        html = html.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');

        return html;
    },

    _setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.typingIndicator.classList.toggle('hidden', !isGenerating);
        this.topbarStatus.textContent = isGenerating ? 'Generating...' : 'Ready';
        this.topbarStatus.style.color = isGenerating
            ? 'var(--warning)'
            : 'var(--success)';

        if (!isGenerating) {
            // Remove streaming cursor
            const cursors = document.querySelectorAll('.streaming-cursor');
            cursors.forEach(c => c.remove());
        }
    },

    _scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    },

    newChat() {
        this.conversationId = null;
        this.messagesEl.innerHTML = '';
        this.welcomeScreen.classList.remove('hidden');
        this.welcomeVisible = true;
        this.input.focus();
    },
};
