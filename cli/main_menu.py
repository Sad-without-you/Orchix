from cli.backup_menu import show_backup_menu
from cli.container_menu import show_container_menu
from cli.ui import select_from_list, show_panel
from cli.install_menu import show_install_menu
from cli.update_menu import show_update_menu
from cli.uninstall_menu import show_uninstall_menu
from cli.setup_menu import show_setup_menu
from cli.audit_log_menu import show_audit_log_menu
from license import get_license_manager, FEATURE_DESCRIPTIONS, PRICING
from license.features import get_pro_benefits
from cli.license_menu import show_license_menu
import sys
from rich.console import Console
from rich.table import Table
from cli.ui import show_warning


def _show_pro_upgrade_prompt(feature_name):
    '''Show PRO upgrade prompt for locked features'''
    from cli.ui import show_panel, show_warning, show_info, select_from_list
    from license import PRICING
    from cli.license_menu import _activate_pro_license
    
    show_panel("PRO Feature Required", f"Upgrade to use {feature_name}")
    print()
    show_warning(f"{feature_name} requires a PRO license!")
    print()
    show_info("Upgrade to PRO to unlock:")
    print("  + Backup & Restore")
    print("  + Server Migration")
    print("  + Unlimited containers")
    print("  + Multi-instance support")
    print("  + PRO-exclusive apps")
    print()
    show_info(f"Price: {PRICING['currency']}{PRICING['monthly']}/{PRICING['billing']}")
    print()

    choice = select_from_list(
        "What would you like to do?",
        ["⬆️  Upgrade to PRO", "⬅️  Back to Menu"]
    )
    
    if "Upgrade" in choice:
        _activate_pro_license()


def run_main_loop():
    '''Main application loop'''

    # Initialize license manager
    license_manager = get_license_manager()

    # Check for ORCHIX updates (non-blocking, runs once)
    try:
        from utils.version_check import check_for_updates
        update_info = check_for_updates()
        if update_info and update_info.get('update_available'):
            show_warning(f"{update_info['message']}")
            show_warning("  Update: git pull && pip install -r requirements.txt")
            print()
    except Exception:
        pass

    while True:
        # Get license info
        license_info = license_manager.get_license_info()
        tier_display = license_info['tier_display']
        container_status = license_info['container_status']
        days_remaining = license_info['days_remaining']

        # Build title with license status and expiry
        if days_remaining is not None:
            if days_remaining == 0:
                title = f"Welcome to ORCHIX! | {tier_display} (expires today!)"
            elif days_remaining == 1:
                title = f"Welcome to ORCHIX! | {tier_display} (1 day left)"
            elif days_remaining <= 7:
                title = f"Welcome to ORCHIX! | {tier_display} ({days_remaining} days left ⚠️)"
            else:
                title = f"Welcome to ORCHIX! | {tier_display} ({days_remaining} days left)"
        else:
            title = f"Welcome to ORCHIX! | {tier_display}"

        subtitle = f"DevOps Container Management | Containers: {container_status['current']}/{container_status['limit']}"

        show_panel(title, subtitle)
        
        # Build menu choices - ALWAYS show all features
        choices = [
            "📊 Dashboard",
            "📦 Install Applications",
            "🔄 Update Applications",
            "🗑️  Uninstall Applications",
            "🔧 Container Management",
        ]

        # Add PRO features (with badge if FREE)
        if license_info['is_pro']:
            choices.extend([
                "💾 Backup & Restore",
                "🚀 Server Migration",
                "📝 Audit Logs"
            ])
        else:
            choices.extend([
                "💾 Backup & Restore (PRO only)",
                "🚀 Server Migration (PRO only)",
                "📝 Audit Logs (PRO only)"
            ])

        choices.extend([
            "🔑 License Manager",
            "⚙️  System Setup",
            "❌ Exit"
        ])
        
        choice = select_from_list("Main Menu", choices)
        
        if "Dashboard" in choice:
            from cli.dashboard import show_dashboard
            show_dashboard()

        elif "System Setup" in choice:
            from cli.setup_menu import show_setup_menu
            show_setup_menu()

        elif "Install Applications" in choice:
            from cli.install_menu import show_install_menu
            show_install_menu()
        
        elif "Update Applications" in choice:
            from cli.update_menu import show_update_menu
            show_update_menu()
        
        elif "Container Management" in choice:
            from cli.container_menu import show_container_menu
            show_container_menu()
        
        elif "Backup" in choice:
            # Check if PRO required
            if "(PRO only)" in choice:
                _show_pro_upgrade_prompt("Backup & Restore")
            else:
                from cli.backup_menu import show_backup_menu
                show_backup_menu()

        elif "Migration" in choice:
            # Check if PRO required
            if "(PRO only)" in choice:
                _show_pro_upgrade_prompt("Server Migration")
            else:
                from cli.migration_menu import show_migration_menu
                show_migration_menu()
        
        elif "Audit Logs" in choice:
            # Check if PRO required
            if "(PRO only)" in choice:
                _show_pro_upgrade_prompt("Audit Logs")
            else:
                show_audit_log_menu()
        
        elif "Uninstall Applications" in choice:
            from cli.uninstall_menu import show_uninstall_menu
            show_uninstall_menu()
        
        elif "License Manager" in choice:
            from cli.license_menu import show_license_menu
            show_license_menu()
        
        elif "Exit" in choice:
            print("\n👋 Goodbye!\n")
            break


def _show_upgrade_prompt(feature_name):
    '''Show upgrade prompt for locked feature'''

    console = Console()
    
    show_warning(f"PRO Feature: {FEATURE_DESCRIPTIONS.get(feature_name, 'This feature')}")
    print()

    # Clean benefits table
    table = Table(
        title="Upgrade to ORCHIX PRO",
        show_header=False,
        border_style="cyan",
        padding=(0, 1)
    )
    table.add_column("", style="green", width=50)

    for benefit in get_pro_benefits():
        table.add_row(benefit)

    # Add separator
    table.add_row("")

    # Add pricing
    table.add_row(f"[bold cyan]{PRICING['currency']}{PRICING['monthly']}/{PRICING['billing']}[/bold cyan]")
    table.add_row("[dim]https://orchix.dev/pricing[/dim]")
    
    console.print(table)
    print()
    
    input("Press Enter to continue...")