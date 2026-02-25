/**
 * App — Main entry point. Initialize all modules.
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize modules
    Chat.init();
    Sidebar.init();
    Settings.init();

    // Wire up input area toggles
    _initInputToggles();

    // Check backend health
    const health = await API.health();
    const statusEl = document.getElementById('topbar-status');

    if (health.status === 'ok') {
        statusEl.textContent = 'Ready';
        statusEl.style.color = 'var(--success)';
        console.log('🐉 Blue Dragon AI Hub — Connected');
        console.log(`   Tier: ${health.tier}`);
        console.log(`   Model: ${health.model}`);
        console.log(`   Skills: ${health.skills_active}`);

        // Update input area labels
        _updateProviderLabel(health.tier);
        document.getElementById('input-model-label').textContent = health.model || '—';
    } else {
        statusEl.textContent = 'Backend Offline';
        statusEl.style.color = 'var(--danger)';
        console.warn('🐉 Blue Dragon AI Hub — Backend not reachable');
        console.warn('   Start the backend: cd backend && python main.py');
    }
});

function _initInputToggles() {
    // Provider toggle — just shows current tier, not clickable to change
    // Users change tier via sidebar buttons (Local / Cloud)
    const providerBtn = document.getElementById('input-toggle-provider');
    providerBtn.style.cursor = 'default';
    providerBtn.title = 'Current inference mode (change via sidebar)';

    // Model toggle — opens model dropdown in sidebar
    const modelBtn = document.getElementById('input-toggle-model');
    modelBtn.addEventListener('click', () => {
        const modelSelector = document.getElementById('model-selector');
        modelSelector.classList.toggle('open');
        // Open sidebar if collapsed
        if (!Sidebar.isOpen) {
            Sidebar.toggle();
        }
    });

    // Search toggle — enables/disables automatic web search
    const searchBtn = document.getElementById('input-toggle-search');
    searchBtn.addEventListener('click', () => {
        searchBtn.classList.toggle('active');

        // Also sync the topbar toggle if it exists
        const topbarToggle = document.getElementById('btn-web-search-toggle');
        if (topbarToggle) {
            if (searchBtn.classList.contains('active')) {
                topbarToggle.classList.add('active');
            } else {
                topbarToggle.classList.remove('active');
            }
        }

        const isActive = searchBtn.classList.contains('active');
        Settings._showToast(isActive ? '🔍 Web Search enabled — queries will search the web' : '🔍 Web Search disabled');
    });

    // Attach skill file from input area
    const attachBtn = document.getElementById('btn-attach-skill');
    if (attachBtn) {
        attachBtn.addEventListener('click', () => {
            Sidebar._fileInput.click();
        });
    }
}

function _updateProviderLabel(tier) {
    const label = document.getElementById('input-provider-label');
    const icon = document.getElementById('input-toggle-provider').querySelector('.input-toggle-icon');
    if (tier === 'cloud') {
        label.textContent = 'Cloud';
        icon.textContent = '☁️';
    } else {
        label.textContent = 'Local';
        icon.textContent = '💻';
    }
}
