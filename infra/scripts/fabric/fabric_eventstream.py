#!/usr/bin/env python3
"""
Fabric Eventstream Creation Script

This script creates a Microsoft Fabric Eventstream in a specified workspace if it doesn't exist.
It creates the eventstream with minimal configuration, and the detailed definition should be 
updated using fabric_eventstream_definition.py script.

Usage:
    python fabric_eventstream.py --workspace-id "workspace-id" --eventstream-name "My Eventstream"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Contributor permissions in the target workspace
"""

import argparse
import sys
from fabric_api import FabricWorkspaceApiClient, FabricApiError

def create_eventstream(workspace_id: str,
                      eventstream_name: str = "rti_eventstream"):
    """
    Create an Eventstream in the specified workspace if it doesn't exist.
    
    Args:
        workspace_id: ID of the workspace where the eventstream will be created (required)
        eventstream_name: Name for the eventstream (required, whitespaces will be removed)

    Returns:
        Dictionary with eventstream information if successful
        
    Raises:
        Exception: If eventstream creation fails
    """
    try:
        # Validate and clean eventstream name (remove whitespaces)
        if not eventstream_name or not eventstream_name.strip():
            raise ValueError("eventstream_name is required and cannot be empty")
        
        eventstream_name = eventstream_name.strip().replace(" ", "")
        if not eventstream_name:
            raise ValueError("eventstream_name cannot be empty after removing whitespaces")
        
        # Initialize the Fabric API client
        print("🚀 Initializing Fabric API client...")
        fabric_client = FabricWorkspaceApiClient(workspace_id=workspace_id)

        # Check if eventstream already exists
        print("🔍 Checking for existing eventstream...")
        existing_eventstream = fabric_client.get_eventstream_by_name(eventstream_name)
        
        if existing_eventstream:
            print(f"✅ Eventstream '{eventstream_name}' already exists (ID: {existing_eventstream.get('id')})")
            return existing_eventstream
        else:
            # Create a new eventstream with minimal configuration
            print(f"📊 Creating new eventstream '{eventstream_name}'...")
            eventstream_result = fabric_client.create_eventstream(
                display_name=eventstream_name,
                description=f"Eventstream: {eventstream_name}"
            )
            
            eventstream_id = eventstream_result.get('id')
            print(f"✅ Successfully created eventstream '{eventstream_name}' (ID: {eventstream_id})")
            print(f"⚠️  Note: Use fabric_eventstream_definition.py to set up the eventstream configuration")
            
            return eventstream_result
        
    except FabricApiError as e:
        print(f"❌ Error in eventstream creation: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute the eventstream creation."""
    parser = argparse.ArgumentParser(
        description="Create an Eventstream in a Fabric workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with required parameters:
  python fabric_eventstream.py --workspace-id "12345678-1234-1234-1234-123456789012" --eventstream-name "MyEventstream"
  
  Note: Eventstream names cannot contain whitespaces and will be automatically removed.
        Use fabric_eventstream_definition.py to configure the eventstream after creation.
        """
    )
    
    parser.add_argument(
        "--workspace-id", 
        required=True, 
        help="ID of the workspace where the eventstream will be created"
    )
    
    parser.add_argument(
        "--eventstream-name",
        default="rti_eventstream",
        help="Name for the eventstream (whitespaces will be automatically removed)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"📊 Eventstream Creation Script")
    print(f"  Workspace ID: {args.workspace_id}")
    print(f"  Eventstream Name: {args.eventstream_name or '(not provided)'}")
    print("=" * 60)
    
    # Execute the main logic
    try:
        result = create_eventstream(
            workspace_id=args.workspace_id,
            eventstream_name=args.eventstream_name
        )
        
        print(f"\n🎉 Eventstream creation completed successfully.")
        print(f"Eventstream ID: {result.get('id')}")
        print(f"Eventstream Name: {result.get('displayName')}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()