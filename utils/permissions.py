"""
Role-Based Access Control (RBAC) permissions system for Marx-Tec VM Dashboard.
"""

import os
import json
from typing import Set, Dict, List, Optional
from functools import wraps
from flask import session, redirect, url_for, abort, current_app

# Core role-to-permissions mapping
ROLE_PERMISSIONS = {
    "admin": {"logs:view", "logs:stream", "users:manage", "system:admin"},
    "mc_admin": {"logs:view", "logs:stream", "minecraft:admin"},
    "git_admin": {"logs:view", "git:admin"},
    "viewer": set(),  # No special permissions
}

# Environment-based role permissions override
ROLE_PERMISSIONS_EXTRA = {}

def load_extra_permissions():
    """Load additional role permissions from environment or config file."""
    global ROLE_PERMISSIONS_EXTRA
    
    # Try to load from environment variable
    env_perms = os.getenv('ROLE_PERMISSIONS_EXTRA')
    if env_perms:
        try:
            ROLE_PERMISSIONS_EXTRA = json.loads(env_perms)
        except json.JSONDecodeError:
            current_app.logger.warning("Invalid ROLE_PERMISSIONS_EXTRA JSON")
    
    # Try to load from config file
    config_file = os.getenv('PERMISSIONS_CONFIG_FILE', 'userdata/permissions.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_perms = json.load(f)
                # Merge with environment permissions
                for role, perms in file_perms.items():
                    if role in ROLE_PERMISSIONS_EXTRA:
                        ROLE_PERMISSIONS_EXTRA[role].update(perms)
                    else:
                        ROLE_PERMISSIONS_EXTRA[role] = set(perms)
        except (json.JSONDecodeError, IOError) as e:
            current_app.logger.warning(f"Could not load permissions config: {e}")

def get_user_roles(user_data: dict) -> List[str]:
    """
    Extract roles from user data, handling both single mcrole and roles list.
    Backward compatible with existing user structure.
    """
    roles = []
    
    # Check if user has explicit roles list
    if 'roles' in user_data and isinstance(user_data['roles'], list):
        roles.extend(user_data['roles'])
    
    # Check for single mcrole (backward compatibility)
    if 'mcrole' in user_data and user_data['mcrole']:
        roles.append(user_data['mcrole'])
    
    # Ensure we have at least one role
    if not roles:
        roles.append('viewer')  # Default role
    
    return list(set(roles))  # Remove duplicates

def has_perm(user_data: dict, permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user_data: User dictionary from session or database
        permission: Permission string (e.g., "logs:view")
    
    Returns:
        True if user has permission, False otherwise
    """
    if not user_data:
        return False
    
    user_roles = get_user_roles(user_data)
    
    # Check core permissions
    for role in user_roles:
        if role in ROLE_PERMISSIONS and permission in ROLE_PERMISSIONS[role]:
            return True
    
    # Check extra permissions
    for role in user_roles:
        if role in ROLE_PERMISSIONS_EXTRA and permission in ROLE_PERMISSIONS_EXTRA[role]:
            return True
    
    return False

def has_perm_decorator(permission: str):
    """
    Decorator to require a specific permission for a route.
    
    Usage:
        @app.route('/logs')
        @has_perm_decorator('logs:view')
        def logs_page():
            return render_template('logs.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('auth.login'))
            
            # Create user data dict from session
            user_data = {
                'mcrole': session.get('mcrole'),
                'roles': session.get('roles', []),
                'username': session.get('username'),
                'service': session.get('service')
            }
            
            if not has_perm(user_data, permission):
                abort(403, description="Insufficient permissions")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_user_permissions(user_data: dict) -> Set[str]:
    """
    Get all permissions for a user.
    
    Args:
        user_data: User dictionary from session or database
    
    Returns:
        Set of permission strings
    """
    if not user_data:
        return set()
    
    user_roles = get_user_roles(user_data)
    permissions = set()
    
    # Collect permissions from all roles
    for role in user_roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
        if role in ROLE_PERMISSIONS_EXTRA:
            permissions.update(ROLE_PERMISSIONS_EXTRA[role])
    
    return permissions

# Initialize extra permissions on module load
try:
    load_extra_permissions()
except Exception as e:
    # Log error but don't fail - use default permissions
    pass
