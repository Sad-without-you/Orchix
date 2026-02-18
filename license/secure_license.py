# ORCHIX v1.3
import hashlib
import hmac
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LicenseKeyValidator:
    """Online license key validator with Supabase backend"""

    # Supabase configuration from environment variables
    # These must be set in .env file (never commit .env to git!)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    # Timeout for online validation (seconds)
    REQUEST_TIMEOUT = 10

    @classmethod
    def validate_key(cls, key: str) -> dict:
        """Validate a license key using online verification"""
        if not key or not isinstance(key, str):
            return {
                'valid': False,
                'message': 'Invalid key format',
                'tier': None,
                'expires': None
            }

        # Strip whitespace
        key = key.strip()

        # Check if Supabase is configured
        if not cls.SUPABASE_URL or not cls.SUPABASE_KEY:
            return {
                'valid': False,
                'message': 'License validation not configured. Please contact support.',
                'tier': None,
                'expires': None
            }

        # Try online validation first
        try:
            online_result = cls._validate_online(key)
            # Update last_validated timestamp on successful validation
            if online_result.get('valid'):
                cls._update_last_validated(key)
            return online_result
        except Exception as e:
            # Connection error - check if we can use offline grace period
            print(f"⚠️  Online validation failed: {e}")
            print("   Attempting offline validation with grace period...")

            # Check if license was previously validated (within 7 days)
            offline_result = cls._validate_offline_grace_period(key)
            if offline_result['valid']:
                return offline_result

            # Grace period expired or never validated
            return {
                'valid': False,
                'message': f'Cannot reach license server. Please check your internet connection.',
                'tier': None,
                'expires': None
            }

    @classmethod
    def _validate_online(cls, key: str) -> dict:
        """Validate license key against Supabase API"""
        try:
            # Query Supabase for license with matching key
            response = requests.get(
                f'{cls.SUPABASE_URL}/rest/v1/licenses',
                params={
                    'license_key': f'eq.{key}',
                    'select': '*,customers(email)'
                },
                headers={
                    'apikey': cls.SUPABASE_KEY,
                    'Authorization': f'Bearer {cls.SUPABASE_KEY}'
                },
                timeout=cls.REQUEST_TIMEOUT
            )

            # Check if request was successful
            if response.status_code != 200:
                return {
                    'valid': False,
                    'message': f'Server error: {response.status_code}',
                    'tier': None,
                    'expires': None
                }

            # Parse response (Supabase always returns an array)
            data = response.json()

            # Check if license exists
            if not data or len(data) == 0:
                return {
                    'valid': False,
                    'message': 'License key not found',
                    'tier': None,
                    'expires': None
                }

            license_data = data[0]  # Take first result

            # Check if license is active
            if not license_data.get('is_active', False):
                return {
                    'valid': False,
                    'message': 'License key is deactivated',
                    'tier': None,
                    'expires': None
                }

            # Check activation limit
            max_activations = int(license_data.get('max_activations', 1))
            current_activations = int(license_data.get('current_activations', 0))

            if current_activations >= max_activations:
                return {
                    'valid': False,
                    'message': f'Maximum activations reached ({max_activations})',
                    'tier': None,
                    'expires': None
                }

            # Parse expiry date
            expires = None
            expires_at = license_data.get('expires_at')
            if expires_at:
                try:
                    expires = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))

                    # Check if expired
                    if datetime.now(expires.tzinfo) > expires:
                        return {
                            'valid': False,
                            'message': 'License has expired',
                            'tier': None,
                            'expires': expires
                        }
                except Exception as e:
                    print(f"Warning: Could not parse expiry date: {e}")

            # Get tier
            tier = license_data.get('tier', 'FREE').upper()

            # Get customer email from joined data
            customer_email = None
            if 'customers' in license_data and license_data['customers']:
                customer_email = license_data['customers'].get('email')

            return {
                'valid': True,
                'message': 'License validated successfully',
                'tier': tier,
                'expires': expires,
                'customer_email': customer_email,
                'license_id': license_data.get('id')
            }

        except requests.exceptions.Timeout:
            raise Exception("Connection timeout - please check your internet connection")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot reach license server - please check your internet connection")
        except Exception as e:
            raise Exception(f"Validation error: {str(e)}")

    @classmethod
    def _validate_offline(cls, key: str) -> dict:
        """Offline validation fallback (for development only)
        In production, this should not allow any keys to validate"""

        # In production/public release, return invalid for all keys
        # This prevents offline cracking
        return {
            'valid': False,
            'message': 'Online validation required. Please check your internet connection.',
            'tier': None,
            'expires': None
        }

    @classmethod
    def _update_last_validated(cls, key: str):
        """
        Update last_validated timestamp in license file after successful validation

        Args:
            key: License key string
        """
        import json
        from config import ORCHIX_CONFIG_DIR

        LICENSE_FILE = ORCHIX_CONFIG_DIR / '.orchix_license'

        if LICENSE_FILE.exists():
            try:
                with open(LICENSE_FILE, 'r') as f:
                    data = json.load(f)

                # Only update if this is the same key
                if data.get('key') == key:
                    data['last_validated'] = datetime.now().isoformat()

                    with open(LICENSE_FILE, 'w') as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not update last_validated: {e}")

    @classmethod
    def _validate_offline_grace_period(cls, key: str) -> dict:
        """Validate using offline grace period (7 days after last successful validation)"""
        import json
        from config import ORCHIX_CONFIG_DIR

        LICENSE_FILE = ORCHIX_CONFIG_DIR / '.orchix_license'

        if not LICENSE_FILE.exists():
            return {
                'valid': False,
                'message': 'No license file found. Please activate online first.',
                'tier': None,
                'expires': None
            }

        try:
            with open(LICENSE_FILE, 'r') as f:
                data = json.load(f)

            # Check if this is the same key
            if data.get('key') != key:
                return {
                    'valid': False,
                    'message': 'License key mismatch.',
                    'tier': None,
                    'expires': None
                }

            # Check if license was previously validated
            last_validated = data.get('last_validated')
            if not last_validated:
                return {
                    'valid': False,
                    'message': 'License must be validated online at least once.',
                    'tier': None,
                    'expires': None
                }

            # Parse last_validated timestamp
            try:
                last_validated_dt = datetime.fromisoformat(last_validated)
            except:
                return {
                    'valid': False,
                    'message': 'Invalid last_validated timestamp.',
                    'tier': None,
                    'expires': None
                }

            # Check grace period (7 days)
            grace_period = timedelta(days=7)
            now = datetime.now()

            if now - last_validated_dt > grace_period:
                days_ago = (now - last_validated_dt).days
                return {
                    'valid': False,
                    'message': f'Grace period expired ({days_ago} days since last validation). Please connect to internet.',
                    'tier': None,
                    'expires': None
                }

            # Check if license itself is expired
            expiry = data.get('expiry')
            if expiry:
                try:
                    expiry_dt = datetime.fromisoformat(expiry)
                    if now > expiry_dt:
                        return {
                            'valid': False,
                            'message': 'License has expired.',
                            'tier': None,
                            'expires': expiry_dt
                        }
                except:
                    pass

            # Grace period is valid
            days_remaining = 7 - (now - last_validated_dt).days
            return {
                'valid': True,
                'message': f'Offline mode - {days_remaining} days remaining in grace period',
                'tier': data.get('tier', 'PRO'),
                'expires': datetime.fromisoformat(expiry) if expiry else None
            }

        except Exception as e:
            return {
                'valid': False,
                'message': f'Error reading license file: {str(e)}',
                'tier': None,
                'expires': None
            }

    @classmethod
    def check_expiry(cls, key: str) -> bool:
        """Check if a license key has expired"""
        validation = cls.validate_key(key)

        if not validation['valid']:
            return True  # Invalid keys are considered "expired"

        if validation['expires'] is None:
            return False  # No expiry date

        # Make sure both datetimes have the same timezone info
        expires = validation['expires']
        if expires.tzinfo is not None:
            # expires is timezone-aware, make now aware too
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            # expires is naive, use naive now
            now = datetime.now()

        return now > expires


    @classmethod
    def get_key_info(cls, key: str) -> dict:
        """Get detailed information about a license key"""
        validation = cls.validate_key(key)

        info = {
            'key': key,
            'valid': validation['valid'],
            'tier': validation['tier'],
            'expires': validation['expires'],
            'expired': cls.check_expiry(key) if validation['valid'] else True,
            'message': validation['message']
        }

        return info


# Example usage and testing
if __name__ == "__main__":
    print("ORCHIX License Key Validator Test\n")

    # Test a sample key
    test_key = "Test"
    print(f"Testing Key: {test_key}")
    result = LicenseKeyValidator.validate_key(test_key)
    print(f"Valid: {result['valid']}")
    print(f"Message: {result['message']}")
    print(f"Tier: {result['tier']}")
    print(f"Expires: {result['expires']}")
    print()

    # Test invalid key
    invalid_key = "INVALID-KEY-12345"
    print(f"Testing Invalid Key: {invalid_key}")
    result = LicenseKeyValidator.validate_key(invalid_key)
    print(f"Valid: {result['valid']}")
    print(f"Message: {result['message']}")
    print()

    # Test key info
    print(f"Getting detailed info for: {test_key}")
    info = LicenseKeyValidator.get_key_info(test_key)
    print(f"Key Info: {info}")
