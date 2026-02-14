import json
import time
import subprocess
import psutil
import shutil
import platform
from flask import Blueprint, Response, jsonify, session
from web.auth import require_permission

bp = Blueprint('api_dashboard', __name__, url_prefix='/api')

IS_WINDOWS = platform.system().lower() == 'windows'

# Cache for docker info (version, images, volumes, networks)
_docker_info_cache = None
_docker_info_time = 0
_DOCKER_INFO_TTL = 30

# Network speed tracking (per SSE generator)
_prev_net = None
_prev_net_time = 0


def _safe_run(cmd, timeout=10):
    """Run a command with timeout, return stdout or empty string."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, encoding='utf-8', errors='ignore'
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return ''


def _get_containers():
    """Get container list with stats. Timeout-safe."""
    containers = []

    # Get container list (fast, <1s)
    out = _safe_run(
        ['docker', 'ps', '-a', '--format', '{{.Names}}|{{.Status}}|{{.Ports}}|{{.Image}}'],
        timeout=5
    )
    if not out:
        return containers

    for line in out.split('\n'):
        if not line.strip():
            continue
        parts = line.split('|')
        if len(parts) < 2:
            continue

        name = parts[0].strip()
        status_raw = parts[1].strip()
        ports_raw = parts[2].strip() if len(parts) > 2 else ''
        image = parts[3].strip() if len(parts) > 3 else '-'

        if '/' in image:
            image = image.split('/')[-1]

        running = status_raw.startswith('Up')

        # Parse uptime
        uptime = ''
        if running:
            text = status_raw.replace('Up ', '').strip()
            if '(' in text:
                text = text[:text.index('(')].strip()
            low = text.lower()
            units = {'second': 's', 'minute': 'm', 'hour': 'h', 'day': 'd', 'week': 'w', 'month': 'mo'}
            for kw, sfx in units.items():
                if kw in low:
                    first = text.split()[0]
                    uptime = f"{first}{sfx}" if first.isdigit() else f"?{sfx}"
                    break
            if not uptime and low.startswith('about'):
                uptime = '~1m' if 'minute' in low else '~1h'

        # Parse ports
        host_ports = []
        if ports_raw:
            for mapping in ports_raw.split(', '):
                if '->' in mapping:
                    host_part = mapping.split('->')[0]
                    port = host_part.split(':')[-1] if ':' in host_part else host_part
                    if port and port not in host_ports:
                        host_ports.append(port)

        containers.append({
            'name': name,
            'status': status_raw,
            'running': running,
            'uptime': uptime,
            'ports': ', '.join(host_ports) if host_ports else '-',
            'image': image,
            'cpu': '-',
            'memory': '-',
            'net_io': '-',
        })

    # Get stats (can be slow ~1-2s, timeout at 8s)
    stats_out = _safe_run(
        ['docker', 'stats', '--no-stream', '--format', '{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}'],
        timeout=8
    )
    if stats_out:
        stats_map = {}
        for line in stats_out.split('\n'):
            if not line.strip():
                continue
            parts = line.split('|')
            if len(parts) >= 4:
                stats_map[parts[0].strip()] = {
                    'cpu': parts[1].strip(),
                    'memory': parts[2].strip(),
                    'net_io': parts[3].strip(),
                }
        for c in containers:
            if c['name'] in stats_map:
                c.update(stats_map[c['name']])

    return containers


def _get_system():
    """Get system metrics via psutil."""
    try:
        cpu = psutil.cpu_percent(interval=0)
        mem = psutil.virtual_memory()
        disk_root = 'C:\\' if IS_WINDOWS else '/'
        try:
            total, used, free = shutil.disk_usage(disk_root)
        except OSError:
            total, used, free = 1, 0, 1

        return {
            'cpu': cpu,
            'ram_total': round(mem.total / (1024 ** 3), 1),
            'ram_used': round(mem.used / (1024 ** 3), 1),
            'ram_percent': mem.percent,
            'disk_total': total // (2 ** 30),
            'disk_used': used // (2 ** 30),
            'disk_free': free // (2 ** 30),
            'disk_percent': int((used / total) * 100) if total else 0,
        }
    except Exception:
        return {
            'cpu': 0, 'ram_total': 0, 'ram_used': 0, 'ram_percent': 0,
            'disk_total': 0, 'disk_used': 0, 'disk_free': 0, 'disk_percent': 0,
        }


def _get_docker_info():
    """Get Docker engine info with caching."""
    global _docker_info_cache, _docker_info_time
    now = time.time()
    if _docker_info_cache and (now - _docker_info_time) < _DOCKER_INFO_TTL:
        return _docker_info_cache

    info = {'version': '?', 'images': 0, 'volumes': 0, 'networks': 0, 'volume_names': []}

    v = _safe_run(['docker', 'version', '--format', '{{.Server.Version}}'], timeout=5)
    if v:
        info['version'] = f'v{v}'

    imgs = _safe_run(['docker', 'images', '-q'], timeout=5)
    if imgs:
        info['images'] = len([l for l in imgs.split('\n') if l])

    nets = _safe_run(['docker', 'network', 'ls', '-q'], timeout=5)
    if nets:
        info['networks'] = len([l for l in nets.split('\n') if l])

    vols = _safe_run(['docker', 'volume', 'ls', '--format', '{{.Name}}'], timeout=5)
    if vols:
        names = [v.strip() for v in vols.split('\n') if v.strip()]
        info['volume_names'] = names
        info['volumes'] = len(names)

    _docker_info_cache = info
    _docker_info_time = now
    return info


def _get_alerts(containers, sys_data):
    """Generate alert messages."""
    alerts = []

    for c in containers:
        if not c['running']:
            alerts.append(f"{c['name']} DOWN")

    for c in containers:
        try:
            cpu_num = float(c.get('cpu', '-').replace('%', ''))
            if cpu_num > 80:
                alerts.append(f"{c['name']} CPU:{c['cpu']}")
        except (ValueError, TypeError):
            pass

    if sys_data['disk_percent'] >= 90:
        alerts.append(f"Disk CRITICAL {sys_data['disk_percent']}%")
    elif sys_data['disk_percent'] >= 80:
        alerts.append(f"Disk warn {sys_data['disk_percent']}%")

    if sys_data['ram_percent'] >= 90:
        alerts.append(f"RAM CRITICAL {sys_data['ram_percent']}%")
    elif sys_data['ram_percent'] >= 80:
        alerts.append(f"RAM warn {sys_data['ram_percent']}%")

    if sys_data['cpu'] >= 90:
        alerts.append(f"CPU CRITICAL {sys_data['cpu']:.0f}%")

    return alerts


def _get_network():
    """Get network interface speeds."""
    global _prev_net, _prev_net_time
    now = time.time()

    try:
        counters = psutil.net_io_counters(pernic=True)
        stats = psutil.net_if_stats()
    except Exception:
        return {'interfaces': [], 'total_up': 0, 'total_down': 0}

    interfaces = []
    total_up = 0
    total_down = 0

    if _prev_net and (now - _prev_net_time) >= 0.5:
        elapsed = now - _prev_net_time
        for name, cnt in counters.items():
            if name.lower() in ('lo', 'loopback'):
                continue
            is_up = name in stats and stats[name].isup
            if name in _prev_net:
                prev = _prev_net[name]
                up = max(0, (cnt.bytes_sent - prev.bytes_sent) / elapsed)
                down = max(0, (cnt.bytes_recv - prev.bytes_recv) / elapsed)
                if is_up or up > 0 or down > 0:
                    interfaces.append({
                        'name': name,
                        'up': round(up, 1),
                        'down': round(down, 1),
                        'active': is_up
                    })
                    total_up += up
                    total_down += down

    _prev_net = counters
    _prev_net_time = now

    # Sort: active first, then by name
    interfaces.sort(key=lambda x: (not x['active'], x['name']))

    return {
        'interfaces': interfaces[:8],
        'total_up': round(total_up, 1),
        'total_down': round(total_down, 1)
    }


def _format_speed(bps):
    """Format bytes/sec to human-readable."""
    if bps >= 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    if bps >= 1024:
        return f"{bps / 1024:.1f} KB/s"
    return f"{bps:.0f} B/s"


@bp.route('/dashboard')
@require_permission('dashboard.read')
def get_dashboard():
    containers = _get_containers()
    sys_data = _get_system()
    docker_info = _get_docker_info()
    alerts = _get_alerts(containers, sys_data)
    network = _get_network()

    return jsonify({
        'containers': containers,
        'system': sys_data,
        'docker': docker_info,
        'alerts': alerts,
        'network': network,
        'timestamp': time.time()
    })


@bp.route('/dashboard/stream')
@require_permission('dashboard.read')
def dashboard_stream():
    def generate():
        # Prime psutil CPU (first call always returns 0)
        psutil.cpu_percent(interval=None)
        time.sleep(0.1)

        while True:
            try:
                containers = _get_containers()
                sys_data = _get_system()
                docker_info = _get_docker_info()
                alerts = _get_alerts(containers, sys_data)
                network = _get_network()

                data = json.dumps({
                    'containers': containers,
                    'system': sys_data,
                    'docker': docker_info,
                    'alerts': alerts,
                    'network': network,
                    'timestamp': time.time()
                })

                yield f"data: {data}\n\n"
            except GeneratorExit:
                return
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

            time.sleep(3)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )
