#!/usr/bin/env python3
"""
Fabric Activator (Reflex) Creation Script

This script creates a Microsoft Fabric Activator (Reflex) in a specified workspace if it doesn't exist.
It creates the activator with minimal configuration, and the detailed definition should be 
updated using fabric_activator_definition.py script.

Usage:
    python fabric_activator.py --workspace-id "workspace-id" --activator-name "My Activator"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Contributor permissions in the target workspace
"""

import os
import sys
import argparse
from typing import Optional

# Add current directory to path so we can import fabric_api
sys.path.append(os.path.dirname(__file__))

from fabric_api import FabricWorkspaceApiClient, FabricApiError

def create_activator(workspace_id: str,
                    activator_name: str = "rti_activator",
                    activator_description: str = None):
    """
    Create an Activator (Reflex) in the specified workspace if it doesn't exist.
    
    Args:
        workspace_id: ID of the workspace where the activator will be created (required)
        activator_name: Name for the activator (required)
        activator_description: Description for the activator (optional)

    Returns:
        Dictionary with activator information if successful
        
    Raises:
        Exception: If activator creation fails
    """
    try:
        # Validate and clean activator name
        if not activator_name or not activator_name.strip():
            raise ValueError("activator_name is required and cannot be empty")
        
        activator_name = activator_name.strip()
        if not activator_name:
            raise ValueError("activator_name cannot be empty after stripping")
        
        # Initialize the Fabric API client
        print("🚀 Initializing Fabric API client...")
        fabric_client = FabricWorkspaceApiClient(workspace_id=workspace_id)

        # Check if activator already exists
        print("🔍 Checking for existing activator...")
        existing_activator = fabric_client.get_activator_by_name(activator_name)
        
        if existing_activator:
            print(f"✅ Activator '{activator_name}' already exists (ID: {existing_activator.get('id')})")
            return existing_activator
        else:
            # Create a new activator with minimal configuration
            print(f"📊 Creating new activator '{activator_name}'...")
            activator_result = fabric_client.create_activator(
                display_name=activator_name,
                description=activator_description or f"Activator: {activator_name}"
            )
            
            activator_id = activator_result.get('id')
            print(f"✅ Successfully created activator '{activator_name}' (ID: {activator_id})")
            print(f"⚠️  Note: Use fabric_activator_definition.py to set up the activator configuration")
            
            return activator_result
        
    except FabricApiError as e:
        print(f"❌ Error in activator creation: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute the activator creation."""
    parser = argparse.ArgumentParser(
        description="Create an Activator (Reflex) in a Fabric workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with required parameters:
  python fabric_activator.py --workspace-id "12345678-1234-1234-1234-123456789012" --activator-name "MyActivator"
  
  Note: Activator names can contain spaces and special characters.
        Use fabric_activator_definition.py to configure the activator after creation.
        """
    )
    
    parser.add_argument(
        "--workspace-id", 
        required=True, 
        help="ID of the workspace where the activator will be created"
    )
    
    parser.add_argument(
        "--activator-name",
        default="rti_activator",
        help="Name for the activator"
    )
    
    parser.add_argument(
        "--activator-description", 
        help="Description for the activator (optional)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"📊 Activator Creation Script")
    print(f"  Workspace ID: {args.workspace_id}")
    print(f"  Activator Name: {args.activator_name or '(not provided)'}")
    print(f"  Description: {args.activator_description or '(not provided)'}")
    print("=" * 60)
    
    # Execute the main logic
    try:
        result = create_activator(
            workspace_id=args.workspace_id,
            activator_name=args.activator_name,
            activator_description=args.activator_description
        )
        
        print(f"\n🎉 Activator creation completed successfully.")
        print(f"Activator ID: {result.get('id')}")
        print(f"Activator Name: {result.get('displayName')}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()