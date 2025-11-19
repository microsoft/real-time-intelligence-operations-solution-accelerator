#!/usr/bin/env python3
"""
Fabric Activator (Reflex) Setup Script

This script creates or updates a Microsoft Fabric Activator (Reflex) in a specified workspace.
It loads activator configuration from a JSON file, encodes it to Base64, and creates or updates 
the activator using the Fabric API.

Usage:
    python fabric_activator.py --workspace-id "workspace-id" --activator-name "My Activator" --activator-file "ReflexEntities.json"
    
    Optional parameters can be provided to customize the activator:
    python fabric_activator.py --workspace-id "workspace-id" --activator-name "My Activator" --activator-file "ReflexEntities.json" --description "My activator description"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Contributor permissions in the target workspace
"""

import os
import sys
import json
import base64
import argparse
import re
from typing import Dict, Any, Optional

# Add current directory to path so we can import fabric_api
sys.path.append(os.path.dirname(__file__))

from fabric_api import FabricWorkspaceApiClient, FabricApiError

def transform_activator_config(activator_config: list,
                              eventstream_id: str = None,
                              eventstream_name: str = None,
                              activator_alerts_email: str = None) -> list:
    """
    Transform activator configuration with dynamic values.
    
    Args:
        activator_config: The original activator configuration list
        eventstream_id: ID of the eventhouse stream for the activator (optional)
        eventstream_name: Name for the event source (optional)
        activator_alerts_email: Email address to replace in alert configurations (optional)
        
    Returns:
        Transformed activator configuration list
    """
    print(f"📝 Updating activator configuration with dynamic values...")
    
    if eventstream_id:
        # Update eventstreamSource entities with the new artifact ID
        for entity in activator_config:
            if entity.get('type') == 'eventstreamSource-v1':
                if 'payload' in entity and 'metadata' in entity['payload']:
                    original_id = entity['payload']['metadata'].get('eventstreamArtifactId')
                    entity['payload']['metadata']['eventstreamArtifactId'] = eventstream_id
                    print(f"   Updated eventstreamArtifactId from '{original_id}' to '{eventstream_id}'")
    else:
        print(f"   Skipping eventstreamArtifactId updates (eventstream_id not provided)")
    
    if eventstream_name:
        # Update event source names
        for entity in activator_config:
            if entity.get('type') == 'eventstreamSource-v1':
                if 'payload' in entity and 'name' in entity['payload']:
                    original_name = entity['payload']['name']
                    entity['payload']['name'] = eventstream_name
                    print(f"   Updated event source name from '{original_name}' to '{eventstream_name}'")
    else:
        print(f"   Skipping event source name updates (eventstream_name not provided)")
    
    if activator_alerts_email:
        # Email regex pattern - matches standard email format
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Update email addresses in rule definitions using regex
        emails_updated = 0
        found_emails = set()
        
        for entity in activator_config:
            if entity.get('type') == 'timeSeriesView-v1':
                payload = entity.get('payload', {})
                definition = payload.get('definition', {})
                if definition.get('type') == 'Rule':
                    instance_str = definition.get('instance', '')
                    if instance_str:
                        try:
                            # Find all email addresses in the instance string using regex
                            found_emails_in_instance = re.findall(email_pattern, instance_str)
                            found_emails.update(found_emails_in_instance)
                            
                            # Replace all found email addresses with the new email
                            updated_instance_str = instance_str
                            for old_email in found_emails_in_instance:
                                updated_instance_str = updated_instance_str.replace(old_email, activator_alerts_email)
                                emails_updated += 1
                                print(f"   Updated email from '{old_email}' to '{activator_alerts_email}'")
                            
                            # Update the instance string
                            definition['instance'] = updated_instance_str
                            
                        except Exception as e:
                            print(f"   Warning: Could not process instance for email replacement: {e}")
        
        if emails_updated > 0:
            print(f"   Updated {emails_updated} email address(es) in activator rules")
            print(f"   Found and replaced emails: {', '.join(found_emails)}")
        else:
            print(f"   No email addresses found to update")
    else:
        print(f"   Skipping email address updates (activator_alerts_email not provided)")
    
    return activator_config

def setup_activator(workspace_id: str,
                   activator_file_path: str,
                   activator_name: str = "rti_activator",
                   activator_description: str = None,
                   eventstream_id: str = None,
                   eventstream_name: str = None,
                   activator_alerts_email: str = None):
    """
    Create or update an Activator (Reflex) in the specified workspace.
    
    Args:
        workspace_id: ID of the workspace where the activator will be created (required)
        activator_file_path: Path to the JSON file containing the activator configuration (required)
        activator_name: Name for the activator (required)
        activator_description: Description for the activator (optional)
        eventstream_id: ID of the eventhouse stream for the activator (optional)
        eventstream_name: Name for the event source (optional)
        activator_alerts_email: Email address to replace in alert configurations (optional)

    Returns:
        Dictionary with activator information if successful
        
    Raises:
        Exception: If activator creation/update fails
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

        # Verify the activator file exists
        if not os.path.exists(activator_file_path):
            print(f"❌ Activator file not found: {activator_file_path}")
            raise FileNotFoundError(f"Activator file not found: {activator_file_path}")

        # Load JSON configuration
        print(f"📄 Loading activator configuration from: {activator_file_path}")
        with open(activator_file_path, "r", encoding="utf-8") as json_file:
            activator_config = json.load(json_file)

        # Transform the activator configuration with dynamic values
        activator_config = transform_activator_config(
            activator_config=activator_config,
            eventstream_id=eventstream_id,
            eventstream_name=eventstream_name,
            activator_alerts_email=activator_alerts_email
        )

        # Encode activator configuration to Base64
        print("🔄 Encoding activator configuration to Base64...")
        activator_json_str = json.dumps(activator_config)
        activator_base64 = base64.b64encode(activator_json_str.encode('utf-8')).decode('utf-8')
        print(f"✅ Activator configuration encoded ({len(activator_base64)} characters)")

        # Check if activator already exists
        print("🔍 Checking for existing activator...")
        existing_activator = fabric_client.get_activator_by_name(activator_name)
        
        if existing_activator:
            # Update the existing activator
            print(f"🔄 Updating existing activator '{activator_name}' (ID: {existing_activator.get('id')})...")
            activator_id = existing_activator.get('id')
            
            update_success = fabric_client.update_activator_definition(
                activator_id=activator_id,
                definition_base64=activator_base64
            )
            
            if update_success:
                print(f"✅ Successfully updated activator '{activator_name}'")
                return existing_activator
            else:
                raise Exception(f"Failed to update activator '{activator_name}'")
        else:
            # Create a new activator
            print(f"📊 Creating new activator '{activator_name}'...")
            activator_result = fabric_client.create_activator(
                display_name=activator_name,
                description=activator_description or f"Activator: {activator_name}",
                definition_base64=activator_base64
            )
            
            activator_id = activator_result.get('id')

        print(f"✅ Activator setup completed successfully")
        print(f"   Activator ID: {activator_id}")
        print(f"   Activator Name: {activator_name}")
        
        return activator_result if not existing_activator else existing_activator
        
    except (FabricApiError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"❌ Error in activator setup: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute the activator setup."""
    parser = argparse.ArgumentParser(
        description="Create or update an Activator (Reflex) in a Fabric workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with required parameters:
  python fabric_activator.py --workspace-id "12345678-1234-1234-1234-123456789012" --activator-name "MyActivator" --activator-file "ReflexEntities.json"
  
  # With custom parameters to override JSON values:
  python fabric_activator.py --workspace-id "12345678-1234-1234-1234-123456789012" --activator-name "MyActivator" --activator-file "ReflexEntities.json" --description "My activator description" --eventhouse-stream-id "87654321-4321-4321-4321-210987654321"
  
  Note: Activator names can contain spaces and special characters.
        """
    )
    
    parser.add_argument(
        "--workspace-id", 
        required=True, 
        help="ID of the workspace where the activator will be created"
    )
    
    parser.add_argument(
        "--activator-file", 
        required=True, 
        help="Path to the JSON file containing the activator configuration"
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
    
    parser.add_argument(
        "--eventstream-id", 
        help="ID of the eventstream for the activator (optional)"
    )
    
    parser.add_argument(
        "--eventstream-name", 
        help="Name for the eventstream (optional, preserves original if not provided)"
    )
    
    parser.add_argument(
        "--activator-alerts-email", 
        help="Email address to replace in alert configurations (optional)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"📊 Activator Setup Script")
    print(f"  Workspace ID: {args.workspace_id}")
    print(f"  Activator File: {args.activator_file}")
    print(f"  Activator Name: {args.activator_name or '(not provided)'}")
    print(f"  Description: {args.activator_description or '(not provided)'}")
    print(f"  Eventstream ID: {args.eventstream_id or '(not provided)'}")
    print(f"  Eventstream Name: {args.eventstream_name or '(preserve original)'}")
    print(f"  Activator Alerts Email: {args.activator_alerts_email or '(not provided)'}")
    print("=" * 60)
    
    # Execute the main logic
    try:
        result = setup_activator(
            workspace_id=args.workspace_id,
            activator_file_path=args.activator_file,
            activator_name=args.activator_name,
            activator_description=args.activator_description,
            eventstream_id=args.eventstream_id,
            eventstream_name=args.eventstream_name,
            activator_alerts_email=args.activator_alerts_email
        )
        
        print(f"\n🎉 Activator setup completed successfully.")
        print(f"Activator ID: {result.get('id')}")
        print(f"Activator Name: {result.get('displayName')}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()