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
            <input class="search-input" id="apps-search" placeholder="Search applications..." oninput="filterApps()">
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
                ${app.can_install
                    ? `<button class="btn btn-primary" onclick="openInstallDialog('${esc(app.name)}', '${esc(app.display_name)}', ${JSON.stringify(app.default_ports)}, ${app.image_size_mb || 0})">Install</button>`
                    : `<span class="pro-badge">PRO</span><button class="btn" disabled style="opacity:0.5">Install</button>`
                }
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
                oninput="checkInstallConflicts()">
            ${isFree ? '<div style="font-size:0.75rem;color:var(--text3);margin-top:0.3rem">Multi-Instance requires PRO license</div>' : ''}
            <div id="name-conflict-warn" class="conflict-warning" style="display:none"></div>
        </div>
        <div class="form-group">
            <label>Port</label>
            <input type="number" class="form-input" id="install-port" value="${defaultPort}" placeholder="${defaultPort}"
                oninput="checkInstallConflicts()">
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

        if (nameWarn) {
            if (res.name_conflict) {
                nameWarn.textContent = `Container "${name}" already exists`;
                nameWarn.style.display = 'block';
            } else {
                nameWarn.style.display = 'none';
            }
        }
        if (portWarn) {
            if (res.port_conflict) {
                portWarn.textContent = `Port ${port} is already in use`;
                portWarn.style.display = 'block';
            } else {
                portWarn.style.display = 'none';
            }
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

    showProgressModal(`Installing ${instanceName}`, 'Pulling image and starting container...');

    const res = await API.post('/api/apps/install', {
        app_name: appName,
        instance_name: instanceName,
        config: config
    });

    hideProgressModal();

    if (res && res.success) {
        showToast('success', res.message);
    } else {
        showToast('error', (res && res.message) || 'Installation failed');
    }
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
                <button class="btn btn-primary" onclick="showCreateBackup()">Create Backup</button>
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
                                <button class="btn-sm btn-success" onclick="confirmRestore('${esc(b.filename)}', '${esc(b.meta?.container || '')}')">Restore</button>
                                <button class="btn-sm btn-danger" onclick="confirmDeleteBackup('${esc(b.filename)}')">Delete</button>
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
                <button class="btn btn-primary" onclick="showExportDialog()">Export Package</button>
                <button class="btn" onclick="showImportDialog()">Import Package</button>
            </div>
        </div>

        <div class="section-card" style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.05) 0%, rgba(20, 184, 166, 0.05) 100%)">
            <h3>How Server Migration Works</h3>
            <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:1.5rem;margin-top:1rem;align-items:center">
                <div style="padding:20px;background:linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(236, 72, 153, 0.05) 100%);border-radius:var(--radius-sm);border:1px solid rgba(236, 72, 153, 0.2)">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
                        <span style="font-size:2rem">📤</span>
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
                        <span style="font-size:2rem">📥</span>
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
                <button class="btn btn-danger" onclick="showClearAuditDialog()">Clear Old Logs</button>
            </div>
        </div>
        <div class="section-card" style="margin-bottom:1rem;padding:12px 16px">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
                <label style="font-size:12px;color:var(--text2);font-weight:500">Event:</label>
                <select class="form-input" id="audit-filter" style="width:auto" onchange="loadAuditLogs()">
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
                <select class="form-input" id="audit-user-filter" style="width:auto" onchange="loadAuditLogs()">
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
            <thead><tr><th>Timestamp</th><th>Event</th><th>Application</th><th>User</th><th>Details</th><th></th></tr></thead>
            <tbody>
                ${data.map(e => `
                    <tr>
                        <td style="font-size:0.8rem">${esc(e.timestamp?.substring(0, 19) || '-')}</td>
                        <td><span style="color:var(--teal);font-weight:600">${esc(e.event_type)}</span></td>
                        <td>${esc(e.app_name)}</td>
                        <td>${esc(e.user)}</td>
                        <td style="font-size:0.8rem;color:var(--text3)">${esc(JSON.stringify(e.details || {}))}</td>
                        <td><button class="btn btn-sm btn-danger" onclick="deleteAuditEvent('${esc(e.timestamp)}','${esc(e.event_type)}')" title="Delete">&times;</button></td>
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

async function deleteAuditEvent(timestamp, eventType) {
    const res = await API.post('/api/audit/delete', { timestamp, event_type: eventType });
    if (res && res.success) {
        showToast('success', 'Event deleted');
        await loadAuditLogs();
    } else {
        showToast('error', (res && res.message) || 'Delete failed');
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
                    <div style="font-size:1.2rem;font-weight:700;color:var(--text)">${Object.values(info.features).filter(f => f).length} <span style="color:var(--text3);font-size:0.9rem">/ 4</span></div>
                </div>
            </div>
        </div>

        <div class="section-card">
            <h3>Feature Access</h3>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:0.75rem;margin-top:0.75rem">
                ${Object.entries(info.features).map(([k, v]) => {
                    const labels = {
                        backup_restore: { icon: '💾', label: 'Backup & Restore', desc: 'Create and restore container backups' },
                        multi_instance: { icon: '📦', label: 'Multi-Instance', desc: 'Run multiple instances of the same app' },
                        migration: { icon: '🚀', label: 'Server Migration', desc: 'Migrate containers between servers' },
                        audit_log: { icon: '📋', label: 'Audit Logging', desc: 'Track all system operations' }
                    };
                    const feature = labels[k] || { icon: '✓', label: k, desc: '' };
                    return `
                        <div style="padding:12px;background:${v ? 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%)' : 'var(--surface2)'};border-radius:var(--radius-sm);border:1px solid ${v ? 'rgba(34, 197, 94, 0.2)' : 'var(--border)'}">
                            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                                <span style="font-size:1.2rem">${feature.icon}</span>
                                <span style="font-weight:700;font-size:0.9rem;color:${v ? 'var(--green)' : 'var(--text3)'}">${feature.label}</span>
                                <span style="margin-left:auto;font-size:1.2rem">${v ? '✓' : '✗'}</span>
                            </div>
                            <div style="font-size:0.8rem;color:var(--text2);line-height:1.4">${feature.desc}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>

        ${!info.is_pro ? `
            <div class="section-card" style="background: linear-gradient(135deg, rgba(234, 179, 8, 0.08) 0%, rgba(234, 179, 8, 0.02) 100%); border:1px solid var(--yellow)">
                <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap">
                    <div style="flex:1;min-width:240px">
                        <h3 style="color:var(--yellow);margin-bottom:6px;display:flex;align-items:center;gap:8px"><span>⚡</span> Upgrade to PRO</h3>
                        <p style="font-size:0.88rem;color:var(--text2);margin:0;line-height:1.5">Unlock unlimited containers, backups, server migrations, audit logging, and priority support.</p>
                    </div>
                    <div style="display:flex;gap:10px;align-items:center">
                        <input type="text" class="form-input" id="license-key" placeholder="Enter PRO license key" style="width:280px;margin:0">
                        <button class="btn btn-primary" onclick="activateLicense()">Activate PRO</button>
                    </div>
                </div>
            </div>
        ` : `
            <div class="section-card">
                <h3>License Actions</h3>
                <div style="display:flex;gap:12px;align-items:center;margin-top:0.75rem">
                    <button class="btn btn-danger" onclick="deactivateLicense()">Deactivate PRO License</button>
                    <span style="font-size:0.85rem;color:var(--text3)">This will revert your account to FREE tier</span>
                </div>
            </div>
        `}

        <div class="section-card">
            <h3>Security Settings</h3>
            <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin-top:0.75rem">
                <div style="flex:1;min-width:240px">
                    <div style="font-size:0.9rem;font-weight:600;color:var(--text);margin-bottom:4px">Web Interface Password</div>
                    <p style="font-size:0.85rem;color:var(--text2);margin:0">Update your login password for the web interface</p>
                </div>
                <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
                    <input type="password" class="form-input" id="pw-current" placeholder="Current password" style="width:180px;margin:0">
                    <input type="password" class="form-input" id="pw-new" placeholder="New password" style="width:180px;margin:0">
                    <button class="btn btn-primary" onclick="changePassword()">Update Password</button>
                </div>
            </div>
        </div>
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
                Router.navigate();
            }
        }}
    ]);
}

async function changePassword() {
    const current = document.getElementById('pw-current')?.value;
    const newPw = document.getElementById('pw-new')?.value;
    if (!current || !newPw) { showToast('error', 'Fill in both fields'); return; }

    const res = await API.post('/api/auth/change-password', {
        current_password: current,
        new_password: newPw
    });
    if (res && res.success) {
        showToast('success', 'Password changed');
        document.getElementById('pw-current').value = '';
        document.getElementById('pw-new').value = '';
    } else {
        showToast('error', (res && res.message) || 'Failed to change password');
    }
}

// ============ System Page ============
Router.register('#/system', async function(el) {
    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">System / <span class="current">System Info</span></div>
                <h1>System Information</h1>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" onclick="checkSystemUpdate()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
                    Check for Updates
                </button>
            </div>
        </div>
        <div id="system-info"><div class="loading"><span class="spinner"></span> Loading...</div></div>
    `;

    const data = await API.get('/api/system');
    const info = document.getElementById('system-info');
    if (!data || !info) return;

    info.innerHTML = `
        <div class="section-card" style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.05) 0%, rgba(20, 184, 166, 0.05) 100%)">
            <h3>System Information</h3>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.5rem;margin-top:1rem">
                <div style="padding:16px;background:var(--surface2);border-radius:var(--radius-sm);border:1px solid var(--border)">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
                        <span style="font-size:1.8rem">💻</span>
                        <div>
                            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3)">Operating System</div>
                            <div style="font-size:1.1rem;font-weight:700;color:var(--text)">${esc(data.platform)}</div>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px;font-size:0.88rem">
                        <span style="color:var(--text3)">OS:</span>
                        <span style="font-weight:600;color:var(--text)">${esc(data.os)}</span>
                        <span style="color:var(--text3)">Package Mgr:</span>
                        <span style="font-weight:600;color:var(--text)">${esc(data.package_manager || 'None')}</span>
                    </div>
                </div>

                <div style="padding:16px;background:var(--surface2);border-radius:var(--radius-sm);border:1px solid var(--border)">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
                        <span style="font-size:1.8rem">🐳</span>
                        <div>
                            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3)">Docker Engine</div>
                            <div style="font-size:1.1rem;font-weight:700;color:${data.docker.running ? 'var(--green)' : 'var(--red)'}">${data.docker.running ? 'Running' : 'Stopped'}</div>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px;font-size:0.88rem">
                        <span style="color:var(--text3)">Installed:</span>
                        <span class="status-badge ${data.docker.installed ? 'running' : 'stopped'}">${data.docker.installed ? 'Yes' : 'No'}</span>
                        ${data.docker.desktop !== undefined ? `
                            <span style="color:var(--text3)">Desktop:</span>
                            <span style="font-weight:600;color:${data.docker.desktop ? 'var(--green)' : 'var(--text2)'}"> ${data.docker.desktop ? 'Running' : 'Not running'}</span>
                        ` : ''}
                    </div>
                </div>

                <div style="padding:16px;background:var(--surface2);border-radius:var(--radius-sm);border:1px solid var(--border)">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
                        <span style="font-size:1.8rem">📦</span>
                        <div>
                            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3)">Dependencies</div>
                            <div style="font-size:1.1rem;font-weight:700;color:var(--text)">${Object.values(data.dependencies).filter(v => v).length} / ${Object.keys(data.dependencies).length} Available</div>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.88rem">
                        ${Object.entries(data.dependencies).map(([k, v]) => `
                            <div style="display:flex;align-items:center;gap:6px">
                                <span style="font-size:1rem;color:${v ? 'var(--green)' : 'var(--text3)'}">${v ? '✓' : '✗'}</span>
                                <span style="font-weight:600;color:${v ? 'var(--text)' : 'var(--text3)'}">${k.replace(/_/g, ' ')}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
        <div class="section-card" id="update-info-card" style="display:none"></div>
    `;

    // Check for ORCHIX updates
    const updateRes = await API.get('/api/system/check-update');
    const updateCard = document.getElementById('update-info-card');
    if (updateRes && updateCard) {
        if (updateRes.update_available) {
            updateCard.innerHTML = `
                <h3>ORCHIX Update Available</h3>
                <p style="margin:0.5rem 0;color:var(--text2)">
                    Current: <strong>v${esc(updateRes.current_version)}</strong> &rarr;
                    Latest: <strong style="color:var(--teal)">v${esc(updateRes.latest_version)}</strong>
                </p>
                <p style="font-size:0.85rem;color:var(--text3)">Pull the latest version from GitHub to update.</p>
            `;
            updateCard.style.display = '';
        } else {
            updateCard.innerHTML = `
                <h3>ORCHIX Version</h3>
                <p style="margin:0.5rem 0;color:var(--text2)">
                    v${esc(updateRes.current_version)} <span class="status-badge running">Up to date</span>
                </p>
            `;
            updateCard.style.display = '';
        }
    }
});

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
