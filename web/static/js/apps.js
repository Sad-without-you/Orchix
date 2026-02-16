// ORCHIX v1.2 - Applications Page

Router.register('#/apps', async function(el) {
    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">Management / <span class="current">Applications</span></div>
                <h1>Applications</h1>
            </div>
        </div>
        <div class="table-toolbar" style="margin-bottom:16px">
            <input class="search-input" id="apps-search" placeholder="Search applications..." data-oninput="filterApps">
        </div>
        <div id="apps-grid"><div class="loading"><span class="spinner"></span> Loading applications...</div></div>
    `;

    const apps = await API.get('/api/apps');
    const grid = document.getElementById('apps-grid');
    if (!apps || !grid) return;

    grid.className = 'app-grid';
    grid.innerHTML = apps.map(app => `
        <div class="app-card ${app.can_install ? 'installable' : 'locked'}" data-app-name="${esc(app.display_name).toLowerCase()}" data-app-desc="${esc(app.description).toLowerCase()}" data-tooltip="${esc(app.description)}">
            <div class="app-card-header">
                <span class="app-icon">${(typeof APP_ICONS !== 'undefined' && APP_ICONS[app.name]) ? APP_ICONS[app.name] : (app.icon || '')}</span>
                <div>
                    <div class="app-name">${esc(app.display_name)}</div>
                    <div class="app-version">v${esc(app.version)}${app.image_size_mb ? ` · ~${app.image_size_mb >= 1000 ? (app.image_size_mb / 1024).toFixed(1) + ' GB' : app.image_size_mb + ' MB'}` : ''}</div>
                </div>
            </div>
            <div class="app-desc">${esc(app.description)}</div>
            <div class="app-card-footer">
                ${hasPermission('apps.install') ? (app.can_install
                    ? `<button class="btn btn-primary" data-action="openInstallDialog" data-p1="${esc(app.name)}" data-p2="${esc(app.display_name)}" data-p3="${(app.default_ports||[]).join(',')}" data-p4="${app.image_size_mb || 0}">Install</button>`
                    : `<span class="pro-badge">PRO</span><button class="btn" disabled style="opacity:0.5">Install</button>`
                ) : `<button class="btn" disabled style="opacity:0.4">Install</button>`}
            </div>
        </div>
    `).join('');
});

function filterApps() {
    const q = (document.getElementById('apps-search')?.value || '').toLowerCase();
    document.querySelectorAll('.app-card').forEach(card => {
        const name = card.getAttribute('data-app-name') || '';
        const desc = card.getAttribute('data-app-desc') || '';
        card.style.display = (!q || name.includes(q) || desc.includes(q)) ? '' : 'none';
    });
}

async function openInstallDialog(appName, displayName, defaultPorts, imageSizeMb) {
    // Parse data-attribute strings
    if (typeof defaultPorts === 'string') {
        defaultPorts = defaultPorts ? defaultPorts.split(',').map(Number) : [];
    }
    imageSizeMb = parseInt(imageSizeMb) || 0;

    const defaultPort = (defaultPorts && defaultPorts.length > 0) ? defaultPorts[0] : 5678;
    const isFree = licenseInfo && !licenseInfo.is_pro;
    const sizeLabel = imageSizeMb ? (imageSizeMb >= 1000 ? (imageSizeMb / 1024).toFixed(1) + ' GB' : imageSizeMb + ' MB') : '';

    // Fetch config schema for template apps
    const schema = await API.get(`/api/apps/${appName}/config-schema`);
    const fields = (schema && schema.fields) || [];

    let fieldsHtml = '';
    for (const f of fields) {
        if (f.generate) {
            fieldsHtml += `
                <div class="form-group">
                    <label>${esc(f.label)}</label>
                    <input type="text" class="form-input" value="(auto-generated)" disabled
                        style="color:var(--text3);font-style:italic">
                </div>`;
        } else if (f.type === 'select' && f.options && f.options.length > 0) {
            fieldsHtml += `
                <div class="form-group">
                    <label>${esc(f.label)}</label>
                    <select class="form-input" id="cfg-${f.key}">
                        ${f.options.map(o => `<option value="${esc(o)}" ${o === f.default ? 'selected' : ''}>${esc(o)}</option>`).join('')}
                    </select>
                </div>`;
        } else {
            fieldsHtml += `
                <div class="form-group">
                    <label>${esc(f.label)}${f.required ? ' *' : ''}</label>
                    <input type="${f.type === 'password' ? 'password' : f.type === 'number' ? 'number' : 'text'}"
                        class="form-input" id="cfg-${f.key}"
                        value="${esc(f.default || '')}" placeholder="${esc(f.default || '')}">
                </div>`;
        }
    }

    showModal('Install ' + displayName, `
        ${sizeLabel ? `<div style="font-size:0.8rem;color:var(--text3);margin-bottom:0.8rem">Download: ~<strong style="color:var(--text2)">${sizeLabel}</strong> <span style="opacity:0.6">(compressed)</span></div>` : ''}
        <div class="form-group">
            <label>Instance Name</label>
            <input type="text" class="form-input" id="install-instance" value="${appName}"
                ${isFree ? 'disabled title="Multi-Instance requires PRO"' : `placeholder="e.g. ${appName}-prod"`}
                data-oninput="checkInstallConflicts">
            ${isFree ? '<div style="font-size:0.75rem;color:var(--text3);margin-top:0.3rem">Multi-Instance requires PRO license</div>' : ''}
            <div id="name-conflict-warn" class="conflict-warning" style="display:none"></div>
        </div>
        <div class="form-group">
            <label>Port</label>
            <input type="number" class="form-input" id="install-port" value="${defaultPort}" placeholder="${defaultPort}"
                data-oninput="checkInstallConflicts">
            <div id="port-conflict-warn" class="conflict-warning" style="display:none"></div>
        </div>
        ${fieldsHtml}
    `, [
        { label: 'Cancel', cls: '' },
        { label: 'Install', cls: 'btn-primary', fn: () => doInstall(appName, fields) }
    ]);
    checkInstallConflicts();
}

let _conflictTimer = null;
function checkInstallConflicts() {
    clearTimeout(_conflictTimer);
    _conflictTimer = setTimeout(async () => {
        const name = (document.getElementById('install-instance')?.value || '').trim();
        const port = (document.getElementById('install-port')?.value || '').trim();
        if (!name && !port) return;

        const params = new URLSearchParams();
        if (name) params.set('name', name);
        if (port) params.set('port', port);

        const res = await API.get('/api/apps/check-conflicts?' + params.toString());
        if (!res) return;

        const nameWarn = document.getElementById('name-conflict-warn');
        const portWarn = document.getElementById('port-conflict-warn');
        let hasConflict = false;

        if (nameWarn) {
            if (res.name_conflict) {
                nameWarn.textContent = `Container "${name}" already exists`;
                nameWarn.style.display = 'block';
                hasConflict = true;
            } else {
                nameWarn.style.display = 'none';
            }
        }
        if (portWarn) {
            if (res.port_conflict) {
                portWarn.textContent = `Port ${port} is already in use`;
                portWarn.style.display = 'block';
                hasConflict = true;
            } else {
                portWarn.style.display = 'none';
            }
        }

        // Disable Install button when conflicts exist
        const installBtn = document.querySelector('.modal-actions .btn-primary');
        if (installBtn) {
            installBtn.disabled = hasConflict;
            installBtn.style.opacity = hasConflict ? '0.4' : '';
            installBtn.style.pointerEvents = hasConflict ? 'none' : '';
        }
    }, 400);
}

async function doInstall(appName, fields) {
    const instanceName = document.getElementById('install-instance')?.value || appName;
    const port = parseInt(document.getElementById('install-port')?.value) || 5678;

    // Collect config from dynamic fields
    const config = { port: port };
    if (fields && fields.length > 0) {
        for (const f of fields) {
            if (f.generate) continue;
            const el = document.getElementById('cfg-' + f.key);
            if (el) config[f.key] = el.value;
        }
    }

    // Track install flow BEFORE showing progress modal
    window._installFlow = { containerName: instanceName };

    showProgressModalWithBar(`Installing ${instanceName}`, 'Initializing...', 0);

    // Use EventSource for SSE progress streaming
    const eventSource = new EventSource(
        '/api/apps/install-stream?' + new URLSearchParams({
            app_name: appName,
            instance_name: instanceName,
            config: JSON.stringify(config)
        })
    );

    // Note: EventSource doesn't support POST, so we need to use fetch with ReadableStream instead
    eventSource.close();

    // Use fetch with streaming instead
    try {
        const response = await fetch('/api/apps/install-stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('orchix-session-token')}`
            },
            body: JSON.stringify({
                app_name: appName,
                instance_name: instanceName,
                config: config
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let finalResult = null;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));

                    if (data.error) {
                        hideProgressModal();
                        window._installFlow = null;
                        showToast('error', data.error);
                        return;
                    }

                    if (data.progress !== undefined) {
                        updateProgressBar(data.progress, data.status || '');
                    }

                    if (data.success) {
                        finalResult = data;
                    }
                }
            }
        }

        hideProgressModal();

        if (finalResult && finalResult.success) {
            if (finalResult.post_install_action && finalResult.post_install_action.type === 'set_password') {
                _showSetPasswordDialog(finalResult.post_install_action, finalResult.access_info, instanceName);
            } else if (finalResult.access_info) {
                _showAccessInfo(instanceName, finalResult.access_info);
            } else {
                window._installFlow = null;
                showToast('success', finalResult.message);
            }
        } else {
            window._installFlow = null;
            showToast('error', 'Installation failed');
        }
    } catch (err) {
        hideProgressModal();
        window._installFlow = null;
        showToast('error', 'Installation failed: ' + err.message);
    }
}

function _showSetPasswordDialog(action, accessInfo, instanceName) {
    const showDialog = () => {
        let html = `<p style="color:var(--green);font-weight:600;margin-bottom:12px">Installed successfully</p>`;
        html += `<div class="form-group"><label>${esc(action.prompt)} <span style="color:var(--pink)">*</span></label>`;
        html += `<input type="password" id="post-install-pw" class="form-input" placeholder="Enter password..." autofocus required></div>`;
        html += `<p id="pw-error" style="font-size:12px;color:var(--red);display:none">Password is required!</p>`;

        showModal(instanceName + ' Ready', html, [
            { label: 'Set Password', cls: 'btn-primary', action: async () => {
                const pw = document.getElementById('post-install-pw').value.trim();
                if (!pw) {
                    document.getElementById('pw-error').style.display = 'block';
                    document.getElementById('post-install-pw').style.borderColor = 'var(--red)';
                    document.getElementById('post-install-pw').focus();
                    return;
                }
                const res = await API.post('/api/apps/set-password', {
                    container_name: action.container_name,
                    password: pw
                });
                closeModal();
                window._installFlow = null;
                if (res && res.success) {
                    showToast('success', 'Password set successfully');
                } else {
                    showToast('error', (res && res.message) || 'Failed to set password');
                }
                if (accessInfo) _showAccessInfo(instanceName, accessInfo);
            }}
        ]);
    };

    // Set restore callback for "Back" button in cancel confirm
    window._installFlow = { containerName: instanceName, restore: showDialog };
    showDialog();
}

function _showAccessInfo(name, info) {
    // Set restore callback if still in install flow
    if (window._installFlow) {
        window._installFlow.restore = () => _showAccessInfo(name, info);
    }
    let html = `<p style="color:var(--green);font-weight:600;margin-bottom:12px">Installed successfully</p>`;

    if (info.type === 'web' && info.url) {
        html += `<div class="form-group"><label>Access URL</label><div style="font-family:monospace;background:var(--surface2);padding:8px 12px;border-radius:var(--radius-sm);user-select:all">${esc(info.url)}</div></div>`;
    } else if (info.type === 'cli' && info.command) {
        html += `<div class="form-group"><label>CLI Command</label><div style="font-family:monospace;background:var(--surface2);padding:8px 12px;border-radius:var(--radius-sm);user-select:all;word-break:break-all">${esc(info.command)}</div></div>`;
        if (info.host) html += `<div class="form-group"><label>Host</label><div style="font-family:monospace;background:var(--surface2);padding:8px 12px;border-radius:var(--radius-sm)">${esc(info.host)}</div></div>`;
    } else if (info.type === 'none' && info.note) {
        html += `<p style="color:var(--text2)">${esc(info.note)}</p>`;
    }

    if (info.credentials && info.credentials.length > 0) {
        html += `<div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">`;
        html += `<label style="font-size:10px;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:8px;display:block">Credentials</label>`;
        for (const c of info.credentials) {
            html += `<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.9rem"><span style="color:var(--text2)">${esc(c.label)}</span><span style="font-family:monospace;user-select:all;color:var(--pink)">${esc(c.value)}</span></div>`;
        }
        html += `</div>`;
    }

    if (info.setup_hint) {
        html += `<div style="margin-top:12px;padding:12px;background:rgba(236,72,153,0.08);border:1px solid rgba(236,72,153,0.2);border-radius:var(--radius-sm)">`;
        html += `<div style="font-size:11px;font-weight:700;color:var(--pink);margin-bottom:6px">${esc(info.setup_hint.title)}</div>`;
        html += `<div style="font-family:monospace;font-size:12px;user-select:all;word-break:break-all;color:var(--text)">${esc(info.setup_hint.command)}</div>`;
        html += `</div>`;
    }

    showModal(name + ' Ready', html, [{ label: 'OK', cls: 'btn-primary', fn: () => { window._installFlow = null; } }]);
}

// ============ Backups Page ============
Router.register('#/backups', async function(el) {
    if (licenseInfo && !licenseInfo.is_pro) {
        el.innerHTML = proRequiredPage('Backup & Restore', 'Operations');
        return;
    }

    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">Operations / <span class="current">Backups</span></div>
                <h1>Backups</h1>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" data-action="showCreateBackup">Create Backup</button>
            </div>
        </div>
        <div id="backups-list"><div class="loading"><span class="spinner"></span> Loading backups...</div></div>
    `;
    await loadBackups();
});

async function loadBackups() {
    const data = await API.get('/api/backups');
    const list = document.getElementById('backups-list');
    if (!data || !list) return;

    if (data.length === 0) {
        list.innerHTML = '<div class="empty-state"><h2>No backups found</h2><p>Create one to get started.</p></div>';
        return;
    }

    list.innerHTML = `
        <table class="data-table">
            <thead><tr><th>File</th><th>Container</th><th>Type</th><th>Timestamp</th><th>Size</th><th>Actions</th></tr></thead>
            <tbody>
                ${data.map(b => `
                    <tr>
                        <td style="font-size:0.85rem">${esc(b.filename)}</td>
                        <td><span style="color:var(--teal);font-weight:600">${esc(b.meta?.container || '-')}</span></td>
                        <td>${esc(b.meta?.type || '-')}</td>
                        <td>${esc(b.meta?.timestamp || '-')}</td>
                        <td>${formatBytes(b.size)}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn-sm btn-success" data-action="confirmRestore" data-p1="${esc(b.filename)}" data-p2="${esc(b.meta?.container || '')}">Restore</button>
                                <button class="btn-sm btn-danger" data-action="confirmDeleteBackup" data-p1="${esc(b.filename)}">Delete</button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function showCreateBackup() {
    const containers = await API.get('/api/containers');
    if (!containers) return;
    const running = containers.filter(c => c.status === 'running');

    if (running.length === 0) {
        showToast('error', 'No running containers to backup');
        return;
    }

    showModal('Create Backup', `
        <div class="form-group">
            <label>Select Container</label>
            <select class="form-input" id="backup-container">
                ${running.map(c => `<option value="${esc(c.name)}">${esc(c.name)}</option>`).join('')}
            </select>
        </div>
    `, [
        { label: 'Cancel', cls: '' },
        { label: 'Create Backup', cls: 'btn-primary', fn: doCreateBackup }
    ]);
}

async function doCreateBackup() {
    const name = document.getElementById('backup-container')?.value;
    if (!name) return;

    showToast('info', `Creating backup for ${name}...`);
    const res = await API.post('/api/backups/create', { container_name: name });
    if (res && res.success) {
        showToast('success', 'Backup created');
        window.location.hash = '#/backups';
        Router.navigate();
    } else {
        showToast('error', (res && res.message) || 'Backup failed');
    }
}

function confirmRestore(filename, container) {
    showModal('Restore Backup', `
        <p style="margin-bottom:0.8rem">Restore <strong>${esc(filename)}</strong> to container <strong>${esc(container)}</strong>?</p>
        <p style="color:var(--yellow);font-weight:500">This will overwrite current data in the container.</p>
    `, [
        { label: 'Cancel', cls: '' },
        { label: 'Restore', cls: 'btn-primary', fn: () => doRestore(filename) }
    ]);
}

async function doRestore(filename) {
    showToast('info', 'Restoring backup...');
    const res = await API.post('/api/backups/restore', { filename: filename });
    if (res && res.success) {
        showToast('success', res.message);
    } else {
        showToast('error', (res && res.message) || 'Restore failed');
    }
}

function confirmDeleteBackup(filename) {
    showModal('Delete Backup', `
        <p>Permanently delete <strong>${esc(filename)}</strong>?</p>
        <p style="color:var(--red);font-weight:500;margin-top:0.5rem">This cannot be undone.</p>
    `, [
        { label: 'Cancel', cls: '' },
        { label: 'Delete', cls: 'btn-danger', fn: () => doDeleteBackup(filename) }
    ]);
}

async function doDeleteBackup(filename) {
    const res = await API.post('/api/backups/delete', { filename: filename });
    if (res && res.success) {
        showToast('success', res.message);
        await loadBackups();
    } else {
        showToast('error', (res && res.message) || 'Delete failed');
    }
}

// ============ Migration Page ============
Router.register('#/migration', async function(el) {
    if (licenseInfo && !licenseInfo.is_pro) {
        el.innerHTML = proRequiredPage('Server Migration', 'Operations');
        return;
    }

    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">Operations / <span class="current">Migration</span></div>
                <h1>Server Migration</h1>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" data-action="showExportDialog">Export Package</button>
                <button class="btn" data-action="showImportDialog">Import Package</button>
            </div>
        </div>

        <div class="section-card" style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.05) 0%, rgba(20, 184, 166, 0.05) 100%)">
            <h3>How Server Migration Works</h3>
            <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:1.5rem;margin-top:1rem;align-items:center">
                <div style="padding:20px;background:linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(236, 72, 153, 0.05) 100%);border-radius:var(--radius-sm);border:1px solid rgba(236, 72, 153, 0.2)">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--pink)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="17 8 12 3 7 8"/>
                            <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                        <div>
                            <div style="font-weight:700;color:var(--pink);font-size:1rem;margin-bottom:2px">Export (Source Server)</div>
                            <div style="font-size:0.8rem;color:var(--text3)">Create migration package</div>
                        </div>
                    </div>
                    <ol style="margin:0;padding-left:1.3rem;color:var(--text2);line-height:2;font-size:0.88rem">
                        <li style="color:var(--text)"><strong>Select</strong> containers to export</li>
                        <li style="color:var(--text)"><strong>Choose</strong> target platform (Linux/Windows)</li>
                        <li style="color:var(--text)"><strong>Download</strong> migration package (.tar.gz)</li>
                        <li style="color:var(--text)"><strong>Transfer</strong> package to new server</li>
                    </ol>
                </div>

                <div style="text-align:center">
                    <div style="font-size:2rem;color:var(--text3)">→</div>
                </div>

                <div style="padding:20px;background:linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(20, 184, 166, 0.05) 100%);border-radius:var(--radius-sm);border:1px solid rgba(20, 184, 166, 0.2)">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="7 10 12 15 17 10"/>
                            <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                        <div>
                            <div style="font-weight:700;color:var(--teal);font-size:1rem;margin-bottom:2px">Import (Target Server)</div>
                            <div style="font-size:0.8rem;color:var(--text3)">Restore containers</div>
                        </div>
                    </div>
                    <ol style="margin:0;padding-left:1.3rem;color:var(--text2);line-height:2;font-size:0.88rem">
                        <li style="color:var(--text)"><strong>Place</strong> package in migrations/ folder</li>
                        <li style="color:var(--text)"><strong>Click</strong> Import Package button</li>
                        <li style="color:var(--text)"><strong>Select</strong> package from list</li>
                        <li style="color:var(--text)"><strong>Confirm</strong> - containers restored automatically</li>
                    </ol>
                </div>
            </div>
        </div>

        <div class="section-card" style="padding:8px 12px">
            <div style="display:flex;align-items:center;gap:10px">
                <button data-action="toggleMigrationInfo" data-p1="what-migrated" class="hover-surface" style="display:flex;align-items:center;gap:8px;background:transparent;border:none;color:var(--text);cursor:pointer;padding:6px 8px;border-radius:var(--radius-sm);transition:all 0.15s;flex:1;text-align:left">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--pink)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                    <span style="font-size:13px;font-weight:600">What Gets Migrated?</span>
                    <svg id="what-migrated-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2" style="margin-left:auto;transition:transform 0.2s">
                        <polyline points="6 9 12 15 18 9"/>
                    </svg>
                </button>
            </div>
            <div id="what-migrated-content" style="display:none;margin-top:8px;padding:12px;background:var(--surface2);border-radius:var(--radius-sm)">
                <ul style="margin:0;padding-left:1.2rem;color:var(--text2);line-height:2;font-size:0.88rem">
                    <li><strong>Container Images:</strong> All Docker images and layers</li>
                    <li><strong>Volumes & Data:</strong> Application data, databases, user files</li>
                    <li><strong>Configuration:</strong> Environment variables, port mappings</li>
                    <li><strong>Networks:</strong> Docker networks and connectivity settings</li>
                </ul>
            </div>
        </div>

        <div class="section-card" style="padding:8px 12px">
            <div style="display:flex;align-items:center;gap:10px">
                <button data-action="toggleMigrationInfo" data-p1="best-practices" class="hover-surface" style="display:flex;align-items:center;gap:8px;background:transparent;border:none;color:var(--text);cursor:pointer;padding:6px 8px;border-radius:var(--radius-sm);transition:all 0.15s;flex:1;text-align:left">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                    <span style="font-size:13px;font-weight:600">Best Practices</span>
                    <svg id="best-practices-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2" style="margin-left:auto;transition:transform 0.2s">
                        <polyline points="6 9 12 15 18 9"/>
                    </svg>
                </button>
            </div>
            <div id="best-practices-content" style="display:none;margin-top:8px;padding:12px;background:var(--surface2);border-radius:var(--radius-sm)">
                <ul style="margin:0;padding-left:1.2rem;color:var(--text2);line-height:2;font-size:0.88rem">
                    <li><strong>Backup First:</strong> Always create backups before migration</li>
                    <li><strong>Test Import:</strong> Verify package on test server if possible</li>
                    <li><strong>Check Compatibility:</strong> Match source/target platforms</li>
                    <li><strong>Network Security:</strong> Transfer packages over secure channels</li>
                </ul>
            </div>
        </div>

        <div class="section-card" style="padding:8px 12px">
            <div style="display:flex;align-items:center;gap:10px">
                <button data-action="toggleMigrationInfo" data-p1="important-notes" class="hover-surface" style="display:flex;align-items:center;gap:8px;background:transparent;border:none;color:var(--text);cursor:pointer;padding:6px 8px;border-radius:var(--radius-sm);transition:all 0.15s;flex:1;text-align:left">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--yellow)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                    <span style="font-size:13px;font-weight:600">Important Notes</span>
                    <svg id="important-notes-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2" style="margin-left:auto;transition:transform 0.2s">
                        <polyline points="6 9 12 15 18 9"/>
                    </svg>
                </button>
            </div>
            <div id="important-notes-content" style="display:none;margin-top:8px;padding:12px;background:var(--surface2);border-radius:var(--radius-sm)">
                <div style="display:grid;grid-template-columns:1fr;gap:12px">
                    <div style="padding:12px;background:rgba(236, 72, 153, 0.05);border-radius:var(--radius-sm);border-left:3px solid var(--pink)">
                        <div style="font-weight:600;color:var(--text);margin-bottom:4px;font-size:0.9rem">Cross-Platform Support</div>
                        <div style="color:var(--text2);font-size:0.85rem">Migration packages can be created for Linux or Windows targets. Choose the correct platform during export.</div>
                    </div>
                    <div style="padding:12px;background:rgba(20, 184, 166, 0.05);border-radius:var(--radius-sm);border-left:3px solid var(--teal)">
                        <div style="font-weight:600;color:var(--text);margin-bottom:4px;font-size:0.9rem">Package Storage</div>
                        <div style="color:var(--text2);font-size:0.85rem">Migration packages are stored in the <code>migrations/</code> folder. Keep packages secure as they contain full container data.</div>
                    </div>
                    <div style="padding:12px;background:rgba(236, 72, 153, 0.05);border-radius:var(--radius-sm);border-left:3px solid var(--pink)">
                        <div style="font-weight:600;color:var(--text);margin-bottom:4px;font-size:0.9rem">Downtime Consideration</div>
                        <div style="color:var(--text2);font-size:0.85rem">Stop containers before export to ensure data consistency. Plan migration during maintenance windows.</div>
                    </div>
                </div>
            </div>
        </div>

        <div id="migration-list"><div class="loading"><span class="spinner"></span> Loading packages...</div></div>
    `;

    const data = await API.get('/api/migrations');
    const list = document.getElementById('migration-list');
    if (!data || !list) return;

    if (data.length === 0) {
        list.innerHTML = '<div class="empty-state"><h2>No migration packages</h2><p>Export a package to get started.</p></div>';
        return;
    }

    list.innerHTML = `
        <div class="section-card">
            <h3>Migration Packages</h3>
            <table class="data-table">
                <thead><tr><th>Package</th><th>Containers</th><th>Source</th><th>Target</th><th>Size</th><th>Created</th></tr></thead>
                <tbody>
                    ${data.map(p => `
                        <tr>
                            <td><span style="font-family:'Consolas','SF Mono',monospace;font-size:0.85rem">${esc(p.filename)}</span></td>
                            <td>${p.containers}</td>
                            <td>${esc(p.source)}</td>
                            <td>${esc(p.target_platform)}</td>
                            <td style="font-family:'Consolas','SF Mono',monospace;font-size:0.85rem">${formatBytes(p.size)}</td>
                            <td>${esc(p.created)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
});

function toggleMigrationInfo(id) {
    const content = document.getElementById(`${id}-content`);
    const icon = document.getElementById(`${id}-icon`);
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        icon.style.transform = 'rotate(0deg)';
    }
}

async function showExportDialog() {
    const containers = await API.get('/api/migrations/containers');
    if (!containers || containers.length === 0) {
        showToast('error', 'No ORCHIX containers found to export');
        return;
    }

    const checkboxes = containers.map(c =>
        `<label style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0;font-size:0.9rem;cursor:pointer">
            <input type="checkbox" value="${esc(c)}" class="export-cb" checked> ${esc(c)}
        </label>`
    ).join('');

    showModal('Export Migration Package', `
        <div class="form-group">
            <label>Select Containers</label>
            <div style="max-height:200px;overflow-y:auto;padding:0.5rem;background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-sm)">
                ${checkboxes}
            </div>
        </div>
        <div class="form-group">
            <label>Target Platform</label>
            <select class="form-input" id="export-platform">
                <option value="linux">Linux (tar.gz backups)</option>
                <option value="windows">Windows (zip backups)</option>
            </select>
        </div>
    `, [
        { label: 'Cancel', cls: '' },
        { label: 'Export', cls: 'btn-primary', fn: doExport }
    ]);
}

async function doExport() {
    const checked = document.querySelectorAll('.export-cb:checked');
    const containers = Array.from(checked).map(cb => cb.value);
    const platform = document.getElementById('export-platform')?.value || 'linux';

    if (containers.length === 0) {
        showToast('error', 'No containers selected');
        return;
    }

    hideModal();
    showProgressModal('Exporting Migration Package', `Backing up ${containers.length} container(s)...`);
    const res = await API.post('/api/migrations/export', {
        containers: containers,
        target_platform: platform
    });
    hideProgressModal();
    if (res && res.success) {
        showToast('success', res.message);
        window.location.hash = '#/migration';
        Router.navigate();
    } else {
        showToast('error', (res && res.message) || 'Export failed');
    }
}

async function showImportDialog() {
    const packages = await API.get('/api/migrations');
    if (!packages || packages.length === 0) {
        showToast('error', 'No migration packages found. Place .tar.gz files in migrations/ directory.');
        return;
    }

    const options = packages.map(p =>
        `<option value="${esc(p.filename)}">${esc(p.filename)} (${p.containers} containers, ${formatBytes(p.size)})</option>`
    ).join('');

    showModal('Import Migration Package', `
        <div class="form-group">
            <label>Select Package</label>
            <select class="form-input" id="import-package">${options}</select>
        </div>
        <p style="color:var(--yellow);font-size:0.85rem">Existing containers with the same name will be skipped.</p>
    `, [
        { label: 'Cancel', cls: '' },
        { label: 'Import', cls: 'btn-primary', fn: doImport }
    ]);
}

async function doImport() {
    const filename = document.getElementById('import-package')?.value;
    if (!filename) return;

    hideModal();
    showProgressModal('Importing Migration Package', 'Restoring containers and volumes...');
    const res = await API.post('/api/migrations/import', { filename: filename });
    hideProgressModal();
    if (res && res.success) {
        showToast('success', res.message);
        window.location.hash = '#/migration';
        Router.navigate();
    } else {
        showToast('error', (res && res.message) || 'Import failed');
    }
}

// ============ Audit Logs Page ============
Router.register('#/audit', async function(el) {
    if (licenseInfo && !licenseInfo.is_pro) {
        el.innerHTML = proRequiredPage('Audit Logs', 'System');
        return;
    }

    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">System / <span class="current">Audit Logs</span></div>
                <h1>Audit Logs</h1>
            </div>
            <div class="header-actions">
                <button class="btn btn-danger" data-action="showClearAuditDialog">Clear Old Logs</button>
            </div>
        </div>
        <div class="section-card" style="margin-bottom:1rem;padding:12px 16px">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
                <label style="font-size:12px;color:var(--text2);font-weight:500">Event:</label>
                <select class="form-input" id="audit-filter" style="width:auto" data-onchange="loadAuditLogs">
                    <option value="">All Events</option>
                    <option value="INSTALL">Install</option>
                    <option value="UNINSTALL">Uninstall</option>
                    <option value="UPDATE">Update</option>
                    <option value="BACKUP">Backup</option>
                    <option value="RESTORE">Restore</option>
                    <option value="CONTAINER_START">Container Start</option>
                    <option value="CONTAINER_STOP">Container Stop</option>
                </select>
                <label style="font-size:12px;color:var(--text2);font-weight:500">User:</label>
                <select class="form-input" id="audit-user-filter" style="width:auto" data-onchange="loadAuditLogs">
                    <option value="">All Users</option>
                </select>
            </div>
        </div>
        <div id="audit-list"><div class="loading"><span class="spinner"></span> Loading...</div></div>
    `;

    // Load users for filter
    const users = await API.get('/api/audit/users');
    if (users && users.length > 0) {
        const sel = document.getElementById('audit-user-filter');
        users.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u;
            opt.textContent = u;
            sel.appendChild(opt);
        });
    }

    await loadAuditLogs();
});

async function loadAuditLogs() {
    const eventFilter = document.getElementById('audit-filter')?.value || '';
    const userFilter = document.getElementById('audit-user-filter')?.value || '';

    let url = '/api/audit?limit=200';
    if (eventFilter) url += `&event_type=${eventFilter}`;
    if (userFilter) url = `/api/audit/user-activity?user=${userFilter}&limit=200`;

    const data = await API.get(url);
    const list = document.getElementById('audit-list');
    if (!data || !list) return;

    if (data.length === 0) {
        list.innerHTML = '<div class="empty-state"><h2>No audit events</h2><p>Events will appear here as actions are performed.</p></div>';
        return;
    }

    list.innerHTML = `
        <table class="data-table">
            <thead><tr><th>Timestamp</th><th>Event</th><th>Application</th><th>User</th><th>Details</th></tr></thead>
            <tbody>
                ${data.map(e => `
                    <tr>
                        <td style="font-size:0.8rem">${esc(e.timestamp?.substring(0, 19) || '-')}</td>
                        <td><span style="color:var(--teal);font-weight:600">${esc(e.event_type)}</span></td>
                        <td>${esc(e.app_name)}</td>
                        <td>${esc(e.user)}</td>
                        <td style="font-size:0.8rem;color:var(--text3)">${esc(JSON.stringify(e.details || {}))}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function showClearAuditDialog() {
    showModal('Clear Old Logs', `
        <div class="form-group">
            <label>Keep logs from the last:</label>
            <select class="form-input" id="audit-retention">
                <option value="30">30 days</option>
                <option value="90" selected>90 days</option>
                <option value="180">180 days</option>
                <option value="365">1 year</option>
            </select>
        </div>
        <p style="color:var(--yellow);font-size:0.85rem">Older logs will be permanently deleted.</p>
    `, [
        { label: 'Cancel', cls: '' },
        { label: 'Clear', cls: 'btn-danger', fn: doClearAudit }
    ]);
}

async function doClearAudit() {
    const days = parseInt(document.getElementById('audit-retention')?.value) || 90;
    const res = await API.post('/api/audit/clear', { days: days });
    if (res && res.success) {
        showToast('success', res.message);
        await loadAuditLogs();
    } else {
        showToast('error', (res && res.message) || 'Clear failed');
    }
}

// ============ License Page ============
Router.register('#/license', async function(el) {
    const info = await API.get('/api/license');
    if (!info) return;

    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">System / <span class="current">License</span></div>
                <h1>License Management</h1>
            </div>
        </div>

        <div class="section-card" style="background: linear-gradient(135deg, ${info.is_pro ? 'rgba(234, 179, 8, 0.05)' : 'rgba(236, 72, 153, 0.05)'} 0%, rgba(20, 184, 166, 0.05) 100%)">
            <h3>License Overview</h3>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.5rem;margin-top:1rem">
                <div>
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:6px">Current Tier</div>
                    <div style="font-size:1.5rem;font-weight:700;background:linear-gradient(135deg,var(--pink) 0%,var(--teal) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">${esc(info.tier_display)}</div>
                </div>
                <div>
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:6px">Container Usage</div>
                    <div style="font-size:1.2rem;font-weight:700;color:var(--text)">${info.container_status.current} <span style="color:var(--text3);font-size:0.9rem">/ ${info.container_status.limit === 999 ? '∞' : info.container_status.limit}</span></div>
                    <div style="height:4px;background:var(--surface2);border-radius:2px;margin-top:6px;overflow:hidden">
                        <div style="height:100%;background:linear-gradient(90deg,var(--pink) 0%,var(--teal) 100%);width:${info.container_status.limit === 999 ? 20 : Math.min(100, (info.container_status.current / info.container_status.limit) * 100)}%;transition:width 0.3s"></div>
                    </div>
                </div>
                ${info.days_remaining !== null ? `
                    <div>
                        <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:6px">Expires In</div>
                        <div style="font-size:1.2rem;font-weight:700;color:${info.days_remaining < 30 ? 'var(--yellow)' : 'var(--text)'}">${info.days_remaining} <span style="color:var(--text3);font-size:0.9rem">days</span></div>
                    </div>
                ` : ''}
                <div>
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:6px">Features Enabled</div>
                    <div style="font-size:1.2rem;font-weight:700;color:var(--text)">${Object.entries(info.features).filter(([k,v]) => k === 'max_containers' ? (v === true || v >= 999) : k === 'max_users' ? (v === true || v > 1) : !!v).length} <span style="color:var(--text3);font-size:0.9rem">/ ${Object.keys(info.features).length}</span></div>
                </div>
            </div>
        </div>

        <div class="section-card">
            <h3>Feature Access</h3>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:0.75rem;margin-top:0.75rem">
                ${Object.entries(info.features).map(([k, v]) => {
                    const labels = {
                        max_containers: {
                            icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="7.5 4.21 12 6.81 16.5 4.21"/><polyline points="7.5 19.79 7.5 14.6 3 12"/><polyline points="21 12 16.5 14.6 16.5 19.79"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
                            label: (v === true || v >= 999) ? 'Unlimited Containers' : `Max ${v} Containers`,
                            desc: (v === true || v >= 999) ? 'No limit on number of containers you can run' : `Limited to ${v} containers (PRO: unlimited)`
                        },
                        max_users: {
                            icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
                            label: v > 1 ? `Multi-User (Max ${v})` : `${v} User`,
                            desc: v > 1 ? 'Role-based access control: Admin, Operator, Viewer' : 'Limited to single admin user (PRO: up to 3 with RBAC)'
                        },
                        backup_restore: {
                            icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
                            label: 'Backup & Restore',
                            desc: 'Create and restore container backups with versioning'
                        },
                        multi_instance: {
                            icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
                            label: 'Multi-Instance',
                            desc: 'Run multiple instances of the same app simultaneously'
                        },
                        migration: {
                            icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
                            label: 'Server Migration',
                            desc: 'Migrate containers between servers seamlessly'
                        },
                        audit_log: {
                            icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
                            label: 'Audit Logging',
                            desc: 'Track all system operations and changes'
                        }
                    };
                    const feature = labels[k] || { icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>', label: k.replace(/_/g, ' '), desc: '' };
                    const enabled = k === 'max_containers' ? (v === true || v >= 999) : k === 'max_users' ? (v === true || v > 1) : !!v;
                    return `
                        <div style="padding:14px;background:${enabled ? 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%)' : 'var(--surface2)'};border-radius:var(--radius-sm);border:1px solid ${enabled ? 'rgba(34, 197, 94, 0.2)' : 'var(--border)'}">
                            <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
                                <div style="color:${enabled ? 'var(--green)' : 'var(--text3)'}">${feature.icon}</div>
                                <span style="font-weight:700;font-size:0.92rem;color:${enabled ? 'var(--green)' : 'var(--text3)'}">${feature.label}</span>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${enabled ? 'var(--green)' : 'var(--text3)'}" stroke-width="2.5" style="margin-left:auto"><${enabled ? 'polyline points="20 6 9 17 4 12"' : 'line x1="18" y1="6" x2="6" y2="18"'}/>${ enabled ? '' : '<line x1="6" y1="6" x2="18" y2="18"/>'}</svg>
                            </div>
                            <div style="font-size:0.82rem;color:var(--text2);line-height:1.5">${feature.desc}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>

        ${!info.is_pro ? `
            <div class="section-card" style="background: linear-gradient(135deg, rgba(234, 179, 8, 0.08) 0%, rgba(234, 179, 8, 0.02) 100%); border:1px solid var(--yellow);padding:8px 10px">
                <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap">
                    <div style="flex:1;min-width:220px">
                        <h3 style="color:var(--yellow);margin-bottom:4px;display:flex;align-items:center;gap:6px;font-size:12px">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="var(--yellow)" stroke="none">
                                <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z"/>
                            </svg>
                            Upgrade to PRO
                        </h3>
                        <p style="font-size:0.82rem;color:var(--text2);margin:0;line-height:1.4">Unlock unlimited containers, backups, migrations, and priority support.</p>
                    </div>
                    <div style="display:flex;gap:8px;align-items:center">
                        <input type="text" class="form-input" id="license-key" placeholder="License key" style="width:200px;margin:0;font-size:12px;padding:6px 10px">
                        <button class="btn btn-primary" data-action="activateLicense" style="font-size:12px;padding:6px 14px">Activate</button>
                    </div>
                </div>
            </div>
        ` : `
            <div class="section-card" style="padding:8px 10px;max-width:620px">
                <h3 style="font-size:12px">License Actions</h3>
                <div style="display:flex;gap:10px;align-items:center;margin-top:6px">
                    <button class="btn btn-danger" data-action="deactivateLicense" style="font-size:12px;padding:6px 12px">Deactivate PRO</button>
                    <span style="font-size:0.8rem;color:var(--text3)">Reverts to FREE tier</span>
                </div>
            </div>
        `}

    `;
});

async function activateLicense() {
    const key = document.getElementById('license-key')?.value;
    if (!key) { showToast('error', 'Please enter a license key'); return; }

    const res = await API.post('/api/license/activate', { license_key: key });
    if (res && res.success) {
        showToast('success', 'PRO license activated!');
        await loadLicenseInfo();
        window.location.hash = '#/license';
        Router.navigate();
    } else {
        showToast('error', (res && res.message) || 'Activation failed');
    }
}

async function deactivateLicense() {
    showModal('Deactivate License', '<p>Are you sure you want to deactivate your PRO license?</p>', [
        { label: 'Cancel', cls: '' },
        { label: 'Deactivate', cls: 'btn-danger', fn: async () => {
            const res = await API.post('/api/license/deactivate');
            if (res && res.success) {
                showToast('success', 'License deactivated');
                await loadLicenseInfo();
                // Check if container selection is needed after downgrade
                if (res.selection_needed) {
                    await checkContainerSelection();
                } else {
                    Router.navigate();
                }
            }
        }}
    ]);
}

async function checkSystemUpdate() {
    // Clear cache to force fresh check
    localStorage.removeItem('orchix-update-check');
    showToast('info', 'Checking for updates...');
    const res = await API.get('/api/system/check-update');
    if (!res) return;
    localStorage.setItem('orchix-update-check', JSON.stringify({ ...res, ts: Date.now() }));

    const card = document.getElementById('update-info-card');
    if (res.update_available) {
        if (card) {
            card.innerHTML = `
                <h3>ORCHIX Update Available</h3>
                <p style="margin:0.5rem 0;color:var(--text2)">
                    Current: <strong>v${esc(res.current_version)}</strong> &rarr;
                    Latest: <strong style="color:var(--teal)">v${esc(res.latest_version)}</strong>
                </p>
                <p style="font-size:0.85rem;color:var(--text3)">Run <code style="background:var(--surface2);padding:2px 6px;border-radius:3px">git pull && pip install -r requirements.txt</code> to update.</p>
            `;
            card.style.display = '';
        }
        showUpdateBadge(res.latest_version);
        showToast('info', `Update available: v${res.latest_version}`);
    } else {
        if (card) {
            card.innerHTML = `
                <h3>ORCHIX Version</h3>
                <p style="margin:0.5rem 0;color:var(--text2)">
                    v${esc(res.current_version)} <span class="status-badge running">Up to date</span>
                </p>
            `;
            card.style.display = '';
        }
        showToast('success', 'ORCHIX is up to date');
    }
}

// ============ Users Page (Admin Only) ============
Router.register('#/users', async function(el) {
    if (!hasPermission('users.read')) {
        el.innerHTML = `
            <div class="page-header"><div>
                <div class="breadcrumb">System / <span class="current">Users</span></div>
                <h1>User Management</h1>
            </div></div>
            <div class="section-card" style="text-align:center;padding:3rem">
                <h3 style="color:var(--red)">Access Denied</h3>
                <p style="color:var(--text2);margin-top:0.5rem">Only administrators can manage users.</p>
            </div>`;
        return;
    }

    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">System / <span class="current">Users</span></div>
                <h1>User Management</h1>
            </div>
            <button class="btn btn-primary" data-action="showAddUserModal">Add User</button>
        </div>
        <div class="section-card">
            <div id="users-table"><div class="loading"><span class="spinner"></span> Loading...</div></div>
        </div>`;

    await loadUsersTable();
});

async function loadUsersTable() {
    const res = await API.get('/api/users');
    const container = document.getElementById('users-table');
    if (!res || !res.users || !container) return;

    const roleBadge = (role) => {
        const colors = { admin: 'var(--pink)', operator: 'var(--teal)', viewer: 'var(--text3)' };
        return `<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:0.75rem;font-weight:600;background:${colors[role] || 'var(--text3)'}20;color:${colors[role] || 'var(--text3)'};text-transform:uppercase">${esc(role)}</span>`;
    };

    const formatDate = (d) => d ? new Date(d).toLocaleString() : '-';

    container.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Role</th>
                    <th>Created</th>
                    <th>Last Login</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${res.users.map(u => `
                    <tr>
                        <td><strong>${esc(u.username)}</strong>${u.username === currentUser.username ? ' <span style="color:var(--teal);font-size:0.75rem">(you)</span>' : ''}</td>
                        <td>${roleBadge(u.role)}</td>
                        <td style="font-size:0.85rem;color:var(--text3)">${formatDate(u.created_at)}</td>
                        <td style="font-size:0.85rem;color:var(--text3)">${formatDate(u.last_login)}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn-sm" data-action="showEditUserModal" data-p1="${esc(u.username)}" data-p2="${esc(u.role)}">Edit</button>
                                ${u.username !== currentUser.username ? `<button class="btn-sm btn-danger" data-action="deleteUser" data-p1="${esc(u.username)}">Delete</button>` : ''}
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <div style="margin-top:12px;font-size:0.82rem;color:var(--text3)">${res.users.length} user${res.users.length !== 1 ? 's' : ''}</div>`;
}

function showAddUserModal() {
    showModal('Add User', `
        <div class="form-group" style="margin-bottom:12px">
            <label style="display:block;font-size:0.82rem;color:var(--text3);margin-bottom:4px">Username</label>
            <input type="text" id="new-username" placeholder="3-32 chars, lowercase" style="width:100%;padding:8px 10px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text);font-size:0.9rem">
        </div>
        <div class="form-group" style="margin-bottom:12px">
            <label style="display:block;font-size:0.82rem;color:var(--text3);margin-bottom:4px">Password</label>
            <input type="password" id="new-password" placeholder="Min 8 characters" style="width:100%;padding:8px 10px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text);font-size:0.9rem">
        </div>
        <div class="form-group" style="margin-bottom:12px">
            <label style="display:block;font-size:0.82rem;color:var(--text3);margin-bottom:4px">Role</label>
            <select id="new-role" style="width:100%;padding:8px 10px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text);font-size:0.9rem">
                <option value="viewer">Viewer - Read only</option>
                <option value="operator">Operator - Manage containers & apps</option>
                <option value="admin">Admin - Full access</option>
            </select>
        </div>
    `, [
        { label: 'Cancel', cls: 'btn-secondary' },
        { label: 'Create User', cls: 'btn-primary', fn: createUser }
    ]);
}

async function createUser() {
    const username = document.getElementById('new-username').value.trim().toLowerCase();
    const password = document.getElementById('new-password').value;
    const role = document.getElementById('new-role').value;

    const res = await API.post('/api/users', { username, password, role });
    hideModal();
    if (res && res.success) {
        showToast('success', res.message);
        await loadUsersTable();
    } else {
        showToast('error', (res && res.message) || 'Failed to create user');
    }
}

function showEditUserModal(username, currentRole) {
    showModal(`Edit User: ${username}`, `
        <div class="form-group" style="margin-bottom:12px">
            <label style="display:block;font-size:0.82rem;color:var(--text3);margin-bottom:4px">Role</label>
            <select id="edit-role" style="width:100%;padding:8px 10px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text);font-size:0.9rem">
                <option value="viewer" ${currentRole === 'viewer' ? 'selected' : ''}>Viewer - Read only</option>
                <option value="operator" ${currentRole === 'operator' ? 'selected' : ''}>Operator - Manage containers & apps</option>
                <option value="admin" ${currentRole === 'admin' ? 'selected' : ''}>Admin - Full access</option>
            </select>
        </div>
        <div class="form-group" style="margin-bottom:12px">
            <label style="display:block;font-size:0.82rem;color:var(--text3);margin-bottom:4px">New Password (leave empty to keep current)</label>
            <input type="password" id="edit-password" placeholder="Min 8 characters" style="width:100%;padding:8px 10px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text);font-size:0.9rem">
        </div>
    `, [
        { label: 'Cancel', cls: 'btn-secondary' },
        { label: 'Save Changes', cls: 'btn-primary', fn: async () => {
            const role = document.getElementById('edit-role').value;
            const password = document.getElementById('edit-password').value;
            const data = { role };
            if (password) data.password = password;
            const res = await API.put('/api/users/' + username, data);
            hideModal();
            if (res && res.success) {
                showToast('success', res.message);
                await loadUsersTable();
            } else {
                showToast('error', (res && res.message) || 'Failed to update user');
            }
        }}
    ]);
}

async function deleteUser(username) {
    showModal('Delete User', `<p>Are you sure you want to delete user <strong>${esc(username)}</strong>?</p><p style="margin-top:8px;color:var(--text3);font-size:0.85rem">This action cannot be undone.</p>`, [
        { label: 'Cancel', cls: 'btn-secondary' },
        { label: 'Delete', cls: 'btn-danger', fn: async () => {
            const res = await API.delete('/api/users/' + username);
            hideModal();
            if (res && res.success) {
                showToast('success', res.message);
                await loadUsersTable();
            } else {
                showToast('error', (res && res.message) || 'Failed to delete user');
            }
        }}
    ]);
}

// Helper: PRO required page
function proRequiredPage(feature, breadcrumbSection) {
    return `
        <div class="page-header">
            <div>
                <div class="breadcrumb">${breadcrumbSection || 'System'} / <span class="current">${feature}</span></div>
                <h1>${feature}</h1>
            </div>
        </div>
        <div class="section-card" style="text-align:center;padding:3rem;border-color:var(--yellow)">
            <div style="margin-bottom:1rem;color:var(--yellow)"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg></div>
            <h3 style="color:var(--yellow);font-size:1.2rem;margin-bottom:0.8rem">PRO Feature</h3>
            <p style="color:var(--text2);margin-bottom:1.5rem">
                ${feature} requires a PRO license. Upgrade to unlock this feature.
            </p>
            <a href="#/license" class="btn btn-primary">Upgrade to PRO</a>
        </div>
    `;
}
