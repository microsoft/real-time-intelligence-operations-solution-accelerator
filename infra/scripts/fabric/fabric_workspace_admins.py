#!/usr/bin/env python3
"""
Fabric Workspace Administrators Management Module

This module provides functionality to add administrators to a Microsoft Fabric workspace.
Supports both user principal names (UPNs) and service principal object IDs via CSV input.

Features:
- Add administrators by UPN (user@contoso.com) or GUID with Graph API resolution
- Skip existing administrators to avoid duplicates
- Comprehensive error handling and reporting
- Support for both individual users and service principals

Usage:
    python fabric_workspace_admins.py --workspace-id "12345678-1234-1234-1234-123456789012" --fabricAdmins-csv "user@contoso.com,admin@company.com,12345678-1234-1234-1234-123456789012"

Requirements:
    - fabric_api.py module in the same directory
    - graph_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Appropriate Fabric workspace permissions (Admin role required to add other administrators)
"""

import argparse
import sys
import uuid
from fabric_api import FabricApiClient, FabricWorkspaceApiClient, FabricApiError
from graph_api import create_graph_client, GraphApiError

####################
# Helper Functions #
####################

def is_valid_guid(value):
    """Check if a string is a valid GUID format."""
    if not value or not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def detect_principal_type(admin_identifier, graph_client=None):
    """
    Detect if an identifier is a user or service principal and resolve to object ID.
    
    Args:
        admin_identifier: User UPN, object ID (GUID), or application ID (GUID)
        graph_client: Optional Graph API client (will create one if not provided)
    
    Returns:
        Tuple of (principal_type, object_id, principal_data)
        - principal_type: "User" or "ServicePrincipal" 
        - object_id: The object ID of the principal
        - principal_data: Full principal object from Graph API
        
    Raises:
        ValueError: If identifier cannot be resolved
        GraphApiError: If Graph API calls fail
    """
    try:
        # Create Graph client if not provided
        if graph_client is None:
            graph_client = create_graph_client()
        
        # Use Graph API to resolve the principal
        principal_type, object_id, principal_data = graph_client.resolve_principal(admin_identifier)
        
        return principal_type, object_id, principal_data
        
    except GraphApiError as e:
        # Convert Graph API errors to Unknown type for fallback handling
        print(f"  ⚠️ WARNING: Graph API lookup failed for '{admin_identifier}': {str(e)}")
        print(f"     Will try both ServicePrincipal and User types...")
        return "Unknown", admin_identifier, {"id": admin_identifier, "displayName": "Unknown"}
    except Exception as e:
        # Fallback to original logic if Graph API is not available
        print(f"  ⚠️ WARNING: Graph API lookup failed for '{admin_identifier}': {str(e)}")
        print(f"     Falling back to basic identifier pattern detection...")
        
        if is_valid_guid(admin_identifier):
            return "ServicePrincipal", admin_identifier, {"id": admin_identifier, "displayName": "Unknown"}
        elif "@" in admin_identifier and "." in admin_identifier:
            return "User", admin_identifier, {"userPrincipalName": admin_identifier, "displayName": "Unknown"}
        else:
            print(f"     Unable to determine principal type - will try both ServicePrincipal and User...")
            return "Unknown", admin_identifier, {"id": admin_identifier, "displayName": "Unknown"}

def get_existing_admin_principals(workspace_client):
    """Get set of existing admin principal IDs for duplicate checking."""
    try:
        print(f"    🔍 Checking existing role assignments...")
        assignments = workspace_client.get_role_assignments(get_all=True)
        
        existing_principals = set()
        admin_count = 0
        
        for assignment in assignments:
            if assignment.get('role') == 'Admin':
                admin_count += 1
                principal = assignment.get('principal', {})
                principal_id = principal.get('id', '').lower()
                if principal_id:
                    existing_principals.add(principal_id)
                
                # Also add UPN if available for easier matching
                user_details = principal.get('userDetails', {})
                upn = user_details.get('userPrincipalName', '').lower()
                if upn:
                    existing_principals.add(upn)
        
        print(f"    📊 Found {admin_count} existing administrator(s)")
        return existing_principals
        
    except Exception as e:
        print(f"    ⚠️ WARNING: Could not retrieve existing role assignments: {str(e)}")
        print("       Will proceed but may create duplicates")
        return set()

def add_workspace_admin(workspace_client, admin_identifier, existing_principals, graph_client):
    """Add a single workspace administrator with simplified error handling."""
    # Check if already exists
    if admin_identifier.lower() in existing_principals:
        print(f"    ⏭️ Skipping '{admin_identifier}' - already a workspace administrator")
        return {'status': 'skipped', 'message': 'Already exists'}
    
    try:
        # Try to resolve principal type using Graph API
        principal_type, object_id, principal_data = detect_principal_type(admin_identifier, graph_client)
        
        if object_id.lower() in existing_principals:
            print(f"    ⏭️ Skipping '{admin_identifier}' - already a workspace administrator")
            existing_principals.add(admin_identifier.lower())  # Prevent future duplicates
            return {'status': 'skipped', 'message': 'Already exists (by object ID)'}
        
        display_name = principal_data.get('displayName', 'Unknown')
        
        # Handle unknown principal type by trying both ServicePrincipal and User
        if principal_type == "Unknown":
            print(f"    🔐 Trying to add administrator (type unknown): {admin_identifier} ({display_name})")
            
            # Try ServicePrincipal first
            try:
                print(f"    🔄 Attempting as ServicePrincipal...")
                workspace_client.add_role_assignment(
                    principal_id=object_id,
                    principal_type="ServicePrincipal",
                    role="Admin",
                    display_name=display_name,
                    aad_app_id=principal_data.get('appId')
                )
                print(f"    ✅ Successfully added '{admin_identifier}' as ServicePrincipal administrator")
                existing_principals.add(object_id.lower())
                existing_principals.add(admin_identifier.lower())
                return {'status': 'success', 'message': 'Added successfully as ServicePrincipal'}
            except Exception as sp_error:
                print(f"    ❌ ServicePrincipal attempt failed: {str(sp_error)}")
                
                # Try User as fallback
                try:
                    print(f"    🔄 Attempting as User...")
                    workspace_client.add_role_assignment(
                        principal_id=object_id,
                        principal_type="User",
                        role="Admin",
                        display_name=display_name,
                        user_principal_name=principal_data.get('userPrincipalName', admin_identifier)
                    )
                    print(f"    ✅ Successfully added '{admin_identifier}' as User administrator")
                    existing_principals.add(object_id.lower())
                    existing_principals.add(admin_identifier.lower())
                    return {'status': 'success', 'message': 'Added successfully as User'}
                except Exception as user_error:
                    print(f"    ❌ User attempt also failed: {str(user_error)}")
                    return {'status': 'failed', 'message': f'Failed as both ServicePrincipal and User: SP({str(sp_error)}), User({str(user_error)})'}
        else:
            print(f"    🔐 Adding {principal_type.lower()} administrator: {admin_identifier} ({display_name})")
            
            # Add role assignment based on type
            if principal_type == "User":
                workspace_client.add_role_assignment(
                    principal_id=object_id,
                    principal_type=principal_type,
                    role="Admin",
                    display_name=display_name,
                    user_principal_name=principal_data.get('userPrincipalName', admin_identifier)
                )
            else:  # ServicePrincipal
                workspace_client.add_role_assignment(
                    principal_id=object_id,
                    principal_type=principal_type,
                    role="Admin",
                    display_name=display_name,
                    aad_app_id=principal_data.get('appId')
                )
            
            print(f"    ✅ Successfully added '{admin_identifier}' as workspace administrator")
            existing_principals.add(object_id.lower())
            existing_principals.add(admin_identifier.lower())
            return {'status': 'success', 'message': 'Added successfully'}
        
    except (ValueError, GraphApiError) as e:
        return {'status': 'failed', 'message': f'Principal type detection failed: {str(e)}'}
        
    except FabricApiError as e:
        error_hints = {
            400: "Verify the identifier is correct and the principal exists",
            403: "Ensure you have Admin permissions on this workspace", 
            404: "Check if the principal exists in your Azure AD tenant"
        }
        hint = error_hints.get(e.status_code, "Check API permissions and principal validity")
        return {'status': 'failed', 'message': f'API error ({e.status_code}): {hint}'}
        
    except Exception as e:
        return {'status': 'failed', 'message': f'Unexpected error: {str(e)}'}



def setup_workspace_administrators(workspace_client: FabricWorkspaceApiClient, fabric_admins_csv: str = None) -> dict:
    """
    Add administrators to a Microsoft Fabric workspace.
    
    Args:
        workspace_client: Authenticated FabricWorkspaceApiClient instance
        fabric_admins_csv: Comma-separated string of administrators (UPNs or GUIDs)
        
    Returns:
        Dict with operation results including counts of added, skipped, and failed assignments
    """
    # Parse comma-separated input
    if not fabric_admins_csv:
        print("ℹ️ No administrators specified - skipping workspace administrator setup")
        return {'added': 0, 'skipped': 0, 'failed': 0, 'errors': []}
    
    # Split by comma and clean up whitespace
    admins_to_add = [admin.strip() for admin in fabric_admins_csv.split(',') if admin.strip()]
    
    if not admins_to_add:
        print("ℹ️ No valid administrators found - skipping workspace administrator setup")
        return {'added': 0, 'skipped': 0, 'failed': 0, 'errors': []}
    
    print(f"📋 Parsed {len(admins_to_add)} administrator(s): {', '.join(admins_to_add)}")
    print(f"👥 Setting up workspace administrators...")
    
    # Initialize Graph API client
    try:
        graph_client = create_graph_client()
        print("✅ Graph API client authenticated successfully")
    except Exception as e:
        print(f"❌ WARNING: Failed to authenticate with Graph APIs: {str(e)}")
        graph_client = None
    
    # Get existing admin principals for this workspace
    existing_admin_principals = get_existing_admin_principals(workspace_client)
    
    workspace_stats = {'added': 0, 'skipped': 0, 'failed': 0, 'errors': []}
    
    # Process administrators (UPNs and object IDs with Graph API resolution)
    print(f"    👥 Adding administrators...")
    
    for admin_identifier in admins_to_add:
        result = add_workspace_admin(workspace_client, admin_identifier, existing_admin_principals, graph_client)
        
        if result['status'] == 'success':
            workspace_stats['added'] += 1
        elif result['status'] == 'skipped':
            workspace_stats['skipped'] += 1
        else:  # failed
            workspace_stats['failed'] += 1
            workspace_stats['errors'].append(f"{admin_identifier}: {result['message']}")
    
    # Print workspace summary
    total_requested = len(admins_to_add)
    print(f"    📊 Workspace administrators summary - Added: {workspace_stats['added']}, Skipped: {workspace_stats['skipped']}, Failed: {workspace_stats['failed']}, Total: {total_requested}")
    
    # Show error details if any failures occurred
    if workspace_stats['errors']:
        print(f"    ⚠️ Errors in workspace administrator setup:")
        for error in workspace_stats['errors'][:3]:  # Show first 3 errors
            print(f"       • {error}")
        if len(workspace_stats['errors']) > 3:
            print(f"       ... and {len(workspace_stats['errors']) - 3} more error(s)")
    
    if workspace_stats['added'] > 0 or workspace_stats['skipped'] > 0:
        return workspace_stats
    elif workspace_stats['failed'] > 0:
        print(f"❌ Failed to add workspace administrators")
        return None
    else:
        print(f"✅ No administrators to add")
        return workspace_stats

##########################
# Command line arguments #
##########################

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Add administrators to a Microsoft Fabric workspace')
    parser.add_argument('--workspace-id', required=True,
                        help='ID of the workspace to add administrators to')
    parser.add_argument('--fabricAdmins-csv', required=True,
                        help='Comma-separated list of administrators (UPNs or GUIDs). Example: user1@contoso.com,user2@contoso.com,12345678-1234-1234-1234-123456789012')
    args = parser.parse_args()

    print(f"🚀 Starting Microsoft Fabric workspace administrator management")
    print(f"📁 Workspace ID: {args.workspace_id}")
    print(f"📋 Administrators (CSV): {args.fabricAdmins_csv}")
    print("-" * 60)

    # Initialize Fabric API clients
    try:
        from fabric_auth import authenticate_workspace
    
        workspace_client = authenticate_workspace(args.workspace_id)
        if not workspace_client:
            print("❌ Failed to authenticate workspace-specific Fabric API client")
            sys.exit(1)
        print("✅ Fabric Workspace API client authenticated successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to authenticate with Fabric APIs")
        print(f"   Details: {str(e)}")
        print("   Solution: Please ensure you are logged in with Azure CLI: az login")
        sys.exit(1)

    # Setup workspace administrators
    result = setup_workspace_administrators(
        workspace_client=workspace_client,
        fabric_admins_csv=args.fabricAdmins_csv
    )

    if result is None:
        print("❌ Failed to setup workspace administrators")
        sys.exit(1)
    else:
        print(f"✅ Workspace administrator setup completed!")
        print(f"📊 Summary: Added {result['added']}, Skipped {result['skipped']}, Failed {result['failed']}")
        sys.exit(0)

if __name__ == "__main__":
    main()