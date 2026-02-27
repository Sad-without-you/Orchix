# ORCHIX v1.4
import json
import os
from pathlib import Path
from datetime import datetime
from enum import Enum
import getpass


class AuditEventType(Enum):
    """Types of audit events"""
    INSTALL = "INSTALL"
    UNINSTALL = "UNINSTALL"
    UPDATE = "UPDATE"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"
    HEALTH_CHECK = "HEALTH_CHECK"
    MIGRATION = "MIGRATION"
    LICENSE_CHANGE = "LICENSE_CHANGE"
    CONTAINER_START = "CONTAINER_START"
    CONTAINER_STOP = "CONTAINER_STOP"
    USER_CREATED = "USER_CREATED"
    USER_DELETED = "USER_DELETED"
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"


# Store logs in ORCHIX/audit directory
AUDIT_LOG_DIR = Path(__file__).parent.parent / 'audit'
AUDIT_LOG_FILE = AUDIT_LOG_DIR / 'audit.log'
AUDIT_DAILY_DIR = AUDIT_LOG_DIR / 'daily'


class AuditLogger:
    """
    Audit logger for tracking user actions
    Only enabled for PRO users
    """
    
    def __init__(self, enabled=False):
        """Initialize audit logger"""
        self.enabled = enabled
        self.log_file = AUDIT_LOG_FILE
        self._web_user = None

    def set_web_user(self, username):
        """Set Web UI username for audit logging."""
        self._web_user = username
    
    def log_event(self, event_type: AuditEventType, app_name: str, details: dict = None):
        """Log an audit event"""
        if not self.enabled:
            return
        
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'user': self._get_current_user(),
                'event_type': event_type.value,
                'app_name': app_name,
                'details': details or {}
            }
            
            # Ensure log directory exists and create if not
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # Append to log file (Web UI editable)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')

            # Write to persistent daily .txt file (not affected by single-event deletes)
            self._write_daily_log(event)

        except Exception as e:
            # Silently fail - don't break the app if logging fails
            pass

    def _write_daily_log(self, event):
        """Write event to persistent daily .txt log file (append-only)."""
        try:
            AUDIT_DAILY_DIR.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime('%Y-%m-%d')
            daily_file = AUDIT_DAILY_DIR / f'{today}.txt'

            ts = event.get('timestamp', '')[:19]
            user = event.get('user', 'unknown')
            etype = event.get('event_type', '')
            app = event.get('app_name', '')
            details = event.get('details', {})
            detail_str = ', '.join(f'{k}={v}' for k, v in details.items()) if details else ''

            line = f'[{ts}] [{user}] {etype} {app}'
            if detail_str:
                line += f' ({detail_str})'

            with open(daily_file, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except Exception:
            pass
    
    def _get_current_user(self):
        """Get current user - prefers Web UI session user, falls back to system user."""
        if self._web_user:
            return self._web_user
        try:
            return getpass.getuser()
        except:
            return "unknown"
    
    def get_recent_events(self, limit=100, event_type=None, app_name=None):
        """Get recent audit events"""
        if not self.log_file.exists():
            return []
        
        events = []
        try:
            with open(self.log_file, 'r') as f:
                # Read all lines and reverse to get newest first
                lines = f.readlines()[::-1]
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    try:
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        if event_type and event.get('event_type') != event_type:
                            continue
                        if app_name and event.get('app_name') != app_name:
                            continue
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        return events
    
    def get_user_activity(self, username=None, limit=100):
        """
        Get activity for a specific user
        
        Args:
            username (str): Username to filter by (if None, current user)
            limit (int): Maximum number of events
            
        Returns:
            list: Events for the user
        """
        if username is None:
            username = self._get_current_user()
        
        if not self.log_file.exists():
            return []
        
        events = []
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[::-1]
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    try:
                        event = json.loads(line.strip())
                        if event.get('user') == username:
                            events.append(event)
                            
                            if len(events) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        return events

    def clear_old_logs(self, days=90):
        """Clear audit logs older than specified days (both main log and daily files)"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)

        # Clean main log file
        if self.log_file.exists():
            try:
                events = []
                with open(self.log_file, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            event = json.loads(line.strip())
                            event_time = datetime.fromisoformat(event['timestamp'])
                            if event_time > cutoff:
                                events.append(event)
                        except:
                            pass

                with open(self.log_file, 'w') as f:
                    for event in events:
                        f.write(json.dumps(event) + '\n')
            except Exception:
                pass

        # Clean old daily .txt files
        if AUDIT_DAILY_DIR.exists():
            try:
                cutoff_str = cutoff.strftime('%Y-%m-%d')
                for f in AUDIT_DAILY_DIR.glob('*.txt'):
                    # Filename is YYYY-MM-DD.txt
                    if f.stem < cutoff_str:
                        f.unlink()
            except Exception:
                pass


# Global audit logger instance
_audit_logger = None


def get_audit_logger(enabled=False):
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(enabled=enabled)
    else:
        _audit_logger.enabled = enabled
    
    return _audit_logger
