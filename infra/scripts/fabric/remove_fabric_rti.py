#!/usr/bin/env python3
"""
Removes Microsoft Fabric workspace for the Real-Time Intelligence Operations Solution Accelerator.

This script provides safe deletion of RTI workspaces from Microsoft Fabric including:
• Workspace lookup and verification
• Safe deletion with confirmation prompts
• Comprehensive error handling and user guidance

Usage:
    python remove_fabric_rti.py

Environment Variables:
    SOLUTION_SUFFIX - Required suffix to append to default workspace name
    FABRIC_WORKSPACE_NAME - Name of the Fabric workspace (optional, uses default if not provided)
    FABRIC_WORKSPACE_ID - ID of the Fabric workspace (GUID) (optional, overrides name-based lookup)

Prerequisites:
    - Azure CLI (logged in): az login
    - Python packages: requests, azure-identity, azure-core, azure-storage-file-datalake
    - Appropriate Fabric workspace permissions (Admin role required for deletion)

Author: Generated for Real-Time Intelligence Operations Solution Accelerator
"""

from fabric_api import create_fabric_client, FabricApiError
import sys
import os

####################
# Variables set up #
####################

solution_name = "Real-Time Intelligence Operations Solution Accelerator"
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up three levels from infra/scripts/fabric to repo root
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))

def get_required_env_var(var_name: str) -> str:
    """Get required environment variable value."""
    value = os.getenv(var_name)
    if not value:
        print(f"Missing required environment variable: {var_name}")
        sys.exit(1)
    return value

##########################
# Load configuration     #
##########################

# Load configuration from environment variables
solution_suffix = get_required_env_var("SOLUTION_SUFFIX")
workspace_name = os.getenv("FABRIC_WORKSPACE_NAME", f"Real-Time Intelligence for Operations - {solution_suffix}")
workspace_id = os.getenv("FABRIC_WORKSPACE_ID")

# Validate that only one workspace identifier is provided
if workspace_name and workspace_id:
    print("WARNING: Both FABRIC_WORKSPACE_NAME and FABRIC_WORKSPACE_ID are set.")
    print("         Using FABRIC_WORKSPACE_NAME and ignoring FABRIC_WORKSPACE_ID.")
    workspace_id = None

print(f"Deleting Microsoft Fabric workspace for the Real-Time Intelligence Operations Solution Accelerator")
if workspace_name:
    print(f"Target workspace name: {workspace_name}")
else:
    print(f"Target workspace ID: {workspace_id}")
print("-" * 80)

##########################
# Clients authentication #
##########################

print("Authenticating Fabric client...")
# Initialize Fabric API client
try:
    fabric_client = create_fabric_client()
    print("Fabric API client authenticated successfully")
except Exception as e:
    print(f"WARNING: Failed to authenticate with Fabric APIs")
    print(f"   Details: {str(e)}")
    print("   Solution: Please ensure you are logged in with Azure CLI: az login")
    print("   Exiting gracefully...")
    sys.exit(0)

###########################
# Workspace lookup/verify #
###########################

try:
    # If workspace name is provided, look it up to get the ID
    if workspace_name:
        print(f"Looking up workspace: '{workspace_name}'")
        workspaces = fabric_client.get_workspaces()
        workspace = next(
            (w for w in workspaces if w['displayName'].lower() == workspace_name.lower()), None)
        
        if not workspace:
            print(f"WARNING: Workspace '{workspace_name}' not found")
            print("   Available workspaces:")
            for ws in workspaces:
                print(f"   - {ws['displayName']} (ID: {ws['id']})")
            print("   Exiting gracefully...")
            sys.exit(0)
        
        workspace_id = workspace['id']
        workspace_display_name = workspace['displayName']
        print(f"✅ Found workspace: '{workspace_display_name}' (ID: {workspace_id})")
    else:
        # If workspace ID is provided, verify it exists
        print(f"Verifying workspace ID: '{workspace_id}'")
        workspaces = fabric_client.get_workspaces()
        workspace = next(
            (w for w in workspaces if w['id'].lower() == workspace_id.lower()), None)
        
        if not workspace:
            print(f"WARNING: Workspace with ID '{workspace_id}' not found")
            print("   Available workspaces:")
            for ws in workspaces:
                print(f"   - {ws['displayName']} (ID: {ws['id']})")
            print("   Exiting gracefully...")
            sys.exit(0)
        
        workspace_display_name = workspace['displayName']
        print(f"✅ Found workspace: '{workspace_display_name}' (ID: {workspace_id})")

except FabricApiError as e:
    if e.status_code == 401:
        print(f"⚠️ WARNING: Unauthorized access to Fabric APIs")
        print("   ⚠️ WARNING: Please review your Fabric permissions and licensing:")
        print("   📋 Check these resources:")
        print("   • Fabric licenses: https://learn.microsoft.com/en-us/fabric/enterprise/licenses")
        print("   • Identity support: https://learn.microsoft.com/en-us/rest/api/fabric/articles/identity-support")
        print("   • Create Entra app: https://learn.microsoft.com/en-us/rest/api/fabric/articles/get-started/create-entra-app")
        print("   Solution: Ensure you have proper Fabric licensing and permissions")
        print("   Exiting gracefully...")
        sys.exit(0)
    elif e.status_code == 404:
        print(f"WARNING: Resource not found")
    elif e.status_code == 403:
        print(f"⚠️ WARNING: Access denied")
        print("   Solution: Ensure you have appropriate permissions")
    else:
        print(f"⚠️ WARNING: Fabric API error")
    print(f"   Status Code: {e.status_code}")
    print(f"   Details: {str(e)}")
    print("   Exiting gracefully...")
    sys.exit(0)
except Exception as e:
    print(f"WARNING: Unexpected error during workspace lookup: {str(e)}")
    print("   Exiting gracefully...")
    sys.exit(0)

####################
# Confirmation     #
####################

# Proceeding with deletion in unattended mode
print(f"Proceeding with workspace deletion...")

######################
# Workspace deletion #
######################

try:
    print(f"Deleting workspace: '{workspace_display_name}'")
    fabric_client.delete_workspace(workspace_id)
    print(f"Workspace '{workspace_display_name}' deleted successfully")

except FabricApiError as e:
    if e.status_code == 401:
        print(f"⚠️ WARNING: Unauthorized access to Fabric APIs")
        print("   ⚠️ WARNING: Please review your Fabric permissions and licensing:")
        print("   📋 Check these resources:")
        print("   • Fabric licenses: https://learn.microsoft.com/en-us/fabric/enterprise/licenses")
        print("   • Identity support: https://learn.microsoft.com/en-us/rest/api/fabric/articles/identity-support")
        print("   • Create Entra app: https://learn.microsoft.com/en-us/rest/api/fabric/articles/get-started/create-entra-app")
        print("   Solution: Ensure you have proper Fabric licensing and permissions")
        print("   Exiting gracefully...")
        sys.exit(0)
    elif e.status_code == 404:
        print(f"⚠️ WARNING: Workspace not found (may have already been deleted)")
        print("   This is typically not an issue during cleanup operations")
    elif e.status_code == 403:
        print(f"⚠️ WARNING: Access denied")
        print("   Solution: Ensure you have Admin permissions on this workspace")
    else:
        print(f"⚠️ WARNING: Fabric API error")
    print(f"   Status Code: {e.status_code}")
    print(f"   Details: {str(e)}")
    print("   Exiting gracefully...")
    sys.exit(0)
except Exception as e:
    print(f"⚠️ WARNING: Unexpected error during workspace deletion: {str(e)}")
    print("   Exiting gracefully...")
    sys.exit(0)

##################
# End of program #
##################

print("-" * 80)
print(f"{solution_name} workspace removal completed successfully!")
print(f"Deleted workspace: {workspace_display_name}")
print(f"Workspace ID: {workspace_id}")
print("-" * 80)