# ORCHIX v1.1
# FREE TIER
FREE_FEATURES = {
    'max_containers': 3,
    'backup_restore': False,
    'multi_instance': False,
    'migration': False,
    'audit_log': False,
    'apps': ['n8n', 'postgres', 'redis'],
    'tier_name': 'FREE',
    'tier_display': '🆓 FREE'
}

# PRO TIER  
PRO_FEATURES = {
    'max_containers': 999,
    'backup_restore': True,
    'multi_instance': True,
    'migration': True,
    'audit_log': True,
    'apps': ['*'],
    'tier_name': 'PRO',
    'tier_display': '⭐ PRO'
}

# Feature descriptions for UI
FEATURE_DESCRIPTIONS = {
    'max_containers': 'Maximum number of containers',
    'backup_restore': 'Backup & Restore functionality',
    'multi_instance': 'Multiple instances per application',
    'migration': 'Server migration tools',
    'audit_log': 'Audit logging and user activity tracking',
    'apps': 'Available applications',
}

# Base PRO Benefits (static features)
_BASE_PRO_BENEFITS = [
    "✅ Unlimited Containers",
    "✅ Backup & Restore",
    "✅ Multi-Instance Support",
    "✅ Server Migration Tools",
    "✅ Audit Logging",
    "✅ Priority Updates",
    "✅ Email Support",
]

def get_pro_benefits():
    '''Get PRO benefits dynamically including PRO-only apps'''
    benefits = _BASE_PRO_BENEFITS.copy()
    
    # Add dynamic PRO apps
    try:
        from apps.manifest_loader import load_all_manifests
        manifests = load_all_manifests()
        
        pro_apps = []
        for manifest in manifests.values():
            if manifest.get('license_required') == 'pro':
                icon = manifest.get('icon', '🔒')
                display_name = manifest.get('display_name', manifest['name'])
                pro_apps.append(f"✅ {icon} {display_name}")
        
        # Add PRO apps to benefits
        if pro_apps:
            benefits.append("")  # Separator
            benefits.append("PRO-Exclusive Apps:")
            benefits.extend(pro_apps)
    
    except Exception:
        # Fallback if manifest loading fails
        pass
    
    return benefits

# Legacy compatibility - for code that still uses PRO_BENEFITS directly
PRO_BENEFITS = get_pro_benefits()

# Pricing
PRICING = {
    'monthly': 29,
    'currency': '€',
    'billing': 'Monthly'
}