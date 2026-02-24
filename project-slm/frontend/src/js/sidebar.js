/**
 * Sidebar Module — Model selector, skill dock, memory stats, tier switching.
 */

const Sidebar = {
    isOpen: true,

    init() {
        this.sidebar = document.getElementById('sidebar');
        this.btnToggle = document.getElementById('btn-toggle-sidebar');
        this.modelSelector = document.getElementById('model-selector');
        this.modelDropdown = document.getElementById('model-dropdown');
        this.modelList = document.getElementById('model-list');
        this.activeModelName = document.getElementById('active-model-name');
        this.skillDock = document.getElementById('skill-dock');
        this.topbarModel = document.getElementById('topbar-model');

        this._bindEvents();
        this._loadInitialData();
    },

    _bindEvents() {
        // Toggle sidebar
        this.btnToggle.addEventListener('click', () => this.toggle());

        // Model selector dropdown
        document.getElementById('model-current').addEventListener('click', () => {
            this.modelSelector.classList.toggle('open');
        });

        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            if (!this.modelSelector.contains(e.target)) {
                this.modelSelector.classList.remove('open');
            }
        });

        // Model portal button
        document.getElementById('btn-model-portal').addEventListener('click', () => {
            this.modelSelector.classList.remove('open');
            Settings.openModelPortal();
        });

        // Tier buttons
        document.querySelectorAll('.tier-btn').forEach(btn => {
            btn.addEventListener('click', () => this._switchTier(btn.dataset.tier));
        });

        // Skill dock drag & drop
        this.skillDock.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.skillDock.classList.add('drag-over');
        });

        this.skillDock.addEventListener('dragleave', () => {
            this.skillDock.classList.remove('drag-over');
        });

        this.skillDock.addEventListener('drop', async (e) => {
            e.preventDefault();
            this.skillDock.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                // Validate extension
                if (!file.name.endsWith('.md') && !file.name.endsWith('.yaml') && !file.name.endsWith('.yml')) {
                    Settings._showToast('Only .md, .yaml, .yml skill files allowed.', 'error');
                    return;
                }

                // Upload to backend
                try {
                    const formData = new FormData();
                    formData.append('file', file);

                    const res = await fetch(`${API.BASE_URL}/api/skills/upload`, {
                        method: 'POST',
                        body: formData,
                    });

                    if (!res.ok) {
                        const err = await res.json().catch(() => ({}));
                        throw new Error(err.detail || 'Upload failed');
                    }

                    Settings._showToast(`Skill "${file.name}" uploaded ✓`);
                    await this.refreshSkills();
                } catch (err) {
                    Settings._showToast(`Failed to upload: ${err.message}`, 'error');
                }
            }
        });

        // Toggle pills (web search, memory)
        document.getElementById('btn-web-search-toggle').addEventListener('click', (e) => {
            e.currentTarget.classList.toggle('active');
        });

        document.getElementById('btn-memory-toggle').addEventListener('click', (e) => {
            e.currentTarget.classList.toggle('active');
        });
    },

    async _loadInitialData() {
        // Load everything in parallel
        await Promise.allSettled([
            this.refreshModel(),
            this.refreshSkills(),
            this.refreshMemory(),
        ]);
    },

    toggle() {
        this.isOpen = !this.isOpen;
        this.sidebar.classList.toggle('collapsed', !this.isOpen);
    },

    // ── Model ─────────────────────────────────────────────

    async refreshModel() {
        try {
            const { model } = await API.getActiveModel();
            this.activeModelName.textContent = model || 'No model';
            this.topbarModel.textContent = `🐉 ${model || 'Blue Dragon AI'}`;

            // Load installed models for dropdown
            const { models } = await API.getInstalledModels();
            this.modelList.innerHTML = '';

            if (models && models.length > 0) {
                models.forEach(m => {
                    const div = document.createElement('div');
                    div.className = `model-option ${m.name === model ? 'active' : ''}`;
                    div.innerHTML = `
                        <span>🧠</span>
                        <span>${m.name}</span>
                        <span style="color: var(--text-tertiary); font-size: 11px;">${m.size_gb} GB</span>
                    `;
                    div.addEventListener('click', () => this._switchModel(m.name));
                    this.modelList.appendChild(div);
                });
            } else {
                const emptyDiv = document.createElement('div');
                emptyDiv.className = 'model-option';
                emptyDiv.style.cssText = 'color: var(--accent); cursor: pointer;';
                emptyDiv.textContent = '📥 Get a Free Model →';
                emptyDiv.addEventListener('click', () => {
                    this.modelSelector.classList.remove('open');
                    Settings.openModelPortal();
                });
                this.modelList.appendChild(emptyDiv);
            }
        } catch (e) {
            this.activeModelName.textContent = 'Offline';
            this.topbarModel.textContent = '🐉 Blue Dragon AI (Offline)';
        }
    },

    async _switchModel(name) {
        try {
            await API.switchModel(name);
            this.modelSelector.classList.remove('open');
            await this.refreshModel();
        } catch (e) {
            alert(`Failed to switch model: ${e.message}`);
        }
    },

    async _switchTier(tier) {
        document.querySelectorAll('.tier-btn').forEach(b => b.classList.remove('active'));
        document.querySelector(`[data-tier="${tier}"]`).classList.add('active');

        if (tier === 'cloud') {
            Settings.openSettings();
        } else {
            try {
                await API.setTier('local');
            } catch (e) {
                // Backend offline — that's OK
            }

            // If no local models installed → auto-open model portal
            try {
                const { models } = await API.getInstalledModels();
                if (!models || models.length === 0) {
                    Settings.openModelPortal();
                }
            } catch (e) {
                // Backend offline → still open portal (it works offline with hardcoded list)
                Settings.openModelPortal();
            }
        }
    },

    // ── Skills ────────────────────────────────────────────

    async refreshSkills() {
        try {
            const data = await API.getSkills();
            const skills = data.skills || [];
            const activeNames = data.active || [];

            if (skills.length === 0) {
                this.skillDock.innerHTML = `
                    <div class="skill-empty-state">
                        <span>📄</span>
                        <p>Drop .md skill files here</p>
                    </div>
                `;
                this._updateActiveSkillBadges([]);
                return;
            }

            this.skillDock.innerHTML = '';
            skills.forEach(skill => {
                const isActive = activeNames.includes(skill.name);
                const div = document.createElement('div');
                div.className = 'skill-item';
                div.innerHTML = `
                    <span>📄</span>
                    <span class="skill-item-name" title="${skill.description}">${skill.name}</span>
                    <button class="skill-item-toggle ${isActive ? 'active' : ''}" 
                            data-filename="${skill.filename}"
                            title="${isActive ? 'Deactivate' : 'Activate'}">
                        ${isActive ? '✓' : ''}
                    </button>
                `;

                const toggle = div.querySelector('.skill-item-toggle');
                toggle.addEventListener('click', () => {
                    this._toggleSkill(skill.filename, !isActive);
                });

                this.skillDock.appendChild(div);
            });

            this._updateActiveSkillBadges(skills.filter(s => activeNames.includes(s.name)));
        } catch (e) {
            // Backend offline
        }
    },

    async _toggleSkill(filename, activate) {
        try {
            if (activate) {
                await API.activateSkill(filename);
            } else {
                await API.deactivateSkill(filename);
            }
            await this.refreshSkills();
        } catch (e) {
            alert(`Failed to ${activate ? 'activate' : 'deactivate'} skill: ${e.message}`);
        }
    },

    _updateActiveSkillBadges(activeSkills) {
        const container = document.getElementById('active-skills-badges');
        container.innerHTML = '';
        activeSkills.forEach(s => {
            container.innerHTML += `<span class="skill-badge">📄 ${s.name}</span>`;
        });
    },

    // ── Memory ────────────────────────────────────────────

    async refreshMemory() {
        try {
            const stats = await API.getMemoryStats();
            document.getElementById('memory-count').textContent = stats.total_entries || 0;
            document.getElementById('memory-size').textContent = `${stats.size_mb || 0} MB`;

            // Memory bar (max ~500 MB for visual)
            const pct = Math.min((stats.size_mb || 0) / 500 * 100, 100);
            document.getElementById('memory-bar-fill').style.width = `${pct}%`;
        } catch (e) {
            document.getElementById('memory-count').textContent = '—';
            document.getElementById('memory-size').textContent = '— MB';
        }
    },
};
