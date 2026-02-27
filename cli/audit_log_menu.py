# ORCHIX v1.4
import json
from cli.ui import select_from_list, show_panel, show_info, show_warning, show_error
from license import get_license_manager
from license.audit_logger import get_audit_logger, AuditEventType
from rich.table import Table
from rich.console import Console
from datetime import datetime
from config import ORCHIX_CONFIG_DIR

AUDIT_CONFIG_FILE = ORCHIX_CONFIG_DIR / '.orchix_audit_config.json'


def _get_retention_days() -> int:
    """Read saved retention period (days). Default 90."""
    try:
        if AUDIT_CONFIG_FILE.exists():
            data = json.loads(AUDIT_CONFIG_FILE.read_text(encoding='utf-8'))
            return int(data.get('retention_days', 90))
    except Exception:
        pass
    return 90


def _save_retention_days(days: int):
    """Persist retention period selection."""
    AUDIT_CONFIG_FILE.write_text(
        json.dumps({'retention_days': days}, indent=2), encoding='utf-8'
    )


def _get_log_stats(audit_logger):
    """Return (count, oldest_days) for current audit log."""
    events = audit_logger.get_recent_events(limit=100000)
    if not events:
        return 0, 0
    # get_recent_events returns newest-first; oldest is last
    oldest_ts = events[-1].get('timestamp', '')
    try:
        oldest_dt = datetime.fromisoformat(oldest_ts)
        days = (datetime.now() - oldest_dt).days
    except Exception:
        days = 0
    return len(events), days


def show_audit_log_menu():
    """Show audit log menu (PRO only)"""

    # Check license
    license_manager = get_license_manager()
    if not license_manager.is_pro():
        show_warning("🔒 Audit Logs require PRO license!")
        input("Press Enter...")
        return

    # Initialize audit logger for PRO users
    audit_logger = get_audit_logger(enabled=True)

    while True:
        count, oldest_days = _get_log_stats(audit_logger)
        retention = _get_retention_days()
        if count > 0:
            days_left = max(0, retention - oldest_days)
            if days_left == 0:
                stats_str = f"{count} entries | deletion overdue!"
            else:
                stats_str = f"{count} entries | {days_left}d until oldest deleted"
        else:
            stats_str = "no logs"

        show_panel("Audit Log Manager", f"View system activity and user actions  |  {stats_str}")

        choices = [
            "📊 View Recent Events",
            "👤 View User Activity",
            "🔍 Filter by App",
            "🧹 Clear Old Logs",
            "⬅️  Back to Main Menu"
        ]

        choice = select_from_list("Select option", choices)
        
        if "Recent Events" in choice:
            _show_recent_events(audit_logger)
        elif "User Activity" in choice:
            _show_user_activity(audit_logger)
        elif "Filter by App" in choice:
            _show_app_events(audit_logger)
        elif "Clear Old" in choice:
            _clear_old_logs(audit_logger)
        elif "Back" in choice:
            break


def _show_recent_events(audit_logger, limit=50):
    """Show recent audit events"""
    show_panel("Recent Audit Events", f"Last {limit} events")
    
    events = audit_logger.get_recent_events(limit=limit)
    
    if not events:
        show_info("No audit events found")
        input("Press Enter...")
        return
    
    # Create table
    console = Console()
    table = Table(title="Audit Events", show_header=True, header_style="bold cyan")
    table.add_column("Time", style="cyan")
    table.add_column("User", style="magenta")
    table.add_column("Event", style="yellow")
    table.add_column("App", style="green")
    table.add_column("Details", style="dim")
    
    for event in events:
        try:
            # Parse timestamp
            ts = datetime.fromisoformat(event['timestamp'])
            time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            
            # Get details
            details_str = ""
            if event.get('details'):
                details = event['details']
                if isinstance(details, dict):
                    # Show key details
                    key_details = []
                    if 'status' in details:
                        key_details.append(f"Status: {details['status']}")
                    if 'version' in details:
                        key_details.append(f"Ver: {details['version']}")
                    if 'error' in details:
                        key_details.append(f"Error: {details['error']}")
                    details_str = " | ".join(key_details) if key_details else ""
            
            table.add_row(
                time_str,
                event.get('user', 'unknown'),
                event.get('event_type', 'UNKNOWN'),
                event.get('app_name', 'system'),
                details_str
            )
        except:
            pass
    
    console.print(table)
    input("\nPress Enter to continue...")


def _show_user_activity(audit_logger):
    """Show activity for a specific user"""
    show_panel("User Activity", "View events for specific user")
    
    users = set()
    
    # Collect all users from logs
    events = audit_logger.get_recent_events(limit=1000)
    for event in events:
        users.add(event.get('user', 'unknown'))
    
    if not users:
        show_info("No audit events found")
        input("Press Enter...")
        return
    
    user_list = sorted(list(users))
    user_list.append("⬅️  Back")
    
    user = select_from_list("Select user", user_list)
    
    if "Back" in user:
        return
    
    # Get user's events
    events = audit_logger.get_user_activity(username=user, limit=50)
    
    show_panel(f"Activity for {user}", f"Found {len(events)} events")
    
    console = Console()
    table = Table(title=f"Events by {user}", show_header=True, header_style="bold cyan")
    table.add_column("Time", style="cyan")
    table.add_column("Event", style="yellow")
    table.add_column("App", style="green")
    
    for event in events:
        try:
            ts = datetime.fromisoformat(event['timestamp'])
            time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            
            table.add_row(
                time_str,
                event.get('event_type', 'UNKNOWN'),
                event.get('app_name', 'system')
            )
        except:
            pass
    
    console.print(table)
    input("\nPress Enter to continue...")


def _show_app_events(audit_logger):
    """Filter events by application"""
    show_panel("App Events Filter", "View events for specific app")
    
    apps = set()
    
    # Collect all apps from logs
    events = audit_logger.get_recent_events(limit=1000)
    for event in events:
        app = event.get('app_name', 'system')
        if app:
            apps.add(app)
    
    if not apps:
        show_info("No audit events found")
        input("Press Enter...")
        return
    
    app_list = sorted(list(apps))
    app_list.append("⬅️  Back")
    
    app = select_from_list("Select application", app_list)
    
    if "Back" in app:
        return
    
    # Get app's events
    events = audit_logger.get_recent_events(limit=50, app_name=app)
    
    show_panel(f"Events for {app}", f"Found {len(events)} events")
    
    console = Console()
    table = Table(title=f"Events for {app}", show_header=True, header_style="bold cyan")
    table.add_column("Time", style="cyan")
    table.add_column("User", style="magenta")
    table.add_column("Event", style="yellow")
    
    for event in events:
        try:
            ts = datetime.fromisoformat(event['timestamp'])
            time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            
            table.add_row(
                time_str,
                event.get('user', 'unknown'),
                event.get('event_type', 'UNKNOWN')
            )
        except:
            pass
    
    console.print(table)
    input("\nPress Enter to continue...")


def _clear_old_logs(audit_logger):
    """Clear old audit logs"""
    show_panel("Clear Old Logs", "Remove old audit entries")

    count, oldest_days = _get_log_stats(audit_logger)
    retention = _get_retention_days()
    if count > 0:
        days_left = max(0, retention - oldest_days)
        show_info(f"Total entries: {count}  |  Oldest entry: {oldest_days} days ago")
        show_info(f"Current retention: {retention} days  |  Days until oldest deleted: {days_left}")
    else:
        show_info("No log entries found.")
    print()
    show_info("Select how many days of logs to KEEP. Everything older will be deleted.")
    print()

    days_options = [
        "Keep last 30 days",
        "Keep last 90 days (default)",
        "Keep last 180 days",
        "Keep last 1 year",
        "⬅️  Cancel"
    ]

    choice = select_from_list("Select retention period", days_options)

    days_map = {
        "30": 30,
        "90": 90,
        "180": 180,
        "1 year": 365
    }

    for key, value in days_map.items():
        if key in choice:
            audit_logger.clear_old_logs(days=value)
            _save_retention_days(value)
            show_info(f"✅ Cleared logs older than {key}. Retention set to {value} days.")
            break
