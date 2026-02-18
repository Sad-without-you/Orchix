// ORCHIX v1.3 - Shared Utilities

let currentUser = null;

// Global event delegation for CSP compliance (no inline handlers)
document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-action]');
    if (!el) return;
    const action = el.dataset.action;
    const fn = window[action];
    if (typeof fn !== 'function') return;
    const p = [el.dataset.p1, el.dataset.p2, el.dataset.p3, el.dataset.p4].filter(v => v !== undefined);
    if (action === 'toggleActionMenu') { fn(el); }
    else if (p.length > 0) { fn(...p); }
    else { fn(); }
});
document.addEventListener('input', (e) => {
    const el = e.target.closest('[data-oninput]');
    if (!el) return;
    const fn = window[el.dataset.oninput];
    if (typeof fn === 'function') fn();
});
document.addEventListener('change', (e) => {
    const el = e.target.closest('[data-onchange]');
    if (!el) return;
    const fn = window[el.dataset.onchange];
    if (typeof fn === 'function') fn();
});

// HTML escape - used globally by all pages
function esc(str) {
    if (str === null || str === undefined || str === '') return '-';
    const d = document.createElement('div');
    d.textContent = String(str);
    return d.innerHTML;
}

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

const API = {
    async get(url) {
        const res = await fetch(url);
        if (res.status === 401) { window.location.href = '/login'; return null; }
        if (res.status === 403) { showToast('error', 'Permission denied'); return null; }
        return res.json();
    },

    async post(url, data = {}) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify(data)
        });
        if (res.status === 401) { window.location.href = '/login'; return null; }
        if (res.status === 403) { showToast('error', 'Permission denied'); return null; }
        return res.json();
    },

    async put(url, data = {}) {
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify(data)
        });
        if (res.status === 401) { window.location.href = '/login'; return null; }
        if (res.status === 403) { showToast('error', 'Permission denied'); return null; }
        return res.json();
    },

    async delete(url) {
        const res = await fetch(url, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCsrfToken() }
        });
        if (res.status === 401) { window.location.href = '/login'; return null; }
        if (res.status === 403) { showToast('error', 'Permission denied'); return null; }
        return res.json();
    }
};

function hasPermission(perm) {
    if (!currentUser) return false;
    return currentUser.permissions.includes(perm);
}

async function loadUserInfo() {
    currentUser = await API.get('/api/auth/me');
    if (!currentUser) return;

    const nameEl = document.getElementById('sidebar-username');
    if (nameEl) nameEl.textContent = currentUser.username;

    const roleEl = document.getElementById('sidebar-role');
    if (roleEl) roleEl.textContent = currentUser.role;

    // Show Users nav only for admin
    const usersNav = document.getElementById('nav-users');
    if (usersNav) usersNav.style.display = currentUser.role === 'admin' ? '' : 'none';
}

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

// Track active install/import flow for cancel protection
window._installFlow = null; // { containerName: 'xxx' } when install is in progress
window._importFlow = null; // true when import is in progress

function showModal(title, bodyHtml, actions) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal-content');
    modal.innerHTML = `
        <div class="modal-header">
            <h2>${esc(title)}</h2>
            <button class="modal-close" data-action="_tryDismissModal">
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
        if (a.action) {
            btn.onclick = a.action;
        } else {
            btn.onclick = () => { hideModal(); if (a.fn) a.fn(); };
        }
        actionsEl.appendChild(btn);
    });
    overlay.classList.remove('hidden');
}

function hideModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
    document.getElementById('modal-content').classList.remove('wide');
}

function closeModal() { hideModal(); }

function _tryDismissModal() {
    // Don't allow dismissing progress modals (install/uninstall/import/export in progress)
    const overlay = document.getElementById('modal-overlay');
    if (overlay.dataset.progressModal === 'true') {
        return;
    }

    if (window._installFlow) {
        _showCancelInstallConfirm();
    } else if (window._importFlow) {
        // Import in progress - prevent dismissal
        showToast('info', 'Import in progress - please wait');
    } else if (window._exportFlow) {
        // Export in progress - prevent dismissal
        showToast('info', 'Export in progress - please wait');
    } else {
        hideModal();
    }
}

function _showCancelInstallConfirm() {
    const flow = window._installFlow;
    if (!flow) { hideModal(); return; }

    const modal = document.getElementById('modal-content');
    modal.innerHTML = `
        <div class="modal-header"><h2>Cancel Installation?</h2></div>
        <div class="modal-body">
            <p>The container <strong>${esc(flow.containerName)}</strong> has already been installed.</p>
            <p style="color:var(--text2);margin-top:8px">If you cancel now, the container and its data will be removed.</p>
        </div>
        <div class="modal-actions">
            <button class="btn" id="cancel-install-back">Back</button>
            <button class="btn btn-danger" id="cancel-install-confirm">Remove & Cancel</button>
        </div>
    `;
    document.getElementById('cancel-install-back').onclick = () => {
        // Re-show the previous modal content by triggering the flow's restore function
        if (flow.restore) flow.restore();
    };
    document.getElementById('cancel-install-confirm').onclick = async () => {
        hideModal();
        showProgressModal('Removing ' + flow.containerName, 'Cleaning up...');
        await API.post('/api/containers/' + encodeURIComponent(flow.containerName) + '/uninstall', {});
        hideProgressModal();
        window._installFlow = null;
        showToast('info', flow.containerName + ' removed');
        if (typeof Router !== 'undefined') Router.navigate('#/apps');
    };
}

// Close modal on overlay click
document.getElementById('modal-overlay').addEventListener('click', function(e) {
    if (e.target === this) _tryDismissModal();
});

// Progress modal for long operations (install, uninstall, update)
function showProgressModal(title, statusText) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal-content');
    modal.innerHTML = `
        <div class="modal-body" style="text-align:center;padding:40px 24px">
            <div class="spinner" style="margin:0 auto 16px"></div>
            <h3 style="margin-bottom:8px">${esc(title)}</h3>
            <p id="progress-status" style="color:var(--text2);font-size:0.9rem">${esc(statusText) || 'Please wait...'}</p>
            <div class="progress-bar-container">
                <div class="progress-bar-indeterminate"></div>
            </div>
        </div>
    `;
    overlay.classList.remove('hidden');
    overlay.dataset.progressModal = 'true'; // Mark as non-dismissible progress modal
}

function hideProgressModal() {
    const overlay = document.getElementById('modal-overlay');
    overlay.classList.add('hidden');
    delete overlay.dataset.progressModal;
}

// Progress modal with actual progress bar (for install with streaming)
function showProgressModalWithBar(title, statusText, progress) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal-content');
    modal.innerHTML = `
        <div class="modal-body" style="text-align:center;padding:40px 24px">
            <h3 style="margin-bottom:16px">${esc(title)}</h3>
            <div style="width:100%;background:var(--surface2);border-radius:12px;height:8px;overflow:hidden;margin-bottom:12px">
                <div id="progress-bar-fill" style="height:100%;background:linear-gradient(90deg,var(--pink),var(--teal));width:${progress}%;transition:width 0.3s ease"></div>
            </div>
            <p id="progress-status" style="color:var(--text2);font-size:0.9rem">${esc(statusText) || 'Please wait...'}</p>
            <p id="progress-percent" style="color:var(--text3);font-size:0.8rem;margin-top:4px">${progress}%</p>
        </div>
    `;
    overlay.classList.remove('hidden');
    overlay.dataset.progressModal = 'true';
}

function updateProgressBar(progress, status) {
    const fill = document.getElementById('progress-bar-fill');
    const statusEl = document.getElementById('progress-status');
    const percentEl = document.getElementById('progress-percent');
    if (fill) fill.style.width = progress + '%';
    if (statusEl && status) statusEl.textContent = status;
    if (percentEl) percentEl.textContent = progress + '%';
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
    const supportLink = document.getElementById('quick-link-support');
    const quickLinksGrid = document.getElementById('quick-links-grid');

    if (licenseInfo.is_pro) {
        badge.textContent = 'PRO';
        badge.className = 'license-badge pro';
        document.querySelectorAll('.pro-feature').forEach(el => el.classList.add('unlocked'));
        if (supportLink) {
            supportLink.style.display = 'flex';
            if (quickLinksGrid) quickLinksGrid.style.gridTemplateColumns = 'repeat(3,1fr)';
        }
    } else {
        badge.textContent = 'FREE';
        badge.className = 'license-badge';
        document.querySelectorAll('.pro-feature').forEach(el => el.classList.remove('unlocked'));
        if (supportLink) {
            supportLink.style.display = 'none';
            if (quickLinksGrid) quickLinksGrid.style.gridTemplateColumns = 'repeat(2,1fr)';
        }
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

// Container selection for FREE tier downgrade
async function checkContainerSelection() {
    const res = await API.get('/api/containers/selection-needed');
    if (res && res.needed) {
        showContainerSelectionModal(res.limit);
    }
}

async function showContainerSelectionModal(limit) {
    const res = await API.get('/api/containers/all-for-selection');
    if (!res || !res.containers || !res.containers.length) return;

    const containers = res.containers;
    let bodyHtml = `
        <p style="margin-bottom:12px">Your FREE tier allows managing <strong>${limit}</strong> containers.
        You have <strong>${containers.length}</strong> containers.</p>
        <p style="margin-bottom:16px;color:var(--text3);font-size:0.85rem">
            Select which containers to manage in ORCHIX. Unselected containers stay running on your server but won't be shown.</p>
        <div id="container-selection-list" style="max-height:300px;overflow-y:auto">
    `;

    for (const c of containers) {
        const statusCls = c.status === 'running' ? 'running' : 'stopped';
        bodyHtml += `
            <label class="hover-surface" style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:var(--radius-sm);cursor:pointer;border:1px solid var(--border);margin-bottom:6px;transition:background 0.15s">
                <input type="checkbox" class="container-select-cb" value="${esc(c.name)}" style="width:16px;height:16px;accent-color:var(--pink)">
                <span style="flex:1;font-weight:500">${esc(c.name)}</span>
                <span class="status-badge ${statusCls}" style="font-size:0.75rem">${esc(c.status)}</span>
            </label>
        `;
    }

    bodyHtml += `</div>
        <p id="selection-count" style="margin-top:10px;font-size:0.85rem;color:var(--text3)">Selected: 0 / ${limit}</p>
        <p id="selection-error" style="color:var(--red);font-size:0.85rem;display:none;margin-top:4px"></p>
    `;

    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal-content');
    modal.innerHTML = `
        <div class="modal-header">
            <h2>Select Containers to Manage</h2>
        </div>
        <div class="modal-body">${bodyHtml}</div>
        <div class="modal-actions">
            <button class="btn btn-primary" id="confirm-selection-btn" data-action="confirmContainerSelection" data-p1="${limit}">Confirm Selection</button>
        </div>
    `;
    overlay.classList.remove('hidden');

    // Prevent closing by clicking overlay
    const preventClose = (e) => {
        if (e.target === overlay) e.stopImmediatePropagation();
    };
    overlay.addEventListener('click', preventClose, true);

    // Update counter on checkbox change
    modal.addEventListener('change', () => {
        const checked = modal.querySelectorAll('.container-select-cb:checked').length;
        const countEl = document.getElementById('selection-count');
        if (countEl) countEl.textContent = `Selected: ${checked} / ${limit}`;

        // Disable unchecked if at limit
        const cbs = modal.querySelectorAll('.container-select-cb');
        cbs.forEach(cb => {
            if (!cb.checked) cb.disabled = checked >= limit;
        });
    });

    // Store cleanup function
    modal._selectionCleanup = () => {
        overlay.removeEventListener('click', preventClose, true);
    };
}

async function confirmContainerSelection(limit) {
    limit = parseInt(limit);
    const cbs = document.querySelectorAll('.container-select-cb:checked');
    const selected = Array.from(cbs).map(cb => cb.value);

    const errorEl = document.getElementById('selection-error');
    if (selected.length === 0) {
        if (errorEl) { errorEl.textContent = 'Please select at least one container.'; errorEl.style.display = ''; }
        return;
    }
    if (selected.length > limit) {
        if (errorEl) { errorEl.textContent = `Maximum ${limit} containers allowed.`; errorEl.style.display = ''; }
        return;
    }

    const res = await API.post('/api/containers/select', { selected });
    if (res && res.success) {
        // Cleanup prevent-close handler
        const modal = document.getElementById('modal-content');
        if (modal._selectionCleanup) modal._selectionCleanup();
        hideModal();
        showToast('success', res.message);
        // Reload current page
        if (typeof Router !== 'undefined') Router.navigate();
    } else {
        if (errorEl) { errorEl.textContent = (res && res.message) || 'Failed to save selection'; errorEl.style.display = ''; }
    }
}

// Load user info and license on startup
loadUserInfo();
loadLicenseInfo().then(() => checkContainerSelection());
checkForUpdates();

// ORCHIX Update Functions
async function updateOrchixNow() {
    showModal(
        'Update ORCHIX?',
        `
            <p>This will update ORCHIX to the latest version.</p>
            <p style="margin-top:12px;color:var(--text3);font-size:0.9rem">
                <strong>Steps:</strong> <code>git pull</code> + <code>pip install --upgrade</code>
            </p>
            <p style="margin-top:8px;padding:10px;background:var(--surface2);border-radius:var(--radius-sm);color:var(--yellow);font-size:0.85rem">
                <strong>⚠ Note:</strong> ORCHIX must be restarted after update.
            </p>
        `,
        [
            { label: 'Cancel', cls: 'btn-secondary' },
            { label: 'Update Now', cls: 'btn-primary', fn: doUpdateOrchix }
        ]
    );
}

async function doUpdateOrchix() {
    showProgressModal('Updating ORCHIX', 'Running git pull and pip install...');

    const res = await API.post('/api/system/update');
    hideProgressModal();

    if (res && res.success) {
        if (res.requires_restart) {
            showModal(
                'Update Complete',
                `
                    <div style="text-align:center">
                        <div style="width:48px;height:48px;margin:0 auto 16px;border-radius:50%;background:linear-gradient(135deg,rgba(34,197,94,0.2),rgba(34,197,94,0.1));display:flex;align-items:center;justify-content:center">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                        </div>
                        <h3 style="margin-bottom:8px">Update Successful</h3>
                        <p style="color:var(--text2);margin-bottom:16px">${esc(res.message)}</p>
                        <div style="background:var(--surface2);padding:12px;border-radius:var(--radius-sm);border-left:3px solid var(--yellow)">
                            <p style="color:var(--yellow);font-weight:600;margin:0 0 4px">
                                ⚠ Restart Required
                            </p>
                            <p style="font-size:0.85rem;color:var(--text3);margin:0">
                                Please restart ORCHIX to apply the update.<br>
                                The page will reload in 3 seconds.
                            </p>
                        </div>
                    </div>
                `,
                [{ label: 'OK', cls: 'btn-primary' }]
            );
            setTimeout(() => location.reload(), 3000);
        } else {
            showToast('info', res.message);
        }
    } else {
        showToast('error', (res && res.message) || 'Update failed');
    }
}
