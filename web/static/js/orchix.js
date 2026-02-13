// ORCHIX v1.2 - Shared Utilities

const API = {
    async get(url) {
        const res = await fetch(url);
        if (res.status === 401) { window.location.href = '/login'; return null; }
        return res.json();
    },

    async post(url, data = {}) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.status === 401) { window.location.href = '/login'; return null; }
        return res.json();
    }
};

function showToast(type, message) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showModal(title, bodyHtml, actions) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal-content');
    modal.innerHTML = `
        <div class="modal-header">
            <h2>${title}</h2>
            <button class="modal-close" onclick="hideModal()">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="4" y1="4" x2="12" y2="12"/>
                    <line x1="12" y1="4" x2="4" y2="12"/>
                </svg>
            </button>
        </div>
        <div class="modal-body">${bodyHtml}</div>
        <div class="modal-actions" id="modal-actions"></div>
    `;
    const actionsEl = document.getElementById('modal-actions');
    actions.forEach(a => {
        const btn = document.createElement('button');
        btn.className = `btn ${a.cls || ''}`;
        btn.textContent = a.label;
        btn.onclick = () => { hideModal(); if (a.fn) a.fn(); };
        actionsEl.appendChild(btn);
    });
    overlay.classList.remove('hidden');
}

function hideModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
    document.getElementById('modal-content').classList.remove('wide');
}

// Close modal on overlay click
document.getElementById('modal-overlay').addEventListener('click', function(e) {
    if (e.target === this) hideModal();
});

// Progress modal for long operations (install, uninstall, update)
function showProgressModal(title, statusText) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal-content');
    modal.innerHTML = `
        <div class="modal-body" style="text-align:center;padding:40px 24px">
            <div class="spinner" style="margin:0 auto 16px"></div>
            <h3 style="margin-bottom:8px">${title}</h3>
            <p id="progress-status" style="color:var(--text2);font-size:0.9rem">${statusText || 'Please wait...'}</p>
            <div class="progress-bar-container">
                <div class="progress-bar-indeterminate"></div>
            </div>
        </div>
    `;
    overlay.classList.remove('hidden');
}

function updateProgressStatus(text) {
    const el = document.getElementById('progress-status');
    if (el) el.textContent = text;
}

function hideProgressModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

function getCpuClass(val) {
    const num = parseFloat(val);
    if (isNaN(num)) return '';
    if (num >= 90) return 'cpu-critical';
    if (num >= 70) return 'cpu-warning';
    return 'cpu-normal';
}

function formatBytes(bytes) {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB';
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
    if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return bytes + ' B';
}

// License state (loaded once, refreshed on license page)
let licenseInfo = null;

async function loadLicenseInfo() {
    licenseInfo = await API.get('/api/license');
    if (!licenseInfo) return;
    const badge = document.getElementById('license-badge');
    if (licenseInfo.is_pro) {
        badge.textContent = 'PRO';
        badge.className = 'license-badge pro';
        document.querySelectorAll('.pro-feature').forEach(el => el.classList.add('unlocked'));
    } else {
        badge.textContent = 'FREE';
        badge.className = 'license-badge';
        document.querySelectorAll('.pro-feature').forEach(el => el.classList.remove('unlocked'));
    }
}

// Sidebar collapse/expand
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('sidebar-toggle');
    if (toggle) {
        if (localStorage.getItem('orchix-sidebar-collapsed') === 'true') {
            document.body.classList.add('sidebar-collapsed');
        }
        toggle.addEventListener('click', () => {
            document.body.classList.toggle('sidebar-collapsed');
            localStorage.setItem('orchix-sidebar-collapsed',
                document.body.classList.contains('sidebar-collapsed'));
        });
    }
});

// Close action menus when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.action-dropdown')) {
        document.querySelectorAll('.action-menu.open').forEach(m => m.classList.remove('open'));
    }
});

// Toggle action dropdown menu
function toggleActionMenu(btn) {
    const menu = btn.nextElementSibling;
    const wasOpen = menu.classList.contains('open');
    document.querySelectorAll('.action-menu.open').forEach(m => m.classList.remove('open'));
    if (!wasOpen) menu.classList.add('open');
}

// Update check with 24h localStorage cache
async function checkForUpdates() {
    const cacheKey = 'orchix-update-check';
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
        try {
            const data = JSON.parse(cached);
            if (Date.now() - data.ts < 86400000) {
                if (data.update_available) showUpdateBadge(data.latest_version);
                return;
            }
        } catch (e) {}
    }

    const res = await API.get('/api/system/check-update');
    if (!res) return;

    localStorage.setItem(cacheKey, JSON.stringify({ ...res, ts: Date.now() }));
    if (res.update_available) showUpdateBadge(res.latest_version);
}

function showUpdateBadge(version) {
    const badge = document.getElementById('update-badge');
    if (badge) {
        badge.textContent = 'v' + version;
        badge.style.display = '';
    }
}

// Load license on startup
loadLicenseInfo();
checkForUpdates();
