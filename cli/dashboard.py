import os
import sys
import platform
import shutil
import curses
import time
import collections
from datetime import datetime

import psutil

from utils.docker_utils import safe_docker_run, check_docker_status
from cli.ui import show_error

IS_WINDOWS = platform.system().lower() == 'windows'

REFRESH_INTERVAL = 3
DOCKER_INFO_TTL = 30

_docker_info_cache = None
_docker_info_time = 0

_prev_net_per_nic = None
_prev_net_per_nic_time = 0
_net_history = collections.deque(maxlen=60)
_net_iface_idx = 0

GRAPH_HEIGHT = 4
GRAPH_BLOCKS = ' ▁▂▃▄▅▆▇█'

# Prime psutil CPU
psutil.cpu_percent(interval=None)


def show_dashboard():
    """Entry point — checks Docker, then launches curses dashboard."""
    status = check_docker_status()
    if not status['installed']:
        show_error(status['message'])
        input("\nPress Enter...")
        return
    if not status['running']:
        show_error(status['message'])
        input("\nPress Enter...")
        return

    curses.wrapper(_curses_main)


def _curses_main(stdscr):
    """Main curses loop."""
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(REFRESH_INTERVAL * 1000)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_WHITE, -1)
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_CYAN)

    while True:
        try:
            stdscr.erase()
            _draw_dashboard(stdscr)
            stdscr.refresh()
        except curses.error:
            pass

        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('r'), ord('R')):
            continue
        elif key in (ord('n'), ord('N')):
            global _net_iface_idx
            _net_iface_idx += 1
        elif key == curses.KEY_RESIZE:
            stdscr.clear()


def _draw_dashboard(stdscr):
    """Draw the full dashboard onto the curses screen."""
    max_y, max_x = stdscr.getmaxyx()
    if max_y < 10 or max_x < 40:
        stdscr.addstr(0, 0, "Terminal too small!")
        return

    containers = _get_container_data()
    sys_data = _get_system_data()
    docker_info = _get_docker_info_cached()
    net_speeds = _update_net_history()
    sys_data['net_up'] = sum(s['up'] for s in net_speeds.values())
    sys_data['net_down'] = sum(s['down'] for s in net_speeds.values())
    alerts = _get_alerts(containers, sys_data)

    now = datetime.now().strftime("%H:%M:%S")
    running = sum(1 for c in containers if c['running'])
    total = len(containers)

    row = 0
    CP = curses.color_pair

    # === HEADER ===
    header = f" ORCHIX Dashboard  {now}  Containers: {running}/{total} "
    header = header.center(max_x)
    _safe_addstr(stdscr, row, 0, header, CP(6) | curses.A_BOLD)
    row += 2

    # === SYSTEM ===
    _safe_addstr(stdscr, row, 1, "SYSTEM  ", CP(1) | curses.A_BOLD)
    col = 10
    col = _draw_metric(stdscr, row, col, "CPU", sys_data['cpu'], 100,
                        f"{sys_data['cpu']:.0f}%", max_x)
    col = _draw_metric(stdscr, row, col, "RAM", sys_data['ram_percent'], 100,
                        f"{sys_data['ram_used']:.1f}/{sys_data['ram_total']:.1f}GB", max_x)
    col = _draw_metric(stdscr, row, col, "Disk", sys_data['disk_percent'], 100,
                        f"{sys_data['disk_used']}/{sys_data['disk_total']}GB", max_x)
    row += 2

    # === DOCKER ===
    _safe_addstr(stdscr, row, 1, "DOCKER  ", CP(1) | curses.A_BOLD)
    info_str = (
        f"Engine: {docker_info['version']}  "
        f"Images: {docker_info['images']}  "
        f"Volumes: {docker_info['volumes']}  "
        f"Networks: {docker_info['networks']}"
    )
    _safe_addstr(stdscr, row, 10, info_str, CP(1))
    row += 2

    # === CONTAINER TABLE ===
    _safe_addstr(stdscr, row, 1, "CONTAINERS", CP(1) | curses.A_BOLD)
    row += 1

    col_w = _col_widths(max_x)
    hdr_parts = ["#", "Container", "Status", "CPU", "Memory", "Net I/O", "Ports", "Image"]
    _draw_table_row(stdscr, row, 1, hdr_parts, col_w, CP(1) | curses.A_BOLD)
    row += 1
    _safe_addstr(stdscr, row, 1, "─" * min(max_x - 2, sum(col_w) + len(col_w) * 2), CP(5))
    row += 1

    if containers:
        for i, c in enumerate(containers, 1):
            if row >= max_y - 5:
                _safe_addstr(stdscr, row, 3, f"... +{total - i + 1} more", CP(5))
                row += 1
                break

            if c['running']:
                status_str = f"UP {c['uptime']}"
                s_color = CP(2)
            else:
                status_str = "DOWN"
                s_color = CP(4) | curses.A_BOLD

            cpu_val = c.get('cpu', '-')
            cpu_color = _value_color(cpu_val)

            parts = [
                str(i),
                _trunc(c['name'], col_w[1]),
                _trunc(status_str, col_w[2]),
                cpu_val,
                _trunc(c.get('memory', '-'), col_w[4]),
                _trunc(c.get('net_io', '-'), col_w[5]),
                _trunc(c.get('ports', '-'), col_w[6]),
                _trunc(c.get('image', '-'), col_w[7]),
            ]

            # per-column colors: default white, status colored, cpu colored
            colors = [CP(5)] * 8
            colors[1] = CP(1)     # container name = cyan
            colors[2] = s_color   # status
            colors[3] = cpu_color # cpu

            _draw_table_row(stdscr, row, 1, parts, col_w, CP(5), colors)
            row += 1
    else:
        _safe_addstr(stdscr, row, 3, "No containers", CP(5))
        row += 1

    row += 1

    # === VOLUMES ===
    volumes = docker_info.get('volume_names', [])
    _safe_addstr(stdscr, row, 1, "VOLUMES ", CP(1) | curses.A_BOLD)
    if volumes:
        vol_str = ", ".join(volumes[:6])
        if len(volumes) > 6:
            vol_str += f" (+{len(volumes) - 6} more)"
        _safe_addstr(stdscr, row, 10, vol_str[:max_x - 12], CP(5))
    else:
        _safe_addstr(stdscr, row, 10, "None", CP(5))
    row += 2

    # === NETWORK GRAPH ===
    row = _draw_net_section(stdscr, row, max_x, max_y, net_speeds)

    # === ALERTS ===
    if alerts:
        _safe_addstr(stdscr, row, 1, "ALERTS  ", CP(3) | curses.A_BOLD)
        alert_str = "  ".join(alerts)
        _safe_addstr(stdscr, row, 10, alert_str[:max_x - 12], CP(3))
    else:
        _safe_addstr(stdscr, row, 1, "STATUS  ", CP(2) | curses.A_BOLD)
        _safe_addstr(stdscr, row, 10, "All systems healthy", CP(2))
    row += 2

    # === FOOTER ===
    if row < max_y:
        footer = " [Q] Quit   [R] Refresh   [N] Switch   Auto-refresh: 3s"
        _safe_addstr(stdscr, row, 1, footer, CP(5))


def _safe_addstr(stdscr, y, x, text, attr=0):
    """addstr that won't crash at screen edges."""
    max_y, max_x = stdscr.getmaxyx()
    if y >= max_y or x >= max_x:
        return
    try:
        stdscr.addnstr(y, x, text, max_x - x - 1, attr)
    except curses.error:
        pass


def _draw_metric(stdscr, row, col, label, value, max_val, text, max_x):
    """Draw: 'CPU [####--------] 23%' """
    CP = curses.color_pair
    bar_w = 12
    ratio = min(value / max_val, 1.0) if max_val > 0 else 0
    filled = int(ratio * bar_w)
    color = CP(2) if value < 70 else CP(3) if value < 90 else CP(4)

    _safe_addstr(stdscr, row, col, f"{label} ", CP(5))
    col += len(label) + 1
    _safe_addstr(stdscr, row, col, "[", CP(5))
    col += 1
    _safe_addstr(stdscr, row, col, "#" * filled, color | curses.A_BOLD)
    col += filled
    _safe_addstr(stdscr, row, col, "-" * (bar_w - filled), CP(5))
    col += bar_w - filled
    _safe_addstr(stdscr, row, col, "] ", CP(5))
    col += 2
    _safe_addstr(stdscr, row, col, text, color)
    col += len(text) + 2
    return col


def _col_widths(max_x):
    """Column widths for the container table, adapting to terminal width."""
    if max_x >= 110:
        return [3, 18, 12, 7, 16, 14, 8, 14]
    elif max_x >= 80:
        return [3, 14, 10, 7, 14, 12, 6, 10]
    else:
        return [3, 10, 8, 6, 10, 8, 5, 8]


def _draw_table_row(stdscr, row, start_x, parts, widths, default_attr, colors=None):
    """Draw a table row with per-column widths and optional per-column colors."""
    col = start_x
    for i, (text, w) in enumerate(zip(parts, widths)):
        attr = colors[i] if colors else default_attr
        padded = text.ljust(w) if i > 0 else text.rjust(w)
        _safe_addstr(stdscr, row, col, padded, attr)
        col += w + 2  # 2 space gap


def _trunc(text, maxlen):
    """Truncate text with ellipsis."""
    if not text:
        return "-"
    if len(text) <= maxlen:
        return text
    return text[:maxlen - 1] + "…"


def _value_color(val):
    """Return color pair for a percentage value."""
    CP = curses.color_pair
    try:
        num = float(val.replace('%', ''))
        if num >= 90:
            return CP(4) | curses.A_BOLD
        if num >= 70:
            return CP(3)
        return CP(2)
    except (ValueError, AttributeError):
        return CP(5)


def _get_container_data():
    """Get container list with status and resource usage."""
    containers = []

    result = safe_docker_run(
        ['docker', 'ps', '-a', '--format',
         '{{.Names}}|{{.Status}}|{{.Ports}}|{{.Image}}'],
        capture_output=True, text=True,
    )
    if not result or result.returncode != 0:
        return containers

    for line in result.stdout.strip().split('\n'):
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
        uptime = _parse_uptime(status_raw) if running else ''

        containers.append({
            'name': name,
            'status': status_raw,
            'running': running,
            'uptime': uptime,
            'ports': _parse_ports(ports_raw),
            'image': image,
            'cpu': '-', 'memory': '-', 'net_io': '-',
        })

    stats_result = safe_docker_run(
        ['docker', 'stats', '--no-stream', '--format',
         '{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}'],
        capture_output=True, text=True,
    )
    if stats_result and stats_result.returncode == 0:
        stats_map = {}
        for line in stats_result.stdout.strip().split('\n'):
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


def _parse_uptime(status):
    """Parse Docker status to short uptime string."""
    text = status.replace('Up ', '').strip()
    if '(' in text:
        text = text[:text.index('(')].strip()

    low = text.lower()

    if low.startswith('about'):
        if 'minute' in low:
            return '~1m'
        if 'hour' in low:
            return '~1h'
        return '~?'

    if low.startswith('less'):
        return '<1s'

    _UNITS = {
        'second': 's', 'minute': 'm', 'hour': 'h',
        'day': 'd', 'week': 'w', 'month': 'mo',
    }
    for keyword, suffix in _UNITS.items():
        if keyword in low:
            first = text.split()[0]
            if first.isdigit():
                return f"{first}{suffix}"
            return f"?{suffix}"

    return text[:6]


def _parse_ports(ports_raw):
    """Parse Docker port mappings to readable format."""
    if not ports_raw:
        return '-'
    host_ports = []
    for mapping in ports_raw.split(', '):
        if '->' in mapping:
            host_part = mapping.split('->')[0]
            port = host_part.split(':')[-1] if ':' in host_part else host_part
            if port and port not in host_ports:
                host_ports.append(port)
    return ', '.join(host_ports) if host_ports else '-'


def _get_system_data():
    """Get system resource metrics."""
    cpu_percent = psutil.cpu_percent(interval=0)
    mem = psutil.virtual_memory()

    disk_root = 'C:\\' if IS_WINDOWS else '/'
    try:
        total, used, free = shutil.disk_usage(disk_root)
    except OSError:
        total, used, free = 1, 0, 1

    return {
        'cpu': cpu_percent,
        'ram_total': mem.total / (1024 ** 3),
        'ram_used': mem.used / (1024 ** 3),
        'ram_percent': mem.percent,
        'disk_total': total // (2 ** 30),
        'disk_used': used // (2 ** 30),
        'disk_free': free // (2 ** 30),
        'disk_percent': int((used / total) * 100) if total else 0,
    }


#  Network monitoring — per-interface tracking, history & graph

def _get_net_interfaces():
    """Get list of network interface names, active ones first."""
    try:
        counters = psutil.net_io_counters(pernic=True)
    except Exception:
        return []
    try:
        stats = psutil.net_if_stats()
    except Exception:
        stats = {}

    active, inactive = [], []
    for name in sorted(counters.keys()):
        if name.lower() in ('lo', 'loopback'):
            continue
        if name in stats and stats[name].isup:
            active.append(name)
        else:
            inactive.append(name)
    result = active + inactive
    return result if result else sorted(counters.keys())


def _update_net_history():
    """Compute per-interface speeds and append to history. Returns current speeds dict."""
    global _prev_net_per_nic, _prev_net_per_nic_time
    now = time.time()
    try:
        current = psutil.net_io_counters(pernic=True)
    except Exception:
        return {}

    speeds = {}
    if _prev_net_per_nic is not None and (now - _prev_net_per_nic_time) >= 0.1:
        elapsed = now - _prev_net_per_nic_time
        for name, cnt in current.items():
            if name in _prev_net_per_nic:
                prev = _prev_net_per_nic[name]
                speeds[name] = {
                    'up': max(0, (cnt.bytes_sent - prev.bytes_sent) / elapsed),
                    'down': max(0, (cnt.bytes_recv - prev.bytes_recv) / elapsed),
                }

    _prev_net_per_nic = current
    _prev_net_per_nic_time = now

    if speeds:
        _net_history.append(speeds)
    return speeds


def _draw_net_section(stdscr, row, max_x, max_y, net_speeds):
    """Draw the network status section with live traffic graph."""
    global _net_iface_idx
    CP = curses.color_pair

    interfaces = _get_net_interfaces()
    if not interfaces:
        _safe_addstr(stdscr, row, 1, "NETWORK ", CP(1) | curses.A_BOLD)
        _safe_addstr(stdscr, row, 10, "No active interfaces", CP(5))
        return row + 2

    _net_iface_idx = _net_iface_idx % len(interfaces)
    iface = interfaces[_net_iface_idx]

    cur_up = net_speeds.get(iface, {}).get('up', 0)
    cur_down = net_speeds.get(iface, {}).get('down', 0)

    # --- Header ---
    _safe_addstr(stdscr, row, 1, "NETWORK ", CP(1) | curses.A_BOLD)
    _safe_addstr(stdscr, row, 10, iface, CP(5) | curses.A_BOLD)
    row += 1

    # --- Build graph data ---
    graph_w = min(max_x - 10, 60)
    up_vals, down_vals = [], []
    for entry in _net_history:
        d = entry.get(iface, {'up': 0, 'down': 0})
        up_vals.append(d['up'])
        down_vals.append(d['down'])
    if len(up_vals) > graph_w:
        up_vals = up_vals[-graph_w:]
        down_vals = down_vals[-graph_w:]

    # Auto-scale Y axis
    peak = max(up_vals + down_vals) if (up_vals or down_vals) else 0
    max_scale = _nice_scale(peak)

    # --- Draw graph rows ---
    g_col = 7  # graph content starts here

    for gr in range(GRAPH_HEIGHT):
        # Y-axis label (top and bottom only)
        if gr == 0:
            label = _format_speed_short(max_scale)
            _safe_addstr(stdscr, row, 1, f"{label:>5}", CP(5))
        elif gr == GRAPH_HEIGHT - 1:
            _safe_addstr(stdscr, row, 1, "    0", CP(5))

        _safe_addstr(stdscr, row, g_col - 1, "│", CP(5))

        for i in range(len(up_vals)):
            x = g_col + i
            if x >= max_x - 1:
                break
            up_bl = _block_level(up_vals[i], max_scale, gr)
            down_bl = _block_level(down_vals[i], max_scale, gr)

            if down_bl >= up_bl and down_bl > 0:
                _safe_addstr(stdscr, row, x, GRAPH_BLOCKS[down_bl], CP(1))
            elif up_bl > 0:
                _safe_addstr(stdscr, row, x, GRAPH_BLOCKS[up_bl], CP(2))
        row += 1

    # --- Speed indicators ---
    up_str = f" ↑ {_format_speed(cur_up)}"
    down_str = f" ↓ {_format_speed(cur_down)}"
    _safe_addstr(stdscr, row, g_col, up_str, CP(2) | curses.A_BOLD)
    _safe_addstr(stdscr, row, g_col + len(up_str) + 2, down_str, CP(1) | curses.A_BOLD)
    row += 2
    return row


def _block_level(value, max_scale, graph_row):
    """Get block character index (0-8) for a value at a given graph row."""
    if max_scale <= 0 or value <= 0:
        return 0
    total_sub = GRAPH_HEIGHT * 8
    val_sub = min(int(value / max_scale * total_sub), total_sub)

    row_from_bottom = GRAPH_HEIGHT - 1 - graph_row
    row_start = row_from_bottom * 8
    row_end = row_start + 8

    if val_sub >= row_end:
        return 8  # full block
    if val_sub <= row_start:
        return 0  # empty
    return val_sub - row_start  # partial 1-7


def _nice_scale(peak):
    """Round peak up to a clean Y-axis maximum."""
    if peak <= 0:
        return 1024  # 1 KB/s minimum
    for t in (1024, 5*1024, 10*1024, 50*1024, 100*1024, 500*1024,
              1024**2, 5*1024**2, 10*1024**2, 50*1024**2, 100*1024**2,
              500*1024**2, 1024**3):
        if peak <= t:
            return t
    return peak


def _format_speed(bytes_per_sec):
    """Format bytes/sec to human-readable string."""
    if bytes_per_sec >= 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"
    if bytes_per_sec >= 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    return f"{bytes_per_sec:.0f} B/s"


def _format_speed_short(bps):
    """Compact speed label for Y-axis."""
    if bps >= 1024 * 1024 * 1024:
        return f"{bps / (1024**3):.0f}G"
    if bps >= 1024 * 1024:
        return f"{bps / (1024**2):.0f}M"
    if bps >= 1024:
        return f"{bps / 1024:.0f}K"
    return f"{bps:.0f}"


def _get_docker_info_cached():
    """Get Docker info with caching."""
    global _docker_info_cache, _docker_info_time
    now = time.time()
    if _docker_info_cache and (now - _docker_info_time) < DOCKER_INFO_TTL:
        return _docker_info_cache
    _docker_info_cache = _get_docker_info()
    _docker_info_time = now
    return _docker_info_cache


def _get_docker_info():
    """Get Docker daemon info."""
    info = {
        'version': '?', 'images': 0,
        'volumes': 0, 'networks': 0,
        'volume_names': [],
    }

    result = safe_docker_run(
        ['docker', 'version', '--format', '{{.Server.Version}}'],
        capture_output=True, text=True,
    )
    if result and result.returncode == 0:
        info['version'] = f"v{result.stdout.strip()}"

    result = safe_docker_run(
        ['docker', 'images', '-q'], capture_output=True, text=True,
    )
    if result and result.returncode == 0:
        info['images'] = len([l for l in result.stdout.strip().split('\n') if l])

    result = safe_docker_run(
        ['docker', 'network', 'ls', '-q'], capture_output=True, text=True,
    )
    if result and result.returncode == 0:
        info['networks'] = len([l for l in result.stdout.strip().split('\n') if l])

    result = safe_docker_run(
        ['docker', 'volume', 'ls', '--format', '{{.Name}}'],
        capture_output=True, text=True,
    )
    if result and result.returncode == 0:
        names = [v.strip() for v in result.stdout.strip().split('\n') if v.strip()]
        info['volume_names'] = names
        info['volumes'] = len(names)

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

    # Network alerts: high bandwidth (>100 MB/s)
    if sys_data.get('net_up', 0) > 100 * 1024 * 1024:
        alerts.append(f"Net Upload HIGH {_format_speed(sys_data['net_up'])}")
    if sys_data.get('net_down', 0) > 100 * 1024 * 1024:
        alerts.append(f"Net Download HIGH {_format_speed(sys_data['net_down'])}")

    return alerts