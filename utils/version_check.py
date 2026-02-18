import urllib.request
import json

CURRENT_VERSION = "1.3"
GITHUB_REPO = "Sad-without-you/ORCHIX"


def check_for_updates():
    '''Check GitHub for newer ORCHIX version.
    Returns dict with 'update_available', 'latest_version', 'message' or None on error.
    '''
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/tags"
        req = urllib.request.Request(url, headers={"User-Agent": "ORCHIX-UpdateCheck"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            tags = json.loads(resp.read().decode())

        if not tags:
            # Repo exists but no release tags yet
            return {
                'update_available': False,
                'latest_version': CURRENT_VERSION,
                'current_version': CURRENT_VERSION,
                'message': ''
            }

        # Get latest tag (first in list)
        latest_tag = tags[0]['name'].lstrip('v')

        if _version_newer(latest_tag, CURRENT_VERSION):
            return {
                'update_available': True,
                'latest_version': latest_tag,
                'message': f"ORCHIX v{latest_tag} available! (current: v{CURRENT_VERSION})"
            }

        return {
            'update_available': False,
            'latest_version': latest_tag,
            'current_version': CURRENT_VERSION,
            'message': ''
        }

    except Exception:
        return None


def _version_newer(latest, current):
    '''Compare version strings (e.g. "1.2" > "1.1")'''
    try:
        latest_parts = [int(x) for x in latest.split('.')]
        current_parts = [int(x) for x in current.split('.')]

        # Pad to same length
        max_len = max(len(latest_parts), len(current_parts))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        current_parts.extend([0] * (max_len - len(current_parts)))

        return latest_parts > current_parts
    except (ValueError, AttributeError):
        return False
