# ORCHIX v1.1
from cli.ui import select_from_list, show_panel, show_info, show_warning, show_error
from license import get_license_manager
from license.audit_logger import get_audit_logger, AuditEventType
from rich.table import Table
from rich.console import Console
from datetime import datetime


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
        show_panel("Audit Log Manager", "View system activity and user actions")
        
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
    
    show_info("By default, logs older than 90 days will be kept.")
    show_info("Recent logs will be preserved.")
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
            show_info(f"✅ Cleared logs older than {key}")
            break
