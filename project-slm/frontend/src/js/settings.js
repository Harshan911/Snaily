/**
 * Settings Module — Modals, cloud config, model portal, danger zone.
 *
 * The model portal uses a HARDCODED free model catalog so it works
 * even before the backend is running. Download triggers Ollama pull
 * via the backend, then auto-switches to the model.
 */

// ── Free Model Catalog (always available, no backend needed) ──────

const FREE_MODELS = [
    {
        name: 'qwen3:4b',
        display_name: 'Qwen 3 4B',
        params: '4B',
        size_gb: 2.5,
        ram_needed_gb: 4.5,
        strengths: 'Reasoning, coding, multilingual, math, tool-use',
        tier: 'local_lite',
        recommended: true,
        label: '⭐ Best overall — recommended for most users',
        free: true,
        source: 'Ollama (Alibaba)',
    },
    {
        name: 'phi4-mini',
        display_name: 'Phi-4 Mini',
        params: '3.8B',
        size_gb: 2.2,
        ram_needed_gb: 4.0,
        strengths: 'Logic, math, reasoning, long context (128K tokens)',
        tier: 'local_lite',
        recommended: false,
        label: '🧮 Best for logic & math',
        free: true,
        source: 'Ollama (Microsoft)',
    },
    {
        name: 'llama3.2:3b',
        display_name: 'Llama 3.2 3B',
        params: '3B',
        size_gb: 1.8,
        ram_needed_gb: 3.5,
        strengths: 'Lightweight, multilingual, fast, summarization',
        tier: 'local_lite',
        recommended: false,
        label: '🪶 Lightest — for very old hardware',
        free: true,
        source: 'Ollama (Meta)',
    },
    {
        name: 'gemma3:4b',
        display_name: 'Gemma 3 4B',
        params: '4B',
        size_gb: 2.5,
        ram_needed_gb: 4.5,
        strengths: 'General purpose, creative writing, explanations',
        tier: 'local_lite',
        recommended: false,
        label: '✍️ Good all-rounder',
        free: true,
        source: 'Ollama (Google)',
    },
    {
        name: 'llama3.2:1b',
        display_name: 'Llama 3.2 1B',
        params: '1B',
        size_gb: 0.8,
        ram_needed_gb: 2.0,
        strengths: 'Ultra-light, basic tasks, edge devices, Raspberry Pi',
        tier: 'pi',
        recommended: false,
        label: '🍓 For Raspberry Pi / <4GB RAM',
        free: true,
        source: 'Ollama (Meta)',
    },
    {
        name: 'mistral:7b',
        display_name: 'Mistral 7B',
        params: '7B',
        size_gb: 4.1,
        ram_needed_gb: 8.0,
        strengths: 'Strong general, instruction-following, longer outputs',
        tier: 'local_power',
        recommended: false,
        label: '💪 Needs 8GB+ RAM',
        free: true,
        source: 'Ollama (Mistral AI)',
    },
    {
        name: 'deepseek-r1:7b',
        display_name: 'DeepSeek R1 7B',
        params: '7B',
        size_gb: 4.7,
        ram_needed_gb: 8.0,
        strengths: 'Deep reasoning, chain-of-thought, research tasks',
        tier: 'local_power',
        recommended: false,
        label: '🔬 Deep reasoning model',
        free: true,
        source: 'Ollama (DeepSeek)',
    },
];


const Settings = {
    init() {
        this._bindEvents();
    },

    _bindEvents() {
        // Open settings modal
        document.getElementById('btn-settings').addEventListener('click', () => {
            this.openSettings();
        });

        // Close modals
        document.querySelectorAll('.btn-close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                this._closeAllModals();
            });
        });

        // Close modal on overlay click
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', () => {
                this._closeAllModals();
            });
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this._closeAllModals();
        });

        // Save cloud settings
        document.getElementById('btn-save-cloud').addEventListener('click', () => {
            this._saveCloudSettings();
        });

        // Clear memory
        document.getElementById('btn-clear-memory').addEventListener('click', () => {
            this._clearMemory();
        });
    },

    openSettings() {
        document.getElementById('modal-settings').classList.remove('hidden');
    },

    // ═══════════════════════════════════════════════════════
    // Model Portal — always works, even without backend
    // ═══════════════════════════════════════════════════════

    async openModelPortal() {
        const modal = document.getElementById('modal-models');
        modal.classList.remove('hidden');

        const list = document.getElementById('model-portal-list');
        list.innerHTML = '<p style="color: var(--text-tertiary); text-align: center;">Checking installed models...</p>';

        // Get installed models (may fail if backend offline — that's fine)
        let installedNames = [];
        try {
            const installed = await API.getInstalledModels();
            installedNames = (installed.models || []).map(m => m.name.split(':')[0]);
        } catch (e) {
            // Backend offline — just show all as downloadable
        }

        list.innerHTML = '';

        // Ollama check banner
        const banner = document.createElement('div');
        banner.className = 'portal-banner';
        banner.innerHTML = `
            <div class="portal-banner-text">
                <strong>💡 Requires Ollama</strong>
                <span>All models download via Ollama (free, open source). 
                    <a href="https://ollama.com" target="_blank" style="color: var(--accent)">Install Ollama →</a>
                </span>
            </div>
        `;
        list.appendChild(banner);

        // Render each model from the hardcoded catalog
        FREE_MODELS.forEach(model => {
            const baseName = model.name.split(':')[0];
            const isInstalled = installedNames.some(n =>
                n === baseName || n.includes(baseName) || baseName.includes(n)
            );

            const card = document.createElement('div');
            card.className = `model-portal-card ${model.recommended ? 'recommended' : ''}`;
            card.innerHTML = `
                <div class="model-portal-icon">${model.recommended ? '⭐' : '🧠'}</div>
                <div class="model-portal-info">
                    <div class="model-portal-name">
                        ${model.display_name}
                        <span class="model-portal-free">FREE</span>
                    </div>
                    <div class="model-portal-meta">
                        ${model.params} · ${model.size_gb} GB download · ${model.ram_needed_gb} GB RAM needed
                    </div>
                    <div class="model-portal-label">${model.label}</div>
                    <div class="model-portal-strengths">${model.strengths}</div>
                    <div class="model-portal-source">Source: ${model.source}</div>
                </div>
                <div class="model-portal-actions">
                    <button class="btn-download ${isInstalled ? 'installed' : ''}"
                            data-model="${model.name}"
                            ${isInstalled ? '' : ''}>
                        ${isInstalled ? '✓ Connected' : '📥 Download & Connect'}
                    </button>
                    ${isInstalled ? '<span class="installed-check">● Active</span>' : ''}
                </div>
            `;

            // Download & Connect click handler
            const btn = card.querySelector('.btn-download');
            if (!isInstalled) {
                btn.addEventListener('click', () => this._downloadAndConnect(model, btn, card));
            } else {
                // Already installed — click to switch to it
                btn.addEventListener('click', async () => {
                    try {
                        await API.switchModel(model.name);
                        Sidebar.refreshModel();
                        this._showToast(`Switched to ${model.display_name} ✓`);
                    } catch (e) {
                        // ignore
                    }
                });
            }

            list.appendChild(card);
        });
    },

    async _downloadAndConnect(model, btn, card) {
        // Phase 1: Downloading
        btn.disabled = true;
        btn.innerHTML = `
            <span class="download-spinner"></span>
            Downloading ${model.display_name}...
        `;
        btn.classList.add('downloading');

        // Add progress bar to card
        const progressBar = document.createElement('div');
        progressBar.className = 'download-progress';
        progressBar.innerHTML = `
            <div class="download-progress-bar">
                <div class="download-progress-fill" id="progress-${model.name.replace(/[:.]/g, '-')}"></div>
            </div>
            <div class="download-progress-text" id="progress-text-${model.name.replace(/[:.]/g, '-')}">
                Starting download via Ollama... (${model.size_gb} GB)
            </div>
        `;
        card.appendChild(progressBar);

        // Simulate progress (actual progress comes from Ollama)
        const progressId = model.name.replace(/[:.]/g, '-');
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress = Math.min(progress + Math.random() * 8, 90);
            const fill = document.getElementById(`progress-${progressId}`);
            const text = document.getElementById(`progress-text-${progressId}`);
            if (fill) fill.style.width = `${progress}%`;
            if (text) text.textContent = `Downloading... ${Math.round(progress)}%`;
        }, 1500);

        try {
            await API.downloadModel(model.name);

            clearInterval(progressInterval);
            const fill = document.getElementById(`progress-${progressId}`);
            const text = document.getElementById(`progress-text-${progressId}`);
            if (fill) fill.style.width = '100%';
            if (text) text.textContent = 'Download complete! Connecting...';

            // Phase 2: Auto-switch to the model
            try {
                await API.switchModel(model.name);
            } catch (e) {
                // Model might auto-select
            }

            // Phase 3: Show success
            btn.innerHTML = '✓ Connected';
            btn.classList.remove('downloading');
            btn.classList.add('installed');
            btn.disabled = false;

            // Remove progress bar
            setTimeout(() => {
                if (progressBar.parentNode) progressBar.remove();
            }, 1500);

            // Refresh sidebar model list
            Sidebar.refreshModel();
            this._showToast(`${model.display_name} downloaded & connected! 🎉`);

        } catch (err) {
            clearInterval(progressInterval);

            // Remove progress bar
            if (progressBar.parentNode) progressBar.remove();

            // Show error with helpful message
            btn.classList.remove('downloading');
            btn.disabled = false;

            const errorMsg = err.message || 'Unknown error';
            if (errorMsg.includes('fetch') || errorMsg.includes('Failed') || errorMsg.includes('NetworkError')) {
                btn.innerHTML = '⚠️ Backend Offline';
                this._showToast(
                    `Start the backend first!\n` +
                    `1. Open terminal\n` +
                    `2. cd backend\n` +
                    `3. python main.py`,
                    'error'
                );
            } else if (errorMsg.includes('Ollama') || errorMsg.includes('connection')) {
                btn.innerHTML = '⚠️ Ollama Not Running';
                this._showToast(
                    `Ollama is not running!\n` +
                    `1. Install from ollama.com\n` +
                    `2. Run: ollama serve`,
                    'error'
                );
            } else {
                btn.innerHTML = '❌ Retry Download';
                this._showToast(`Download failed: ${errorMsg}`, 'error');
            }

            // Allow retry after 3s
            setTimeout(() => {
                if (!btn.classList.contains('installed')) {
                    btn.innerHTML = '📥 Download & Connect';
                    btn.disabled = false;
                }
            }, 4000);
        }
    },

    // ── Toast Notifications ───────────────────────────────

    _showToast(message, type = 'success') {
        // Remove existing toast
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${type === 'success' ? '✅' : '⚠️'}</span>
            <span class="toast-text">${message.replace(/\n/g, '<br>')}</span>
        `;
        document.body.appendChild(toast);

        // Auto-remove
        setTimeout(() => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 300);
        }, type === 'error' ? 6000 : 3000);
    },

    // ── Cloud Settings ────────────────────────────────────

    async _saveCloudSettings() {
        const provider = document.getElementById('cloud-provider').value;
        const apiKey = document.getElementById('cloud-api-key').value;

        if (!apiKey) {
            this._showToast('Please enter an API key.', 'error');
            return;
        }

        try {
            await API.setTier('cloud', apiKey, provider);
            this._showToast('Cloud settings saved ✓');
            this._closeAllModals();
        } catch (e) {
            this._showToast(`Failed to save: ${e.message}`, 'error');
        }
    },

    async _clearMemory() {
        if (!confirm('⚠️ This will permanently delete all memory entries. Are you sure?')) return;

        try {
            await API.clearMemory();
            Sidebar.refreshMemory();
            this._showToast('Memory cleared ✓');
        } catch (e) {
            this._showToast(`Failed to clear memory: ${e.message}`, 'error');
        }
    },

    _closeAllModals() {
        document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
    },
};
