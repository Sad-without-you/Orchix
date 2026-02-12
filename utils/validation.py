# ORCHIX v1.2 - Input validation and sanitization
import re


def validate_container_name(name):
    '''Validate and sanitize container/instance name.
    Docker names must match: [a-zA-Z0-9][a-zA-Z0-9_.-]*
    Returns sanitized name or raises ValueError.
    '''
    if not name or not isinstance(name, str):
        raise ValueError("Container name is required")

    name = name.strip()

    if len(name) > 128:
        raise ValueError("Container name too long (max 128 chars)")

    # Block path traversal
    if '..' in name or '/' in name or '\\' in name:
        raise ValueError("Invalid characters in container name")

    # Docker container name regex
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', name):
        raise ValueError("Container name must start with alphanumeric and contain only letters, digits, _, ., -")

    return name


def validate_port(port):
    '''Validate port number. Returns int or raises ValueError.'''
    try:
        port = int(port)
    except (ValueError, TypeError):
        raise ValueError("Port must be a number")

    if not (1 <= port <= 65535):
        raise ValueError("Port must be between 1 and 65535")

    return port


def validate_filename(filename, allowed_extensions=None):
    '''Validate a filename (no path traversal, restricted chars).
    Returns filename or raises ValueError.
    '''
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename is required")

    filename = filename.strip()

    # Block path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Invalid filename")

    # Block null bytes
    if '\x00' in filename:
        raise ValueError("Invalid filename")

    # Check extension if specified
    if allowed_extensions:
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        # Handle double extensions like .tar.gz
        if filename.endswith('.tar.gz'):
            ext = 'tar.gz'
        if ext not in allowed_extensions:
            raise ValueError(f"File type not allowed: .{ext}")

    return filename


def sanitize_yaml_value(value):
    '''Sanitize a value for safe YAML interpolation.
    Escapes or quotes values that could break YAML structure.
    '''
    if not isinstance(value, str):
        return str(value)

    # If value contains YAML-breaking chars, quote it
    dangerous_chars = [':', '#', '{', '}', '[', ']', ',', '&', '*', '!', '|', '>', "'", '"', '%', '@', '`', '\n', '\r']
    if any(c in value for c in dangerous_chars):
        # Double-quote and escape internal quotes/backslashes
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        return f'"{escaped}"'

    return value
