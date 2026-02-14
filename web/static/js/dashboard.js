// ORCHIX v1.2 - Dashboard Page

Router.register('#/dashboard', function(el) {
    el.innerHTML = `
        <div class="page-header">
            <div>
                <div class="breadcrumb">Management / <span class="current">Dashboard</span></div>
                <h1>Dashboard</h1>
            </div>
            <span class="connection-status" id="sse-status">Connecting...</span>
        </div>

        <div class="section-card" style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.05) 0%, rgba(20, 184, 166, 0.05) 100%);margin-bottom:14px">
            <h3>System Overview</h3>
            <div id="system-overview-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem;margin-top:1rem">
                <div class="loading" style="padding:20px;grid-column:1/-1"><span class="spinner"></span></div>
            </div>
        </div>

        <div class="metrics-row">
            <div class="metric-card">
                <div class="metric-icon" style="color:var(--accent)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><line x1="9" y1="20" x2="9" y2="10"/><line x1="15" y1="20" x2="15" y2="4"/></svg>
                </div>
                <div class="metric-content">
                    <label>CPU Usage</label>
                    <div class="value" id="cpu-val">--</div>
                    <div class="progress-bar"><div class="fill normal" id="cpu-bar" style="width:0%"></div></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon" style="color:var(--teal)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="12" rx="2"/><line x1="6" y1="10" x2="6" y2="14"/><line x1="10" y1="10" x2="10" y2="14"/><line x1="14" y1="10" x2="14" y2="14"/><line x1="18" y1="10" x2="18" y2="14"/></svg>
                </div>
                <div class="metric-content">
                    <label>Memory</label>
                    <div class="value" id="ram-val">--</div>
                    <div class="progress-bar"><div class="fill normal" id="ram-bar" style="width:0%"></div></div>
                    <div class="metric-text" id="ram-text"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon" style="color:var(--yellow)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                </div>
                <div class="metric-content">
                    <label>Disk</label>
                    <div class="value" id="disk-val">--</div>
                    <div class="progress-bar"><div class="fill normal" id="disk-bar" style="width:0%"></div></div>
                    <div class="metric-text" id="disk-text"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon" style="color:var(--green)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="7" rx="1.5"/><rect x="3" y="14" width="18" height="7" rx="1.5"/><circle cx="7" cy="6.5" r="1" fill="currentColor" stroke="none"/><circle cx="7" cy="17.5" r="1" fill="currentColor" stroke="none"/></svg>
                </div>
                <div class="metric-content">
                    <label>Containers</label>
                    <div class="value" id="container-count">--</div>
                    <div class="metric-text" id="container-text">running</div>
                </div>
            </div>
        </div>

        <div class="section-card" style="padding:14px 18px;margin-bottom:14px">
            <div class="info-grid" id="docker-info" style="font-size:13px;color:var(--text2)">Loading Docker info...</div>
        </div>

        <div class="section-card" style="padding:14px 18px;margin-bottom:14px">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><polyline points="12 5 19 12 12 19"/></svg>
                <span style="font-size:12px;font-weight:600;color:var(--text);text-transform:uppercase;letter-spacing:0.6px">Network</span>
                <span style="font-size:11px;color:var(--text3);margin-left:auto" id="net-total"></span>
            </div>
            <div id="net-interfaces" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px"></div>
        </div>

        <div class="alerts-bar healthy" id="alerts-bar">
            Connecting...
        </div>

        <table class="data-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Container</th>
                    <th>Status</th>
                    <th>CPU</th>
                    <th>Memory</th>
                    <th>Net I/O</th>
                    <th>Ports</th>
                    <th>Image</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="container-tbody">
                <tr><td colspan="9" class="loading"><span class="spinner"></span> Loading...</td></tr>
            </tbody>
        </table>

        <div style="margin-top:1rem">
            <div class="info-bar" id="volumes-info" style="display:none"></div>
        </div>

        <div style="position:fixed;bottom:16px;left:calc(var(--sidebar-width) + 16px);z-index:10;transition:left 0.3s" id="dashboard-footer">
            <div class="container-summary" id="container-summary"></div>
        </div>
    `;

    // Load system overview data
    loadSystemOverview();

    // Start SSE connection
    const source = new EventSource('/api/dashboard/stream');
    Router.currentSSE = source;

    source.onmessage = function(event) {
        const d = JSON.parse(event.data);
        if (d.error) return;

        // Connection status
        const statusEl = document.getElementById('sse-status');
        statusEl.textContent = 'Live';
        statusEl.className = 'connection-status connected';

        // System metrics
        updateMetric('cpu', d.system.cpu);
        updateMetric('ram', d.system.ram_percent);
        updateMetric('disk', d.system.disk_percent);

        document.getElementById('cpu-val').textContent = d.system.cpu.toFixed(0) + '%';
        document.getElementById('ram-val').textContent = d.system.ram_percent.toFixed(0) + '%';
        document.getElementById('ram-text').textContent =
            d.system.ram_used.toFixed(1) + ' / ' + d.system.ram_total.toFixed(1) + ' GB';
        document.getElementById('disk-val').textContent = d.system.disk_percent + '%';
        document.getElementById('disk-text').textContent =
            d.system.disk_used + ' / ' + d.system.disk_total + ' GB';

        // Container count + summary
        const running = d.containers.filter(c => c.running).length;
        const total = d.containers.length;
        document.getElementById('container-count').textContent = running + '/' + total;
        document.getElementById('container-text').textContent = 'running / total';

        const summaryEl = document.getElementById('container-summary');
        if (summaryEl) {
            summaryEl.innerHTML = `
                <span class="summary-stat running"><span class="dot"></span> ${running} Running</span>
                <span class="summary-stat stopped"><span class="dot"></span> ${total - running} Stopped</span>
                <span class="summary-stat total">${total} Total</span>
            `;
        }

        // Docker info as grid
        const di = d.docker;
        const dockerEl = document.getElementById('docker-info');
        dockerEl.innerHTML = `
            <div class="info-grid-item"><div class="label">Engine</div><div class="val">${di.version}</div></div>
            <div class="info-grid-item"><div class="label">Images</div><div class="val">${di.images}</div></div>
            <div class="info-grid-item"><div class="label">Volumes</div><div class="val">${di.volumes}</div></div>
            <div class="info-grid-item"><div class="label">Networks</div><div class="val">${di.networks}</div></div>
        `;

        // Volumes
        if (di.volume_names && di.volume_names.length > 0) {
            const volEl = document.getElementById('volumes-info');
            volEl.style.display = 'flex';
            const shown = di.volume_names.slice(0, 8).join(', ');
            const more = di.volume_names.length > 8 ? ` (+${di.volume_names.length - 8} more)` : '';
            volEl.innerHTML = `Volumes: <span>${shown}${more}</span>`;
        }

        // Alerts
        const alertsEl = document.getElementById('alerts-bar');
        if (d.alerts.length > 0) {
            const hasCritical = d.alerts.some(a => a.includes('CRITICAL') || a.includes('DOWN'));
            alertsEl.className = 'alerts-bar ' + (hasCritical ? 'critical' : 'has-alerts');
            alertsEl.textContent = d.alerts.join('  |  ');
        } else {
            alertsEl.className = 'alerts-bar healthy';
            alertsEl.textContent = 'All systems healthy';
        }

        // Network
        if (d.network) {
            const netEl = document.getElementById('net-interfaces');
            const totalEl = document.getElementById('net-total');
            if (d.network.interfaces.length > 0) {
                netEl.innerHTML = d.network.interfaces.map(iface => `
                    <div class="net-iface">
                        <div class="net-iface-name">
                            <span class="dot" style="background:${iface.active ? 'var(--green)' : 'var(--text3)'}"></span>
                            ${esc(iface.name)}
                        </div>
                        <div class="net-iface-speeds">
                            <span class="net-up" title="Upload">&#8593; ${formatSpeed(iface.up)}</span>
                            <span class="net-down" title="Download">&#8595; ${formatSpeed(iface.down)}</span>
                        </div>
                    </div>
                `).join('');
                totalEl.textContent = `Total: ↑ ${formatSpeed(d.network.total_up)}  ↓ ${formatSpeed(d.network.total_down)}`;
            } else {
                netEl.innerHTML = '<span style="color:var(--text3);font-size:12px">Waiting for data...</span>';
                totalEl.textContent = '';
            }
        }

        // Container table
        const tbody = document.getElementById('container-tbody');
        if (d.containers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="empty-state">No containers found</td></tr>';
            return;
        }

        tbody.innerHTML = d.containers.map((c, i) => `
            <tr>
                <td>${i + 1}</td>
                <td><span style="color:var(--teal);font-weight:600">${esc(c.name)}</span></td>
                <td>
                    <span class="status-badge ${c.running ? 'running' : 'stopped'}">
                        ${c.running ? 'Running' : 'Stopped'}
                    </span>
                </td>
                <td class="${getCpuClass(c.cpu)}">${esc(c.cpu)}</td>
                <td>${esc(c.memory)}</td>
                <td>${esc(c.net_io)}</td>
                <td><code style="font-size:11px;color:var(--text3)">${esc(c.ports)}</code></td>
                <td style="font-size:11px;color:var(--text3)">${esc(c.image)}</td>
                <td>
                    <div class="btn-group">
                        ${c.running
                            ? `<button class="btn-sm btn-danger" onclick="dashAction('${esc(c.name)}','stop')">Stop</button>
                               <button class="btn-sm btn-warn" onclick="dashAction('${esc(c.name)}','restart')">Restart</button>`
                            : `<button class="btn-sm btn-success" onclick="dashAction('${esc(c.name)}','start')">Start</button>`
                        }
                        <button class="btn-sm" onclick="dashLogs('${esc(c.name)}')">Logs</button>
                    </div>
                </td>
            </tr>
        `).join('');
    };

    source.onerror = function() {
        const statusEl = document.getElementById('sse-status');
        statusEl.textContent = 'Reconnecting...';
        statusEl.className = 'connection-status disconnected';
    };
});

function updateMetric(id, value) {
    const bar = document.getElementById(id + '-bar');
    if (!bar) return;
    bar.style.width = value + '%';
    bar.className = 'fill ' + (value >= 90 ? 'critical' : value >= 70 ? 'warning' : 'normal');
}

function esc(str) {
    if (!str) return '-';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function formatSpeed(bps) {
    if (bps >= 1048576) return (bps / 1048576).toFixed(1) + ' MB/s';
    if (bps >= 1024) return (bps / 1024).toFixed(1) + ' KB/s';
    return bps.toFixed(0) + ' B/s';
}

async function dashAction(name, action) {
    const res = await API.post(`/api/containers/${name}/${action}`);
    if (res && res.success) {
        showToast('success', res.message);
    } else {
        showToast('error', (res && res.message) || 'Action failed');
    }
}

async function dashLogs(name) {
    const res = await API.get(`/api/containers/${name}/logs?tail=80`);
    if (res) {
        showModal(
            `Logs: ${name}`,
            `<div class="logs-viewer">${esc(res.logs || '') + (res.stderr ? '\n--- STDERR ---\n' + esc(res.stderr) : '')}</div>`,
            [{ label: 'Close', cls: 'btn-primary' }]
        );
    }
}

async function loadSystemOverview() {
    const data = await API.get('/api/system');
    const grid = document.getElementById('system-overview-grid');
    if (!data || !grid) return;

    // Check for ORCHIX updates first
    const updateRes = await API.get('/api/system/check-update');

    grid.innerHTML = `
        <div style="padding:16px;background:var(--surface2);border-radius:var(--radius-sm);border:1px solid var(--border)">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
                <div style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(236,72,153,0.15),rgba(20,184,166,0.15));border-radius:var(--radius-sm)">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--pink)" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                </div>
                <div style="flex:1">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:2px">Operating System</div>
                    <div style="font-size:1.05rem;font-weight:700;color:var(--text)">${esc(data.platform)}</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:0.86rem">
                <div style="display:flex;align-items:center;gap:6px">
                    <span style="color:var(--text3)">OS:</span>
                    <span style="font-weight:600;color:var(--text)">${esc(data.os)}</span>
                </div>
                <div style="display:flex;align-items:center;gap:6px">
                    <span style="color:var(--text3)">Package:</span>
                    <span style="font-weight:600;color:var(--text)">${esc(data.package_manager || 'None')}</span>
                </div>
            </div>
        </div>

        <div style="padding:16px;background:var(--surface2);border-radius:var(--radius-sm);border:1px solid var(--border)">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
                <div style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(${data.docker.running ? '34,197,94' : '239,68,68'},0.15),rgba(${data.docker.running ? '34,197,94' : '239,68,68'},0.15));border-radius:var(--radius-sm)">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="${data.docker.running ? 'var(--green)' : 'var(--red)'}" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
                </div>
                <div style="flex:1">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:2px">Docker Engine</div>
                    <div style="font-size:1.05rem;font-weight:700;color:${data.docker.running ? 'var(--green)' : 'var(--red)'}">${data.docker.running ? 'Running' : 'Stopped'}</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:auto 1fr;gap:5px 10px;font-size:0.86rem">
                <span style="color:var(--text3)">Installed:</span>
                <span class="status-badge ${data.docker.installed ? 'running' : 'stopped'}">${data.docker.installed ? 'Yes' : 'No'}</span>
                ${data.docker.desktop !== undefined ? `
                    <span style="color:var(--text3)">Desktop:</span>
                    <span style="font-weight:600;color:${data.docker.desktop ? 'var(--green)' : 'var(--text2)'}">${data.docker.desktop ? 'Running' : 'Not running'}</span>
                ` : ''}
            </div>
        </div>

        <div style="padding:16px;background:var(--surface2);border-radius:var(--radius-sm);border:1px solid var(--border)">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
                <div style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(236,72,153,0.15),rgba(20,184,166,0.15));border-radius:var(--radius-sm)">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="7.5 4.21 12 6.81 16.5 4.21"/><polyline points="7.5 19.79 7.5 14.6 3 12"/><polyline points="21 12 16.5 14.6 16.5 19.79"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
                </div>
                <div style="flex:1">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:2px">Dependencies</div>
                    <div style="font-size:1.05rem;font-weight:700;color:var(--text)">${Object.values(data.dependencies).filter(v => v).length} / ${Object.keys(data.dependencies).length} Available</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:0.86rem">
                ${Object.entries(data.dependencies).map(([k, v]) => `
                    <div style="display:flex;align-items:center;gap:6px">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${v ? 'var(--green)' : 'var(--text3)'}" stroke-width="2.5"><${v ? 'polyline points="20 6 9 17 4 12"' : 'line x1="18" y1="6" x2="6" y2="18"'}/>${v ? '' : '<line x1="6" y1="6" x2="18" y2="18"/>'}</svg>
                        <span style="font-weight:600;color:${v ? 'var(--text)' : 'var(--text3)'}">${k.replace(/_/g, ' ')}</span>
                    </div>
                `).join('')}
            </div>
        </div>

        <div style="padding:16px;background:var(--surface2);border-radius:var(--radius-sm);border:1px solid var(--border)">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
                <div style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(236,72,153,0.15),rgba(20,184,166,0.15));border-radius:var(--radius-sm)">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                </div>
                <div style="flex:1">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:2px">ORCHIX</div>
                    <div style="font-size:1.05rem;font-weight:700;color:var(--text)">${updateRes && updateRes.current_version ? 'v' + esc(updateRes.current_version) : 'v1.2'}</div>
                </div>
            </div>
            <div style="display:flex;flex-direction:column;gap:6px;font-size:0.86rem">
                <div style="font-size:0.82rem;color:var(--text3)">
                    ${updateRes && updateRes.update_available ?
                        `<span style="color:var(--teal);font-weight:600">v${esc(updateRes.latest_version)} available</span>` :
                        updateRes ?
                            '<span style="color:var(--green)">✓ Up to date</span>' :
                            '<span style="color:var(--text3)">Checking...</span>'
                    }
                </div>
                ${updateRes && updateRes.update_available ?
                    '<button class="btn btn-sm btn-primary" onclick="updateOrchixNow()" style="font-size:0.8rem;padding:4px 10px;width:100%">Update Now</button>' :
                    '<button class="btn btn-sm" onclick="checkSystemUpdate()" style="font-size:0.8rem;padding:4px 10px;width:100%">Check Update</button>'
                }
            </div>
        </div>
    `;
}
