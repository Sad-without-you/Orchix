# ORCHIX v1.3
"""
License Validator
=================
Validates license keys against the ORCHIX license server.
Supabase has been removed – all validation goes through /api/v1/validate.

Config (.env or environment):
    ORCHIX_LICENSE_SERVER=https://orchix.dev   (default)

Offline grace period: 3 days after last successful online validation.
The last-validated timestamp is saved in ~/.orchix_configs/.orchix_license.
"""

import hashlib
import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('ORCHIX_LICENSE_SERVER', 'https://orchix.dev').rstrip('/')
_TIMEOUT = 10


class LicenseKeyValidator:
    """Validates ORCHIX license keys against the license server."""

    @classmethod
    def validate_key(cls, key: str) -> dict:
        """
        Full validation: try online first, fall back to 3-day offline grace.

        Returns dict with keys:
            valid (bool), message (str), tier (str|None),
            expires (str|None), status (str)
        """
        if not key or not isinstance(key, str):
            return cls._result(False, 'Invalid key format')

        key = key.strip()

        try:
            resp = requests.post(
                f'{_SERVER}/api/v1/validate',
                json={'license_key': key, 'orchix_version': '1.3'},
                timeout=_TIMEOUT,
            )
            data = resp.json()
            if data.get('valid'):
                cls._save_last_validated(key, data)
                return cls._result(
                    True,
                    data.get('message', 'License validated'),
                    tier=data.get('tier'),
                    expires=data.get('expires_at'),
                    status=data.get('status', 'active'),
                    license_id=data.get('license_id'),
                )
            return cls._result(False, data.get('message', 'License invalid or expired'))

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print('⚠️  License server unreachable – trying offline grace period...')
            return cls._validate_offline_grace_period(key)
        except Exception as e:
            return cls._result(False, f'Validation error: {e}')

    # -------------------------------------------------------------------------

    @classmethod
    def check_expiry(cls, key: str) -> bool:
        """Returns True if the key is expired / invalid."""
        result = cls.validate_key(key)
        return not result['valid']

    @classmethod
    def increment_activations(cls, license_id, current_activations=0):
        """No-op: activation tracking is now server-side."""

    @classmethod
    def decrement_activations(cls, license_key: str):
        """No-op: deactivation tracking is now server-side."""

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _result(valid, message, tier=None, expires=None, status='active', license_id=None):
        return {
            'valid': valid,
            'message': message,
            'tier': tier,
            'expires': expires,
            'status': status,
            'license_id': license_id,
            'current_activations': 0,
        }

    @classmethod
    def _license_file(cls) -> Path:
        from config import ORCHIX_CONFIG_DIR
        return Path(ORCHIX_CONFIG_DIR) / '.orchix_license'

    @classmethod
    def _save_last_validated(cls, key: str, data: dict):
        """Write last-validated timestamp + key hash to license file."""
        lf = cls._license_file()
        try:
            existing = {}
            if lf.exists():
                try:
                    existing = json.loads(lf.read_text(encoding='utf-8'))
                except Exception:
                    pass

            existing['last_validated'] = datetime.now().isoformat()
            existing['key_hash'] = hashlib.sha256(key.encode()).hexdigest()
            existing['tier'] = data.get('tier', existing.get('tier'))
            existing['expiry'] = data.get('expires_at', existing.get('expiry'))

            lf.write_text(json.dumps(existing, indent=2), encoding='utf-8')
        except Exception as e:
            print(f'Warning: could not update last_validated: {e}')

    @classmethod
    def _validate_offline_grace_period(cls, key: str) -> dict:
        """Allow up to 3 days of operation when server is unreachable."""
        lf = cls._license_file()
        if not lf.exists():
            return cls._result(False, 'Cannot reach license server. Please check your internet connection.')

        try:
            data = json.loads(lf.read_text(encoding='utf-8'))
        except Exception:
            return cls._result(False, 'Cannot reach license server.')

        # Verify this is the same key (compare hashes)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        if data.get('key_hash') != key_hash:
            # Fallback: also accept plaintext key field (legacy files)
            if data.get('key') != key:
                return cls._result(False, 'Cannot reach license server.')

        last_validated_str = data.get('last_validated')
        if not last_validated_str:
            return cls._result(False, 'License must be validated online at least once.')

        try:
            last_validated = datetime.fromisoformat(last_validated_str)
        except Exception:
            return cls._result(False, 'Cannot reach license server.')

        elapsed = datetime.now() - last_validated
        if elapsed > timedelta(days=3):
            days = elapsed.days
            return cls._result(
                False,
                f'Offline grace period expired ({days} days since last check). '
                'Please connect to the internet to re-validate your license.',
            )

        remaining = 3 - elapsed.days
        return cls._result(
            True,
            f'Offline mode – {remaining} day(s) remaining in grace period',
            tier=data.get('tier', 'PRO'),
            expires=data.get('expiry'),
            status='active',
        )
