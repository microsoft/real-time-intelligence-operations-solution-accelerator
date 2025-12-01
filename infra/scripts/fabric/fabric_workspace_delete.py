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
        print(f"❌ FabricApiError ({e.status_code}): {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
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
    
    # Execute the main logic
    fabric_client = FabricApiClient()
    
    workspace_id = args.workspace_id
    workspace_name = args.workspace_name
    
    # Look up workspace if name provided
    if workspace_name:
        lookup_result = lookup_workspace(fabric_client, workspace_name)
        if not lookup_result:
            print(f"❌ Workspace '{workspace_name}' not found")
            sys.exit(1)
        workspace_id, workspace_display_name = lookup_result
    
    # Delete workspace
    result = delete_workspace(fabric_client, workspace_id)
    
    print(f"\n✅ Deleted workspace ID: {result if result else 'Failed'}")


if __name__ == "__main__":
    main()