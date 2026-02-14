# ORCHIX v1.2
from cli.ui import show_panel, select_from_list, show_info, show_success, show_error, show_warning
from license import get_license_manager, PRICING
from license.features import get_pro_benefits
from rich.console import Console
from rich.table import Table
    

def show_license_menu():
    '''License management menu'''
    console = Console()
    license_manager = get_license_manager()
    
    while True:
        info = license_manager.get_license_info()
        
        show_panel("License Manager", f"Current Tier: {info['tier_display']}")
        
        table = Table(title="License Information", show_header=True, header_style="bold cyan")
        table.add_column("Feature", style="cyan", width=30)
        table.add_column("Status", style="white", width=30)

        table.add_row("Tier", info['tier_display'])

        # Show license key and expiry for PRO users
        if license_manager.is_pro() and info.get('license_key'):
            # Mask the license key for security (show first and last 4 chars)
            key = info['license_key']
            if len(key) > 20:
                masked_key = f"{key[:12]}...{key[-8:]}"
            else:
                masked_key = key

            table.add_row("License Key", masked_key)

            # Show expiry information
            if info.get('days_remaining') is not None:
                days = info['days_remaining']
                if days == 0:
                    expiry_text = "⚠️ Expires today!"
                elif days == 1:
                    expiry_text = "⚠️ 1 day remaining"
                elif days <= 7:
                    expiry_text = f"⚠️ {days} days remaining"
                elif days <= 30:
                    expiry_text = f"{days} days remaining"
                else:
                    expiry_text = f"{days} days remaining"
            else:
                expiry_text = "♾️ Never expires"

            table.add_row("License Expiry", expiry_text)

        table.add_row("Containers", f"{info['container_status']['current']}/{info['container_status']['limit']}")
        table.add_row("Backup & Restore", "✅ Enabled" if info['features']['backup_restore'] else "❌ Disabled")
        table.add_row("Multi-Instance", "✅ Enabled" if info['features']['multi_instance'] else "❌ Disabled")
        table.add_row("Server Migration", "✅ Enabled" if info['features'].get('migration', False) else "❌ Disabled")
        table.add_row("Audit Logging", "✅ Enabled" if info['features'].get('audit_log', False) else "❌ Disabled")

        # Dynamically add PRO-only apps
        from apps.manifest_loader import load_all_manifests
        manifests = load_all_manifests()

        pro_apps = []
        for manifest in manifests.values():
            if manifest.get('license_required') == 'pro':
                icon = manifest.get('icon', '🔒')
                display_name = manifest.get('display_name', manifest['name'])
                pro_apps.append(f"{icon} {display_name}")

        # Add PRO apps to table
        if pro_apps:
            table.add_row("", "")  # Empty separator
            for app in pro_apps:
                if license_manager.is_pro():
                    table.add_row(app, "✅ Available")
                else:
                    table.add_row(app, "🔒 Locked (PRO only)")

        print()
        console.print(table)
        print()
        
        # Show what FREE users can unlock
        if license_manager.is_free():
            unlock_table = Table(
                title="Unlock with PRO",
                show_header=False,
                border_style="yellow",
                padding=(0, 1)
            )
            unlock_table.add_column("Feature", style="yellow", width=60)

            # Core PRO features
            unlock_table.add_row("+ Backup & Restore - Protect your data")
            unlock_table.add_row("+ Multi-Instance - Run multiple instances per app")
            unlock_table.add_row("+ Unlimited Containers - No 3 container limit")
            unlock_table.add_row("+ Server Migration - Migrate to other servers")
            unlock_table.add_row("+ Audit Logging - Track user actions and changes")
            unlock_table.add_row("+ Priority Support - Get help faster")
            
            # Dynamically add PRO-only apps
            from apps.manifest_loader import load_all_manifests
            manifests = load_all_manifests()
            
            pro_apps = []
            for manifest in manifests.values():
                if manifest.get('license_required') == 'pro':
                    icon = manifest.get('icon', '🔒')
                    display_name = manifest.get('display_name', manifest['name'])
                    description = manifest.get('description', '')
                    pro_apps.append(f"{icon} {display_name} - {description}")
            
            # Add separator if we have PRO apps
            if pro_apps:
                unlock_table.add_row("")  # Empty row as separator
                unlock_table.add_row("[bold]PRO-Exclusive Applications:[/bold]")
                for app in pro_apps:
                    unlock_table.add_row(app)
            
            console.print(unlock_table)
            print()
            
            # Pricing highlight
            from license import PRICING
            pricing_info = f"[bold cyan]Price: {PRICING['currency']}{PRICING['monthly']}/{PRICING['billing']}[/bold cyan]"
            console.print(pricing_info, justify="center")
            print()
        
        # Menu choices
        choices = []
        
        if license_manager.is_free():
            choices.append("⬆️  Upgrade to PRO")
        else:
            choices.extend([
                "📄 View License Details",
                "🔒 Deactivate License",
            ])

        choices.append("⬅️  Back to Main Menu")
        
        choice = select_from_list("License Options", choices)
        
        if "Upgrade to PRO" in choice:
            _activate_pro_license()
        
        elif "View License Details" in choice:
            _show_license_details()
        
        elif "Deactivate License" in choice:
            _deactivate_license()
        
        elif "Back" in choice:
            break


def _activate_pro_license():
    '''Activate PRO license'''
    
    show_panel("Activate PRO License", "Enter your license key")
    
    print()
    show_info("Purchase a license key at: https://orchix.dev/pricing")
    print()
    
    license_key = input("Enter license key (or 'cancel' to abort): ").strip()
    
    if license_key.lower() == 'cancel':
        show_info("Activation cancelled")
        input("\nPress Enter...")
        return
    
    print()
    show_info("Activating license...")
    
    license_manager = get_license_manager()
    
    if license_manager.activate_pro(license_key):
        print()
        show_success("PRO License activated!")
        print()
        show_info("You now have access to:")
        for benefit in get_pro_benefits():
            if benefit:  # skip empty separator lines
                print(f"  {benefit}")
        print()
    else:
        print()
        show_error("Invalid license key!")
        show_info("Please check your key and try again.")
        print()
    
    input("Press Enter...")


def _show_license_details():
    '''Show detailed license information'''
    
    console = Console()
    
    license_manager = get_license_manager()
    info = license_manager.get_license_info()
    
    show_panel("License Details", "Your PRO License Information")
    
    # Features Table
    table = Table(title="Enabled Features", show_header=True, header_style="bold cyan")
    table.add_column("Feature", style="cyan", width=30)
    table.add_column("Status", style="white", width=30)
    
    table.add_row("Tier", info['tier_display'])
    table.add_row("Max Containers", f"{info['features']['max_containers']} (unlimited)")
    table.add_row("Backup & Restore", "✅ Enabled" if info['features']['backup_restore'] else "❌ Disabled")
    table.add_row("Multi-Instance", "✅ Enabled" if info['features']['multi_instance'] else "❌ Disabled")
    table.add_row("Audit Logging", "✅ Enabled" if info['features'].get('audit_log', False) else "❌ Disabled")
    
    print()
    console.print(table)
    print()
    
    # Usage Table
    usage_table = Table(title="Current Usage", show_header=True, header_style="bold green")
    usage_table.add_column("Metric", style="cyan", width=30)
    usage_table.add_column("Value", style="white", width=30)
    
    usage_table.add_row("Active Containers", str(info['container_status']['current']))
    usage_table.add_row("Container Limit", str(info['container_status']['limit']))
    usage_table.add_row("Remaining Slots", str(info['container_status']['remaining']))
    
    console.print(usage_table)
    print()
    
    input("Press Enter...")

def _deactivate_license():
    '''Deactivate PRO license'''
    
    show_warning("  Deactivate PRO License")
    print()
    show_info("This will:")
    print("  • Revert to FREE tier")
    print("  • Disable Backup & Restore")
    print("  • Limit containers to 3")
    print()
    
    confirm = select_from_list(
        "Are you sure?",
        ["❌ Yes, deactivate", "⬅️  Cancel"]
    )
    
    if "Cancel" in confirm:
        show_info("Deactivation cancelled")
        input("\nPress Enter...")
        return
    
    license_manager = get_license_manager()
    
    if license_manager.deactivate():
        show_success("License deactivated")
        show_info("You are now on the FREE tier")

        # Check if container selection is needed after downgrade
        if license_manager.needs_container_selection():
            print()
            from cli.container_menu import get_all_containers, _prompt_container_selection
            all_containers = get_all_containers()
            _prompt_container_selection(all_containers, license_manager.get_container_limit())
    else:
        show_error("Failed to deactivate license")

    print()
    input("Press Enter...")