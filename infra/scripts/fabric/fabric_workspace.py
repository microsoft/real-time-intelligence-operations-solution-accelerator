#!/usr/bin/env python3
"""
Fabric Workspace Creation and Capacity Assignment Module

This module provides workspace creation and capacity assignment functionality for Microsoft Fabric operations.
It creates a new Microsoft Fabric workspace (if it doesn't exist) and assigns it 
to a specified capacity.

Usage:
    python fabric_workspace.py --capacity-name "MyCapacity" [--workspace-name "MyWorkspace"]

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Appropriate permissions to create workspaces and assign capacities
"""

import argparse
import sys
from fabric_api import FabricApiClient, FabricWorkspaceApiClient, FabricApiError

def setup_workspace(fabric_client: FabricApiClient, capacity_name: str, workspace_name: str) -> object:
    """
    Create a workspace (if it doesn't exist) and assign it to the specified capacity.
    
    Args:
        fabric_client: Authenticated FabricApiClient instance
        capacity_name: Name of the capacity to assign the workspace to
        workspace_name: Name of the workspace to create
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"🔍 Searching for capacity: '{capacity_name}'")

        capacity = fabric_client.get_capacity(capacity_name)
        if not capacity:
            print(f"❌ Capacity '{capacity_name}' not found. Exiting.")
            return None

        capacity_id = capacity['id']
        print(f"✅ Capacity found: ID = {capacity_id}, Name = {capacity['displayName']}")

        existing_workspace = fabric_client.get_workspace(workspace_name)
        
        if existing_workspace:
            workspace_id = existing_workspace['id']
            print(f"ℹ️  Using existing workspace: {workspace_name}")
        else:
            print(f"📁 Creating new workspace: '{workspace_name}'")
            try:
                workspace_id = fabric_client.create_workspace(name=workspace_name)
                print(f"✅ Successfully created workspace: {workspace_name} (ID: {workspace_id})")
            except FabricApiError as e:
                if e.status_code == 409:
                    print(f"ℹ️ Workspace '{workspace_name}' already exists")
                    workspace_id = fabric_client.get_workspace(workspace_name)['id']
                else:
                    print(f"❌ Failed to create workspace: {e}")
                    return None
        
        workspace_setup_response = {"id": workspace_id }

        print(f"🔧 Initializing workspace-specific client...")
        workspace_client = FabricWorkspaceApiClient(workspace_id=workspace_id)
        
        print(f"⚡ Assigning workspace '{workspace_name}' to capacity '{capacity_name}'...")
        try:
            workspace_client.assign_to_capacity(capacity_id)
            print(f"✅ Successfully assigned workspace to capacity!")
        except FabricApiError as e:
            print(f"❌ FabricApiError ({e.status_code}): {e}")
            return None
        
        print(f"🔍 Verifying workspace assignment...")
        try:
            workspace_info = workspace_client.get_workspace_info()
            assigned_capacity_id = workspace_info.get('capacityId')
            
            if assigned_capacity_id == capacity_id:
                print(f"✅ Verification successful: Workspace is assigned to capacity {capacity_name}")
                
                print(f"\n📊 Workspace Summary:")
                print(f"   Name: {workspace_info.get('displayName', 'Unknown')}")
                print(f"   ID: {workspace_info.get('id', 'Unknown')}")
                print(f"   Capacity: {capacity['displayName']} ({capacity_id})")
                print(f"   Type: {workspace_info.get('type', 'Unknown')}")
                
                items = workspace_client.get_items()
                print(f"   Items: {len(items)} total")
                
                return workspace_setup_response
            else:
                print(f"⚠️  Warning: Workspace shows different capacity assignment: {assigned_capacity_id}")
                return None
                  
        except FabricApiError as e:
            print(f"⚠️  Could not verify assignment: {e}")
            print(f"✅ Workspace creation and assignment completed (verification failed)")
            return workspace_setup_response
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def main():
    """Main function to handle command line arguments and execute the workspace creation."""
    parser = argparse.ArgumentParser(
        description="Create a Fabric workspace and assign it to a capacity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_workspace.py --capacity-name "Dev Capacity" --workspace-name "Development Workspace"
        """
    )
    
    parser.add_argument(
        "--capacity-name", 
        required=True, 
        help="Name of the capacity to assign the workspace to"
    )
    
    parser.add_argument(
        "--workspace-name", 
        required=True, 
        help="Name of the workspace to create"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the main logic
    fabric_client = FabricApiClient()
    
    result = setup_workspace(
        fabric_client=fabric_client,
        capacity_name=args.capacity_name,
        workspace_name=args.workspace_name
    )
    
    print(f"\n✅ Workspace ID: {result.get('id') if result else 'Failed'}")
    print(f"✅ Workspace Name: {args.workspace_name}")


if __name__ == "__main__":
    main()
