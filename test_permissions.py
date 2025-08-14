#!/usr/bin/env python3
"""
Test script for the RBAC permission system.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.permissions import (
    has_perm, 
    get_user_roles, 
    get_user_permissions,
    ROLE_PERMISSIONS
)

def test_permissions():
    """Test the permission system with various user configurations."""
    
    print("🔐 Testing RBAC Permission System\n")
    
    # Test user configurations
    test_users = [
        {
            "name": "Admin User",
            "data": {"mcrole": "admin", "roles": []}
        },
        {
            "name": "MC Admin User", 
            "data": {"mcrole": "mc_admin", "roles": []}
        },
        {
            "name": "Git Admin User",
            "data": {"mcrole": "git_admin", "roles": []}
        },
        {
            "name": "Viewer User",
            "data": {"mcrole": "viewer", "roles": []}
        },
        {
            "name": "Multi-Role User",
            "data": {"mcrole": "viewer", "roles": ["mc_admin", "git_admin"]}
        },
        {
            "name": "Legacy User (no roles field)",
            "data": {"mcrole": "admin"}
        }
    ]
    
    # Test permissions
    test_permissions = [
        "logs:view",
        "logs:stream", 
        "users:manage",
        "minecraft:admin",
        "git:admin"
    ]
    
    print("📋 Default Role Permissions:")
    for role, perms in ROLE_PERMISSIONS.items():
        print(f"  {role}: {', '.join(sorted(perms)) if perms else 'none'}")
    
    print("\n👥 Testing User Permissions:")
    print("-" * 80)
    
    for user in test_users:
        print(f"\n👤 {user['name']}")
        print(f"   Data: {user['data']}")
        
        # Get user roles
        roles = get_user_roles(user['data'])
        print(f"   Roles: {', '.join(roles)}")
        
        # Get all permissions
        all_perms = get_user_permissions(user['data'])
        print(f"   All Permissions: {', '.join(sorted(all_perms)) if all_perms else 'none'}")
        
        # Test specific permissions
        print("   Permission Check:")
        for perm in test_permissions:
            has_access = has_perm(user['data'], perm)
            status = "✅" if has_access else "❌"
            print(f"     {status} {perm}")
    
    print("\n🎯 Permission Summary:")
    print("-" * 80)
    
    # Show who can access what
    for perm in test_permissions:
        print(f"\n{perm}:")
        for user in test_users:
            if has_perm(user['data'], perm):
                print(f"  ✅ {user['name']}")
    
    print("\n✨ Permission system test completed!")

if __name__ == "__main__":
    test_permissions()
