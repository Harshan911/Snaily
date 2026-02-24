/**
 * App — Main entry point. Initialize all modules.
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize modules
    Chat.init();
    Sidebar.init();
    Settings.init();

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
    } else {
        statusEl.textContent = 'Backend Offline';
        statusEl.style.color = 'var(--danger)';
        console.warn('🐉 Blue Dragon AI Hub — Backend not reachable');
        console.warn('   Start the backend: cd backend && python main.py');
    }
});
