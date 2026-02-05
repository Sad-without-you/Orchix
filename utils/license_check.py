# ORCHIX v1.1
'''Centralized license checking for apps'''

from license import get_license_manager, PRICING


def can_install_app(manifest):
    '''Check if user can install this app based on license'''
    license_manager = get_license_manager()
    license_required = manifest.get('license_required', None)
    
    # No license requirement - always allowed
    if not license_required:
        return {
            'allowed': True,
            'reason': None,
            'upgrade_required': False
        }
    
    # Check if user has required license
    if license_required == 'pro':
        if license_manager.is_free():
            return {
                'allowed': False,
                'reason': f"This app requires a PRO license",
                'upgrade_required': True
            }
    
    # License requirement met
    return {
        'allowed': True,
        'reason': None,
        'upgrade_required': False
    }


def get_app_badge(manifest):
    '''Get badge string for app based on license requirement'''
    license_manager = get_license_manager()
    license_required = manifest.get('license_required', None)
    
    if not license_required:
        return ""
    
    if license_required == 'pro' and license_manager.is_free():
        return " (PRO only)"
    
    return ""


def show_upgrade_prompt_for_app(manifest):
    '''Show upgrade prompt when trying to install PRO-only app'''
    from cli.ui import show_panel, show_warning, show_info, select_from_list
    from cli.license_menu import _activate_pro_license
    
    show_panel("PRO Feature Required", "Upgrade to install this app")
    print()
    show_warning(f"🔒 {manifest['display_name']} requires a PRO license!")
    print()
    show_info("Upgrade to PRO to unlock:")
    print("  • PRO-exclusive apps")
    print("  • Unlimited containers")
    print("  • Backup & Restore")
    print("  • Migration tools")
    print()
    show_info(f"💰 Only {PRICING['currency']}{PRICING['monthly']}/{PRICING['billing']}")
    print()
    
    choice = select_from_list(
        "What would you like to do?",
        ["⭐ Upgrade to PRO", "⬅️  Back to Apps"]
    )
    
    if "Upgrade" in choice:
        _activate_pro_license()
        return True
    
    return False