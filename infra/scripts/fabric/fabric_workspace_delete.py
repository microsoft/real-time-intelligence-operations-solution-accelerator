#!/usr/bin/env python3
"""
Fabric Workspace Deletion Module

This module provides workspace deletion functionality for Microsoft Fabric operations.

Usage:
    python fabric_workspace_delete.py --workspace-name "MyWorkspace"
    python fabric_workspace_delete.py --workspace-id "12345678-1234-1234-1234-123456789012"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Appropriate permissions to delete workspaces
"""

import argparse
import sys
from fabric_api import FabricApiClient, FabricApiError

def lookup_workspace(fabric_client: FabricApiClient, workspace_name: str):
    """
    Look up workspace by name.
    
    Args:
        fabric_client: Authenticated FabricApiClient instance
        workspace_name: Workspace name to look up
        
    Returns:
        Tuple of (workspace_id, workspace_display_name) if successful, None if failed
    """
    try:
        print(f"Looking up workspace: '{workspace_name}'")
        workspaces = fabric_client.get_workspaces()
        workspace = next(
            (w for w in workspaces if w['displayName'].lower() == workspace_name.lower()), None)
        
        if not workspace:
            print(f"   Workspace '{workspace_name}' not found")
            return None
        
        workspace_id = workspace['id']
        workspace_display_name = workspace['displayName']
        print(f"✅ Found workspace: '{workspace_display_name}' (ID: {workspace_id})")
        result = workspace_id, workspace_display_name
            
        print(f"✅ Successfully completed: lookup_workspace")
        return result
        
    except FabricApiError as e:
        if e.status_code == 401:
            print(f"⚠️ WARNING: Unauthorized access to Fabric APIs")
            print("   ⚠️ WARNING: Please review your Fabric permissions and licensing:")
            print("   📋 Check these resources:")
            print("   • Fabric licenses: https://learn.microsoft.com/en-us/fabric/enterprise/licenses")
            print("   • Identity support: https://learn.microsoft.com/en-us/rest/api/fabric/articles/identity-support")
            print("   • Create Entra app: https://learn.microsoft.com/en-us/rest/api/fabric/articles/get-started/create-entra-app")
            print("   Solution: Ensure you have proper Fabric licensing and permissions")
        elif e.status_code == 404:
            print(f"WARNING: Resource not found")
        elif e.status_code == 403:
            print(f"⚠️ WARNING: Access denied")
            print("   Solution: Ensure you have appropriate permissions")
        else:
            print(f"⚠️ WARNING: Fabric API error")
        print(f"   Status Code: {e.status_code}")
        print(f"   Details: {str(e)}")
        print(f"❌ Exception while executing lookup_workspace: {e}")
        return None
    except Exception as e:
        print(f"WARNING: Unexpected error during workspace lookup: {str(e)}")
        print(f"❌ Exception while executing lookup_workspace: {e}")
        return None

def delete_workspace(fabric_client: FabricApiClient, workspace_id: str):
    """
    Delete a Fabric workspace by ID.
    
    Args:
        fabric_client: Authenticated FabricApiClient instance
        workspace_id: ID of the workspace to delete
        
    Returns:
        Workspace ID if deletion successful, None if workspace not found
        
    Raises:
        FabricApiError: If deletion fails due to unexpected error
    """
    try:
        deleted_workspace_id = fabric_client.delete_workspace(workspace_id)
        if deleted_workspace_id:
            print(f"✅ Successfully completed: delete_workspace (deleted: {deleted_workspace_id})")
            return deleted_workspace_id
        else:
            print(f"Workspace {workspace_id} was not found")
            return None
    except FabricApiError as e:
        print(f"❌ Exception while executing delete_workspace: {e}")
        raise
    except Exception as e:
        print(f"❌ Exception while executing delete_workspace: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute workspace deletion."""
    parser = argparse.ArgumentParser(
        description="Delete a Fabric workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_workspace_delete.py --workspace-name "TestWorkspace"
  python fabric_workspace_delete.py --workspace-id "12345678-1234-1234-1234-123456789012"
        """
    )
    
    parser.add_argument(
        "--workspace-name",
        help="Name of the workspace to delete"
    )
    
    parser.add_argument(
        "--workspace-id",
        help="ID of the workspace to delete"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate arguments
    if not args.workspace_name and not args.workspace_id:
        print("❌ Error: Must specify either --workspace-name or --workspace-id")
        sys.exit(1)
    
    if args.workspace_name and args.workspace_id:
        print("❌ Error: Cannot specify both --workspace-name and --workspace-id")
        sys.exit(1)
    
    # Print configuration
    print(f"🗑️  Fabric Workspace Deletion")
    print("=" * 60)
    if args.workspace_name:
        print(f"Workspace Name: {args.workspace_name}")
    else:
        print(f"Workspace ID: {args.workspace_id}")
    print("=" * 60)
    
    try:
        # Authenticate
        print(f"🔐 Authenticating Fabric API client...")
        fabric_client = FabricApiClient()
        print(f"✅ Authentication successful")
        
        workspace_id = args.workspace_id
        workspace_name = args.workspace_name
        
        # Look up workspace if name provided
        if workspace_name:
            print(f"🔍 Looking up workspace by name...")
            lookup_result = lookup_workspace(fabric_client, workspace_name)
            if not lookup_result:
                print(f"❌ Workspace '{workspace_name}' not found")
                sys.exit(1)
            workspace_id, workspace_display_name = lookup_result
        else:
            workspace_display_name = workspace_id
        
        # Delete workspace
        print(f"🗑️  Deleting workspace...")
        result = delete_workspace(fabric_client, workspace_id)
        
        if result:
            print(f"\n🎉 Workspace deleted successfully!")
            print(f"✅ Deleted workspace ID: {result}")
            sys.exit(0)
        else:
            print(f"\n❌ Workspace deletion failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⚠️  Workspace deletion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)