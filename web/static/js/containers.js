// ORCHIX v1.4 - Containers Page

Router.register('#/containers', async function(el) {
    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">Management / <span class="current">Containers</span></div>
                <h1>Container Management</h1>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" data-action="refreshContainers">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
                    Refresh
                </button>
            </div>
        </div>
        <div class="table-toolbar">
            <input type="text" class="search-input" id="container-search"
                   placeholder="Search containers..." data-oninput="filterContainers">
            ${hasPermission('containers.start') ? `
            <div class="toolbar-actions" id="batch-actions" style="display:none">
                <button class="btn-sm btn-success" data-action="batchAction" data-p1="start">Start Selected</button>
                <button class="btn-sm btn-danger" data-action="batchAction" data-p1="stop">Stop Selected</button>
            </div>` : ''}
        </div>
        <div id="containers-list"><div class="loading"><span class="spinner"></span> Loading containers...</div></div>
    `;
    await refreshContainers();
});

const _CLI_MAP = {
    'redis': name => `docker exec -it ${name} redis-cli`,
    'postgres': name => `docker exec -it ${name} psql -U postgres`,
    'postgresql': name => `docker exec -it ${name} psql -U postgres`,
    'mariadb': name => `docker exec -it ${name} mysql -u root -p`,
    'mysql': name => `docker exec -it ${name} mysql -u root -p`,
    'mongo': name => `docker exec -it ${name} mongosh`,
    'mongodb': name => `docker exec -it ${name} mongosh`,
    'mosquitto': name => `docker exec -it ${name} mosquitto_sub -t "#"`,
};
const _WEB_PORTS = new Set([80, 443, 3000, 4000, 4040, 5000, 8000, 8080, 8088, 8443, 8888, 9000, 9090]);

function _buildAccessPopup(c) {
    if (c.status !== 'running') return '';
    const lines = [];

    // Web URL from ports
    if (c.ports && c.ports.length > 0) {
        for (const p of c.ports) {
            if (_WEB_PORTS.has(p.container) || _WEB_PORTS.has(p.host)) {
                const proto = (p.container === 443 || p.host === 443) ? 'https' : 'http';
                lines.push(`<div style="margin-bottom:4px"><span style="color:var(--text2);font-size:0.72rem">Host</span><br><a href="${proto}://localhost:${p.host}" target="_blank" style="color:var(--teal);text-decoration:none">${proto}://localhost:${p.host}</a></div>`);
                break;
            }
        }
        // If no web port, show raw host port
        if (lines.length === 0) {
            const p = c.ports[0];
            lines.push(`<div style="margin-bottom:4px"><span style="color:var(--text2);font-size:0.72rem">Host</span><br><span style="color:var(--text)">localhost:${p.host}</span></div>`);
        }
    }

    // CLI command from image
    if (c.image) {
        const imgBase = c.image.split(':')[0].split('/').pop().toLowerCase();
        const cmdFn = _CLI_MAP[imgBase];
        if (cmdFn) {
            lines.push(`<div><span style="color:var(--text2);font-size:0.72rem">CLI</span><br><span style="color:var(--pink)">${esc(cmdFn(c.name))}</span></div>`);
        }
    }

    if (lines.length === 0) return '';
    return `<div class="c-access-popup">${lines.join('')}</div>`;
}

async function refreshContainers() {
    const data = await API.get('/api/containers');
    const el = document.getElementById('containers-list');
    if (!data || !el) return;

    if (data.length === 0) {
        el.innerHTML = '<div class="empty-state"><h2>No containers found</h2><p>Install an application first.</p></div>';
        return;
    }

    el.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th style="width:40px"><input type="checkbox" class="table-checkbox" id="select-all" data-onchange="toggleSelectAll"></th>
                    <th>Container</th>
                    <th>Status</th>
                    <th>Disk Size</th>
                    <th style="width:200px">Actions</th>
                </tr>
            </thead>
            <tbody>
                ${data.map(c => {
                    const popup = _buildAccessPopup(c);
                    return `
                    <tr>
                        <td><input type="checkbox" class="table-checkbox container-cb" value="${esc(c.name)}" data-onchange="updateBatchActions"></td>
                        <td>
                            <div class="c-name-wrap">
                                <span style="color:var(--teal);font-weight:600">${esc(c.name)}</span>
                                ${popup}
                            </div>
                        </td>
                        <td>
                            <span class="status-badge ${c.status === 'running' ? 'running' : 'stopped'}">
                                ${c.status === 'running' ? 'Running' : esc(c.status.charAt(0).toUpperCase() + c.status.slice(1))}
                            </span>
                        </td>
                        <td style="font-size:0.8rem;color:var(--text2);font-family:'Consolas','SF Mono',monospace">${esc(c.size || '-')}</td>
                        <td>
                            <div class="btn-group">
                                ${hasPermission('containers.start') ? (c.status === 'running'
                                    ? `<button class="btn-sm btn-danger" data-action="containerAction" data-p1="${esc(c.name)}" data-p2="stop">Stop</button>`
                                    : `<button class="btn-sm btn-success" data-action="containerAction" data-p1="${esc(c.name)}" data-p2="start">Start</button>`
                                ) : ''}
                                <div class="action-dropdown">
                                    <button class="btn-icon" data-action="toggleActionMenu" title="More actions">&#8943;</button>
                                    <div class="action-menu">
                                        ${hasPermission('containers.restart') && c.status === 'running'
                                            ? `<button data-action="containerAction" data-p1="${esc(c.name)}" data-p2="restart">Restart</button>`
                                            : ''
                                        }
                                        ${hasPermission('apps.update') ? `<button data-action="showUpdateDialog" data-p1="${esc(c.name)}">Update</button>` : ''}
                                        ${hasPermission('containers.compose_write') ? `<button data-action="editComposeFile" data-p1="${esc(c.name)}">Edit YAML</button>` : ''}
                                        <button data-action="viewContainerLogs" data-p1="${esc(c.name)}">View Logs</button>
                                        <button data-action="viewContainerDetails" data-p1="${esc(c.name)}">Inspect</button>
                                        ${hasPermission('containers.uninstall') ? `<button class="danger" data-action="confirmUninstall" data-p1="${esc(c.name)}">Uninstall</button>` : ''}
                                    </div>
                                </div>
                            </div>
                        </td>
                    </tr>
                `}).join('')}
            </tbody>
        </table>
    `;
    _initAccessPopups();
}

let _accessTimer = null;
function _initAccessPopups() {
    document.querySelectorAll('.c-name-wrap').forEach(wrap => {
        const popup = wrap.querySelector('.c-access-popup');
        if (!popup) return;

        const show = () => { clearTimeout(_accessTimer); popup.classList.add('visible'); };
        const hide = () => { _accessTimer = setTimeout(() => popup.classList.remove('visible'), 120); };

        wrap.addEventListener('mouseenter', show);
        wrap.addEventListener('mouseleave', hide);
        popup.addEventListener('mouseenter', show);
        popup.addEventListener('mouseleave', hide);
    });
}

function filterContainers() {
    const query = (document.getElementById('container-search')?.value || '').toLowerCase();
    document.querySelectorAll('#containers-list tbody tr').forEach(row => {
        const name = (row.querySelector('td:nth-child(2)')?.textContent || '').toLowerCase();
        row.style.display = name.includes(query) ? '' : 'none';
    });
}

function toggleSelectAll() {
    const checked = document.getElementById('select-all')?.checked;
    document.querySelectorAll('.container-cb').forEach(cb => cb.checked = checked);
    updateBatchActions();
}

function updateBatchActions() {
    const selected = document.querySelectorAll('.container-cb:checked').length;
    const el = document.getElementById('batch-actions');
    if (el) el.style.display = selected > 0 ? 'flex' : 'none';
}

async function batchAction(action) {
    const names = Array.from(document.querySelectorAll('.container-cb:checked')).map(cb => cb.value);
    for (const name of names) {
        await containerAction(name, action);
    }
}

async function containerAction(name, action) {
    const labels = { start: 'Starting', stop: 'Stopping', restart: 'Restarting' };
    showProgressModalWithBar(`${labels[action] || action} ${name}`, 'Initializing...', 0);

    // Simulate progress while waiting for response
    let progress = 0;
    const interval = setInterval(() => {
        progress = Math.min(progress + 10, 90);
        updateProgressBar(progress, labels[action] + '...');
    }, 100);

    const res = await API.post(`/api/containers/${name}/${action}`, {
        headers: { 'X-CSRFToken': getCsrfToken() }
    });

    clearInterval(interval);
    updateProgressBar(100, 'Complete!');

    setTimeout(() => {
        hideProgressModal();
        if (res && res.success) {
            showToast('success', res.message);
            setTimeout(refreshContainers, 1000);
        } else {
            showToast('error', (res && res.message) || 'Action failed');
        }
    }, 300);
}

async function viewContainerLogs(name) {
    showModal('Logs: ' + name, '<div class="loading"><span class="spinner"></span> Loading logs...</div>', []);
    const res = await API.get(`/api/containers/${name}/logs?tail=100`);
    if (res) {
        const logContent = (res.logs || '') + (res.stderr ? '\n--- STDERR ---\n' + res.stderr : '');
        showModal(
            'Logs: ' + name,
            `<div class="logs-viewer">${esc(logContent || 'No logs available')}</div>`,
            [{ label: 'Close', cls: 'btn-primary' }]
        );
    }
}

async function viewContainerDetails(name) {
    showModal('Inspect: ' + name, '<div class="loading"><span class="spinner"></span> Loading...</div>', []);
    const res = await API.get(`/api/containers/${name}/inspect`);
    if (res && !res.error) {
        const portsHtml = Object.entries(res.ports || {}).map(([port, bindings]) =>
            bindings.map(b => `<span>${esc(b.HostPort)} -> ${esc(port)}</span>`).join('<br>')
        ).join('<br>') || 'None';

        showModal('Inspect: ' + name, `
            <div class="section-card" style="margin-bottom:0">
                <div style="display:grid;grid-template-columns:120px 1fr;gap:0.5rem;font-size:0.9rem">
                    <span style="color:var(--text2)">Status</span>
                    <span><span class="status-badge ${res.running ? 'running' : 'stopped'}">${esc(res.status)}</span></span>
                    <span style="color:var(--text2)">Image</span>
                    <span>${esc(res.image)}</span>
                    <span style="color:var(--text2)">Started</span>
                    <span>${esc(res.started_at)}</span>
                    <span style="color:var(--text2)">Ports</span>
                    <span>${portsHtml}</span>
                    <span style="color:var(--text2)">Env Vars</span>
                    <span style="font-size:0.8rem;color:var(--text3)">${esc((res.env || []).join(', ')) || 'None'}</span>
                </div>
            </div>
        `, [{ label: 'Close', cls: 'btn-primary' }]);
    }
}

function confirmUninstall(name) {
    showModal('Uninstall ' + name, `
        <p style="margin-bottom:0.8rem">This will <strong>completely remove</strong> the container, volumes, images, and all associated files.</p>
        <p style="color:var(--red);font-weight:600">This action cannot be undone!</p>
    `, [
        { label: 'Cancel', cls: '' },
        { label: 'Uninstall', cls: 'btn-danger', fn: () => doUninstall(name) }
    ]);
}

async function doUninstall(name) {
    showProgressModalWithBar(`Uninstalling ${name}`, 'Initializing...', 0);
    try {
        const response = await fetch(`/api/containers/${name}/uninstall-stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('orchix-session-token')}`,
                'X-CSRFToken': getCsrfToken()
            }
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
            showToast('success', finalResult.message);
            setTimeout(refreshContainers, 500);
        } else {
            showToast('error', 'Uninstall failed');
        }
    } catch (err) {
        hideProgressModal();
        showToast('error', 'Uninstall failed: ' + (err.message || 'Network error'));
    }
}

async function showUpdateDialog(name) {
    showModal('Update ' + name, '<div class="loading"><span class="spinner"></span> Loading update options...</div>', []);

    const res = await API.get(`/api/apps/update-actions/${name}`);
    if (!res || !res.actions || res.actions.length === 0) {
        showModal('Update ' + name, '<p>No update actions available for this container.</p>', [
            { label: 'Close', cls: 'btn-primary' }
        ]);
        return;
    }

    const btns = res.actions.map(a =>
        `<button class="btn btn-primary" style="width:100%;margin-bottom:0.5rem" data-action="doUpdate" data-p1="${esc(name)}" data-p2="${a.key}">${esc(a.label)}</button>`
    ).join('');

    showModal('Update ' + name, `
        <p style="margin-bottom:1rem;color:var(--text2)">Select update action:</p>
        ${btns}
    `, [{ label: 'Cancel', cls: '' }]);
}

async function doUpdate(name, updateType) {
    hideModal();
    showProgressModalWithBar(`Updating ${name}`, 'Initializing...', 0);

    try {
        const response = await fetch('/api/apps/update-stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('orchix-session-token')}`,
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                container_name: name,
                update_type: updateType
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
            showToast('success', finalResult.message);
            setTimeout(refreshContainers, 1000);
        } else {
            showToast('error', 'Update failed');
        }
    } catch (err) {
        hideProgressModal();
        showToast('error', 'Update failed: ' + err.message);
    }
}

async function editComposeFile(name) {
    showModal('Edit YAML: ' + name, '<div class="loading"><span class="spinner"></span> Loading compose file...</div>', []);
    const res = await API.get(`/api/containers/${name}/compose`);
    if (res && res.error) {
        showModal('Edit YAML: ' + name, `<p style="color:var(--text2)">No compose file found for this container.</p>`, [
            { label: 'Close', cls: 'btn-primary' }
        ]);
        return;
    }

    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal-content');
    modal.classList.add('wide');
    modal.innerHTML = `
        <div class="modal-header">
            <h2>Edit YAML: ${esc(name)}</h2>
            <button class="modal-close" data-action="hideModal">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="4" y1="4" x2="12" y2="12"/><line x1="12" y1="4" x2="4" y2="12"/>
                </svg>
            </button>
        </div>
        <div class="modal-body" style="padding:12px 24px">
            <div style="font-size:11px;color:var(--text3);margin-bottom:8px">${esc(res.filename)}</div>
            <div class="yaml-editor-wrap">
                <div id="yaml-line-numbers" class="yaml-line-numbers"></div>
                <textarea id="yaml-editor" class="yaml-editor" spellcheck="false">${esc(res.content)}</textarea>
            </div>
            <div id="yaml-error" class="yaml-error" style="display:none"></div>
        </div>
        <div class="modal-actions">
            <button class="btn" data-action="hideModal">Cancel</button>
            <button class="btn btn-primary" data-action="saveComposeFile" data-p1="${esc(name)}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                Save
            </button>
        </div>
    `;
    overlay.classList.remove('hidden');

    const editor = document.getElementById('yaml-editor');
    const lineNums = document.getElementById('yaml-line-numbers');

    function updateLineNumbers() {
        const lines = editor.value.split('\n').length;
        lineNums.innerHTML = Array.from({ length: lines }, (_, i) => `<div>${i + 1}</div>`).join('');
    }

    updateLineNumbers();
    editor.addEventListener('input', updateLineNumbers);
    editor.addEventListener('scroll', () => { lineNums.scrollTop = editor.scrollTop; });

    // Tab key support
    editor.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;
            this.value = this.value.substring(0, start) + '  ' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = start + 2;
            updateLineNumbers();
        }
    });
}

async function saveComposeFile(name) {
    const editor = document.getElementById('yaml-editor');
    const errorEl = document.getElementById('yaml-error');
    if (!editor) return;

    const content = editor.value;
    if (!content.trim()) {
        errorEl.textContent = 'Content cannot be empty';
        errorEl.style.display = 'block';
        return;
    }

    errorEl.style.display = 'none';
    const res = await API.post(`/api/containers/${name}/compose`, { content });
    if (res && res.success) {
        hideModal();
        showToast('success', res.message);
    } else {
        errorEl.textContent = (res && res.message) || 'Save failed';
        errorEl.style.display = 'block';
    }
}
