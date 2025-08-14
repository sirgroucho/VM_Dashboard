"""
Template helper functions for Jinja2 templates.
"""

from utils.permissions import has_perm

def has_permission(user_data, permission):
    """
    Check if user has a specific permission.
    This function can be used in Jinja2 templates.
    """
    return has_perm(user_data, permission)

def get_user_data_from_session(session):
    """
    Extract user data from Flask session for permission checking.
    """
    return {
        'mcrole': session.get('mcrole'),
        'roles': session.get('roles', []),
        'username': session.get('username'),
        'service': session.get('service')
    }
