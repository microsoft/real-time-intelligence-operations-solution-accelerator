#!/usr/bin/env python3
"""
Workspace removal orchestrator script for Real-Time Intelligence Operations Solution Accelerator.

This script coordinates the execution of workspace removal functions
in the correct order, with proper error handling and logging. It uses environment
variables for configuration and calls each function directly.

Functions executed in order:
1. authenticate - Authenticate Fabric API client
2. lookup_workspace - Look up workspace by name
3. delete_connection - Delete Event Hub connection
4. delete_workspace - Delete the Fabric workspace

Usage:
    python delete_fabric_rti.py

Environment Variables (from Bicep outputs):
    AZURE_ENV_NAME - Name of the Azure environment
    SOLUTION_SUFFIX - Required suffix to append to default workspace name
    FABRIC_WORKSPACE_NAME - Name of the Fabric workspace (optional, uses default if not provided)
    FABRIC_EVENT_HUB_CONNECTION_NAME - Name of the Event Hub connection (optional, uses default if not provided)
"""

import os
import sys
from datetime import datetime

# Add current directory to path so we can import local modules
sys.path.append(os.path.dirname(__file__))

# Import removal functions
from fabric_auth import authenticate
from fabric_workspace_delete import lookup_workspace, delete_workspace
from fabric_connection_delete import delete_connection
from fabric_common_utils import get_required_env_var, print_step, print_steps_summary

def main():
    # Calculate repository root directory (3 levels up from this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    
    # Load configuration from environment variables
    solution_name = get_required_env_var("AZURE_ENV_NAME")
    solution_suffix = get_required_env_var("SOLUTION_SUFFIX")
    workspace_name = os.getenv("FABRIC_WORKSPACE_NAME", f"Real-Time Intelligence for Operations - {solution_suffix}")
    connection_name = os.getenv("FABRIC_EVENT_HUB_CONNECTION_NAME", f"rti_eventhub_connection_{solution_suffix}")

    # Show removal summary
    print(f"🏭 {solution_name} Workspace Removal")
    print("="*60)
    print(f"Target workspace name: {workspace_name}")
    print(f"Target connection name: {connection_name}")
    print(f"Solution Suffix: {solution_suffix}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    executed_steps = []
    failed_steps = []
    
    # Step 1: Authenticate Fabric API client
    print_step(1, 4, "Authenticating Fabric API client")
    fabric_client = authenticate()
    if fabric_client is None:
        print(f"\n❌ Authentication failed. Cannot proceed with workspace removal.")
        failed_steps.append("authenticate")
        print_steps_summary(solution_name, solution_suffix, executed_steps, failed_steps)
        sys.exit(1)
    executed_steps.append("authenticate")
    
    # Step 2: Look up workspace by name
    print_step(2, 4, "Looking up workspace", workspace_name=workspace_name)
    lookup_result = lookup_workspace(
        fabric_client,
        workspace_name=workspace_name
    )
    if lookup_result is None:
        print("⚠️ Warning: Could not find workspace. Continuing with connection cleanup...")
        failed_steps.append("lookup_workspace")
        workspace_id = None
    else:
        executed_steps.append("lookup_workspace")
        workspace_id, workspace_display_name = lookup_result
    
    # Step 3: Delete Event Hub connection
    print_step(3, 4, "Deleting Event Hub connection", connection_name=connection_name)
    try:
        connection_result = delete_connection(
            fabric_client,
            connection_name=connection_name
        )
        if connection_result is not None:
            print(f"Connection deleted successfully: {connection_result}")
            executed_steps.append("delete_connection")
        else:
            print("⚠️ Warning: Connection not found, nothing to delete.")
            executed_steps.append("delete_connection")
    except Exception as e:
        print(f"⚠️ Warning: Could not delete connection: {e}. Continuing with workspace deletion...")
        failed_steps.append("delete_connection")
    
    # Step 4: Delete workspace (only if we found it)
    if workspace_id:
        print_step(4, 4, "Deleting workspace", workspace_id=workspace_id)
        try:
            result = delete_workspace(
                fabric_client,
                workspace_id=workspace_id
            )
            if result is not None:
                print(f"Workspace deleted successfully: {result}")
                executed_steps.append("delete_workspace")
            else:
                print("⚠️ Warning: Workspace not found during deletion, nothing to delete.")
                executed_steps.append("delete_workspace")
        except Exception as e:
            print(f"⚠️ Warning: Could not delete workspace: {e}")
            failed_steps.append("delete_workspace")
    else:
        print("⚠️ Skipping workspace deletion (workspace not found)")
        failed_steps.append("lookup_workspace")
    
    # Print final summary
    print_steps_summary(solution_name, solution_suffix, executed_steps, failed_steps)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⚠️ Workspace removal interrupted by user")
        sys.exit(1)
    except UnicodeEncodeError as e:
        print(f"\n[ERROR] Unicode encoding error detected:")
        print(f"Your console doesn't support the Unicode characters used in this script.")
        print(f"This is common on Windows systems with certain console configurations.")
        print(f"\nSolutions:")
        print(f"1. Run the script in Windows Terminal or VS Code terminal")
        print(f"2. Use PowerShell 7+ instead of Windows PowerShell")
        print(f"3. Set environment variable: set PYTHONIOENCODING=utf-8")
        print(f"4. Use command: chcp 65001 (to set UTF-8 codepage)")
        print(f"\nTechnical details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
