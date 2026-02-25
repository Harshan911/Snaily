/**
 * API Client — All backend communication.
 * Single source of truth for API calls.
 * Every call checks res.ok and throws descriptive errors.
 */

const API = {
    BASE_URL: 'http://127.0.0.1:8000',

    // ── Helper ────────────────────────────────────────────

    async _post(path, body = {}) {
        const res = await fetch(`${this.BASE_URL}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `${res.status} ${res.statusText}`);
        }
        return res.json();
    },

    async _get(path) {
        const res = await fetch(`${this.BASE_URL}${path}`);
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `${res.status} ${res.statusText}`);
        }
        return res.json();
    },

    async _delete(path) {
        const res = await fetch(`${this.BASE_URL}${path}`, { method: 'DELETE' });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `${res.status} ${res.statusText}`);
        }
        return res.json();
    },

    // ── Chat ──────────────────────────────────────────────

    async chat(message, conversationId = null) {
        return this._post('/api/chat', {
            message,
            conversation_id: conversationId,
        });
    },

    async chatStream(message, conversationId = null, onToken, onDone, options = {}) {
        const res = await fetch(`${this.BASE_URL}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                conversation_id: conversationId,
                web_search: options.webSearch || false,
                use_memory: options.useMemory !== undefined ? options.useMemory : true,
            }),
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Stream failed: ${res.status} ${res.statusText}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6).trim();
                    if (data === '[DONE]') {
                        if (onDone) onDone();
                        return;
                    }
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.token && onToken) {
                            onToken(parsed.token, parsed.conversation_id);
                        }
                        if (parsed.done && onDone) {
                            onDone(parsed);
                        }
                    } catch (e) {
                        // skip malformed chunks
                    }
                }
            }
        }
    },

    // ── Skills ────────────────────────────────────────────

    async getSkills() {
        return this._get('/api/skills');
    },

    async activateSkill(filename) {
        return this._post('/api/skills/activate', { filename });
    },

    async deactivateSkill(filename) {
        return this._post('/api/skills/deactivate', { filename });
    },

    async deleteSkill(filename) {
        return this._delete(`/api/skills/${encodeURIComponent(filename)}`);
    },

    // ── Memory ────────────────────────────────────────────

    async getMemoryStats() {
        return this._get('/api/memory/stats');
    },

    async clearMemory() {
        return this._delete('/api/memory/clear');
    },

    // ── Models ────────────────────────────────────────────

    async getAvailableModels() {
        return this._get('/api/models/available');
    },

    async getInstalledModels() {
        return this._get('/api/models/installed');
    },

    async getActiveModel() {
        return this._get('/api/models/active');
    },

    async switchModel(modelName) {
        return this._post('/api/models/switch', { model_name: modelName });
    },

    async downloadModel(modelName) {
        return this._post('/api/models/download', { model_name: modelName });
    },

    // ── Settings/Tier ─────────────────────────────────────

    async getTier() {
        return this._get('/api/settings/tier');
    },

    async setTier(tier, apiKey = null, apiProvider = null) {
        return this._post('/api/settings/tier', {
            tier,
            api_key: apiKey,
            api_provider: apiProvider,
        });
    },

    // ── Search Settings ───────────────────────────────────

    async getSearchSettings() {
        return this._get('/api/settings/search');
    },

    async setSearchSettings(firecrawlApiKey) {
        return this._post('/api/settings/search', {
            firecrawl_api_key: firecrawlApiKey
        });
    },

    // ── Health ─────────────────────────────────────────────

    async health() {
        try {
            return await this._get('/api/health');
        } catch (e) {
            return { status: 'offline' };
        }
    },
};
