from cli.ui import select_from_list, show_panel, show_success, show_error, show_info, show_warning
from utils.docker_utils import safe_docker_run
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import subprocess

def import_timestamp():
    '''Get current timestamp for filenames'''
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_all_containers():
    '''Get ALL containers (including stopped)'''
    result = safe_docker_run(
        ['docker', 'ps', '-a', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    if result is None:
        return []
    if result.returncode == 0:
        return [c for c in result.stdout.split('\n') if c]
    return []


def get_container_status(container_name):
    '''Get container status'''
    result = safe_docker_run(
        ['docker', 'inspect', container_name, '--format', '{{.State.Status}}'],
        capture_output=True,
        text=True
    )
    if result is None:
        return 'unknown'
    if result.returncode == 0:
        return result.stdout.strip()
    return 'unknown'


def show_container_menu():
    '''Container management menu'''
    
    while True:
        show_panel("Container Management", "Manage running containers")
        
        # Get all containers
        containers = get_all_containers()
        
        if not containers:
            show_info("No containers found!")
            input("Press Enter...")
            break
        
        # Build choices with status
        choices = []
        for container in containers:
            status = get_container_status(container)
            
            if status == 'running':
                choices.append(f"🟢 {container} (running)")
            elif status == 'exited':
                choices.append(f"🔴 {container} (stopped)")
            else:
                choices.append(f"⚪ {container} ({status})")
        
        choices.append("⬅️  Back to Main Menu")
        
        # User selects container
        choice = select_from_list("Select container to manage", choices)
        
        if "Back" in choice:
            break
        
        # Extract container name
        container_name = choice.split(' ')[1]  # "🟢 n8n (running)" -> "n8n"
        
        # Show management options
        manage_container(container_name)


def manage_container(container_name):
    '''Manage a specific container'''
    
    status = get_container_status(container_name)
    
    show_panel(f"Manage {container_name}", f"Status: {status}")
    
    # Build action choices based on status
    actions = []
    
    if status == 'running':
        actions.extend([
            "⏸️  Stop Container",
            "🔄 Restart Container",
            "📝 View Logs",
            "📊 View Status"
        ])
    elif status == 'exited':
        actions.extend([
            "▶️  Start Container",
            "📝 View Logs",
            "📊 View Status"
        ])
    else:
        actions.extend([
            "🔄 Restart Container",
            "📊 View Status"
        ])
    
    actions.append("⬅️  Back")
    
    # User selects action
    choice = select_from_list(f"Action for {container_name}", actions)
    
    if "Back" in choice:
        return
    
    # Execute action
    if "Start" in choice:
        start_container(container_name)
    elif "Stop" in choice:
        stop_container(container_name)
    elif "Restart" in choice:
        restart_container(container_name)
    elif "View Logs" in choice:
        view_logs(container_name)
    elif "View Status" in choice:
        view_status(container_name)


def start_container(container_name):
    '''Start a container'''
    show_info(f"Starting {container_name}...")

    result = safe_docker_run(
        ['docker', 'start', container_name],
        capture_output=True,
        text=True
    )

    if result is None:
        show_error("Docker is not installed!")
        return

    if result.returncode == 0:
        show_success(f"{container_name} started!")
    else:
        show_error(f"Failed to start: {result.stderr}")

    input("\nPress Enter...")


def stop_container(container_name):
    '''Stop a container'''
    show_info(f"Stopping {container_name}...")

    result = safe_docker_run(
        ['docker', 'stop', container_name],
        capture_output=True,
        text=True
    )

    if result is None:
        show_error("Docker is not installed!")
        return

    if result.returncode == 0:
        show_success(f"{container_name} stopped!")
    else:
        show_error(f"Failed to stop: {result.stderr}")

    input("\nPress Enter...")


def restart_container(container_name):
    '''Restart a container'''
    show_info(f"Restarting {container_name}...")

    result = safe_docker_run(
        ['docker', 'restart', container_name],
        capture_output=True,
        text=True
    )

    if result is None:
        show_error("Docker is not installed!")
        return

    if result.returncode == 0:
        show_success(f"{container_name} restarted!")
    else:
        show_error(f"Failed to restart: {result.stderr}")

    input("\nPress Enter...")


def view_logs(container_name):
    '''View container logs'''

    console = Console()
    
    show_info(f"Fetching logs for {container_name}...")
    print()
    
    # Show last 50 lines
    result = safe_docker_run(
        ['docker', 'logs', '--tail', '50', container_name],
        capture_output=True,
        text=True
    )

    if result is None:
        show_error("Docker is not installed!")
        return

    if result.returncode == 0:
        # Show in Rich Panel
        console.print(Panel(
            result.stdout,
            title=f"📝 Logs for {container_name} (last 50 lines)",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # Ask if save to file
        print()
        save = select_from_list(
            "Save logs to file?",
            ["💾 Yes, save to file", "⬅️  No, go back"]
        )
        
        if "save" in save.lower():
            filename = f"{container_name}_logs_{import_timestamp()}.txt"
            with open(filename, 'w') as f:
                f.write(f"Logs for {container_name}\n")
                f.write("=" * 80 + "\n")
                f.write(result.stdout)
            
            show_success(f"Logs saved to: {filename}")
    else:
        show_error(f"Failed to fetch logs: {result.stderr}")
    


def view_status(container_name):
    '''View detailed container status'''
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    show_info(f"Fetching status for {container_name}...")
    print()
    
    result = safe_docker_run(
        ['docker', 'inspect', container_name],
        capture_output=True,
        text=True
    )

    if result is None:
        show_error("Docker is not installed!")
        return

    if result.returncode == 0:
        import json
        data = json.loads(result.stdout)[0]
        
        state = data['State']
        config = data['Config']
        
        # Create status table
        table = Table(title=f"📊 Status: {container_name}", show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        # Add rows
        status_emoji = "🟢" if state['Running'] else "🔴"
        table.add_row("Status", f"{status_emoji} {state['Status']}")
        table.add_row("Running", str(state['Running']))
        table.add_row("Started At", state.get('StartedAt', 'N/A')[:19])  # Trim microseconds
        table.add_row("Image", config['Image'])
        
        # Ports
        if data.get('NetworkSettings', {}).get('Ports'):
            ports_list = []
            for port, bindings in data['NetworkSettings']['Ports'].items():
                if bindings:
                    for binding in bindings:
                        ports_list.append(f"{binding['HostPort']} → {port}")
            if ports_list:
                table.add_row("Ports", "\n".join(ports_list))
        
        # Show table
        console.print()
        console.print(table)
        console.print()
    else:
        show_error(f"Failed to fetch status: {result.stderr}")
    
    input("\nPress Enter...")