import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from license.features import FREE_FEATURES, PRO_FEATURES, FEATURE_DESCRIPTIONS

LICENSE_FILE = Path.home() / '.orchix_license'
MANAGED_CONTAINERS_FILE = Path.home() / '.orchix_managed_containers.json'


class LicenseManager:
    '''Manage license and feature gates'''

    def __init__(self):
        self.tier, self.license_key, self.expiry_date = self._load_license()

    def _load_license(self):
        '''Load license from file'''
        if LICENSE_FILE.exists():
            try:
                with open(LICENSE_FILE, 'r') as f:
                    content = f.read().strip()

                    # Try to parse as JSON (new format)
                    try:
                        data = json.loads(content)
                        tier = data.get('tier', 'FREE')
                        license_key = data.get('key')
                        expiry = data.get('expiry')

                        # Parse expiry date if exists
                        expiry_date = None
                        if expiry:
                            try:
                                expiry_date = datetime.fromisoformat(expiry)
                            except:
                                pass

                        # Check if license is expired
                        if tier == 'PRO' and expiry_date:
                            if expiry_date.tzinfo is not None:
                                from datetime import timezone
                                now = datetime.now(timezone.utc)
                            else:
                                now = datetime.now()
                            if now > expiry_date:
                                return 'FREE', None, None

                        return tier, license_key, expiry_date
                    except json.JSONDecodeError:
                        # Old format - just "PRO" string
                        if content == 'PRO':
                            return 'PRO', None, None
            except Exception:
                pass

        return 'FREE', None, None
    
    def is_pro(self):
        '''Check if PRO license'''
        return self.tier == 'PRO'
    
    def is_free(self):
        '''Check if FREE license'''
        return self.tier == 'FREE'
    
    def get_tier(self):
        '''Get current tier name'''
        return self.tier
    
    def get_tier_display(self):
        '''Get display name for current tier'''
        features = PRO_FEATURES if self.is_pro() else FREE_FEATURES
        return features['tier_display']
    
    def activate_pro(self, license_key):
        '''Activate PRO license with key'''
        validation = self._validate_key(license_key)
        if validation:
            try:
                LICENSE_FILE.parent.mkdir(exist_ok=True)

                # Get key info including expiry
                from license.secure_license import LicenseKeyValidator
                key_info = LicenseKeyValidator.get_key_info(license_key)

                # Prepare license data
                license_data = {
                    'tier': 'PRO',
                    'key': license_key,
                    'expiry': key_info['expires'].isoformat() if key_info['expires'] else None,
                    'activated': datetime.now().isoformat(),
                    'last_validated': datetime.now().isoformat()
                }

                # Save as JSON
                with open(LICENSE_FILE, 'w') as f:
                    json.dump(license_data, f, indent=2)

                self.tier = 'PRO'
                self.license_key = license_key
                self.expiry_date = key_info['expires']
                self.clear_managed_containers()
                return True
            except Exception as e:
                print(f"Failed to save license: {e}")
                return False
        return False
    
    def _validate_key(self, key):
        '''Validate license key with cryptographic verification'''
        from license.secure_license import LicenseKeyValidator
        
        # Use secure validator
        result = LicenseKeyValidator.validate_key(key)
        
        if not result['valid']:
            print(f"  License validation failed: {result['message']}")
            return False

        # Check if expired
        if LicenseKeyValidator.check_expiry(key):
            print("  License has expired")
            return False

        print(f"  License validated successfully")
        return True
    
    def deactivate(self):
        '''Deactivate license (back to FREE)'''
        try:
            if LICENSE_FILE.exists():
                LICENSE_FILE.unlink()
            self.tier = 'FREE'
            self.license_key = None
            self.expiry_date = None
            return True
        except Exception:
            return False
    
    def get_feature(self, feature_name):
        '''Get feature value for current tier'''
        features = PRO_FEATURES if self.is_pro() else FREE_FEATURES
        return features.get(feature_name)
    
    def has_feature(self, feature_name):
        '''Check if feature is available'''
        value = self.get_feature(feature_name)
        if isinstance(value, bool):
            return value
        return True  # Non-boolean features are always "available"
    
    def get_container_limit(self):
        '''Get max container limit'''
        return self.get_feature('max_containers')
    
    def can_install_app(self, app_name):
        '''Check if app is available in current tier'''
        allowed_apps = self.get_feature('apps')
        if '*' in allowed_apps:
            return True
        return app_name in allowed_apps
    
    def check_container_limit(self):
        '''Check current container count vs limit'''
        try:
            # Count running containers managed by ORCHIX
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                containers = [c for c in result.stdout.split('\n') if c]
                current_count = len(containers)
                limit = self.get_container_limit()
                
                return {
                    'current': current_count,
                    'limit': limit,
                    'reached': current_count >= limit,
                    'remaining': max(0, limit - current_count)
                }
            
            return {'current': 0, 'limit': self.get_container_limit(), 'reached': False, 'remaining': self.get_container_limit()}
        except Exception:
            return {'current': 0, 'limit': self.get_container_limit(), 'reached': False, 'remaining': self.get_container_limit()}
    
    # ============ Managed Container Selection (FREE tier) ============

    def get_managed_containers(self):
        """Get list of selected containers for FREE tier, or None if all visible."""
        if self.is_pro():
            return None  # PRO sees everything
        if not MANAGED_CONTAINERS_FILE.exists():
            return None  # No selection made yet
        try:
            data = json.loads(MANAGED_CONTAINERS_FILE.read_text(encoding='utf-8'))
            return data.get('selected', [])
        except Exception:
            return None

    def set_managed_containers(self, names):
        """Save the selected container names for FREE tier."""
        data = {
            'selected': list(names),
            'selected_at': datetime.now().isoformat()
        }
        MANAGED_CONTAINERS_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def clear_managed_containers(self):
        """Remove selection file (e.g. when PRO is activated)."""
        try:
            if MANAGED_CONTAINERS_FILE.exists():
                MANAGED_CONTAINERS_FILE.unlink()
        except Exception:
            pass

    def needs_container_selection(self):
        """Check if user needs to select managed containers.
        Returns True when FREE tier, >limit containers, no selection file.
        """
        if self.is_pro():
            return False
        if MANAGED_CONTAINERS_FILE.exists():
            return False
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            if result.returncode == 0:
                containers = [c for c in result.stdout.split('\n') if c.strip()]
                return len(containers) > self.get_container_limit()
        except Exception:
            pass
        return False

    def get_license_info(self):
        '''Get complete license information'''
        container_status = self.check_container_limit()

        # Calculate days remaining if expiry exists
        days_remaining = None
        if self.expiry_date:
            # Handle timezone-aware vs naive datetime
            if self.expiry_date.tzinfo is not None:
                from datetime import timezone
                now = datetime.now(timezone.utc)
            else:
                now = datetime.now()
            delta = self.expiry_date - now
            days_remaining = max(0, delta.days)

        return {
            'tier': self.tier,
            'tier_display': self.get_tier_display(),
            'is_pro': self.is_pro(),
            'license_key': self.license_key,
            'expiry_date': self.expiry_date,
            'days_remaining': days_remaining,
            'features': {
                'max_containers': self.get_container_limit(),
                'backup_restore': self.has_feature('backup_restore'),
                'multi_instance': self.has_feature('multi_instance'),
                'migration': self.has_feature('migration'),
                'audit_log': self.has_feature('audit_log'),
            },
            'container_status': container_status
        }


# Global instance
_license_manager = None

def get_license_manager():
    '''Get global license manager instance'''
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager