#!/usr/bin/env python3
"""
Fabric Activator (Reflex) Definition Update Script

This script updates the definition of an existing Microsoft Fabric Activator (Reflex) in a specified workspace.
It loads activator configuration from a JSON file, transforms it with dynamic values, encodes it to Base64, 
and updates the activator using the Fabric API.

Usage:
    python fabric_activator_definition.py --workspace-id "workspace-id" --activator-id "activator-id" --activator-file "ReflexEntities.json"
    
    Optional parameters can be provided to customize the activator configuration:
    python fabric_activator_definition.py --workspace-id "workspace-id" --activator-id "activator-id" --activator-file "ReflexEntities.json" --eventstream-id "eventstream-id" --activator-alerts-email "alerts@example.com"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Contributor permissions in the target workspace
    - Existing activator in the workspace
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
        # Update event names for timeSeriesView-v1 entities with definition type "Event"
        for entity in activator_config:
            if entity.get('type') == 'timeSeriesView-v1':
                payload = entity.get('payload', {})
                definition = payload.get('definition', {})
                if definition.get('type') == 'Event' and 'name' in payload:
                    original_name = payload['name']
                    payload['name'] = eventstream_name
                    print(f"   Updated event definition name from '{original_name}' to '{eventstream_name}'")
    else:
        print(f"   Skipping event name updates (eventstream_name not provided)")
    
    if activator_alerts_email:
        # Email token regex pattern - matches tokenized email format: __TOKEN_email_[counter]__
        email_token_pattern = r'__TOKEN_email_\d+__'
        
        # Update tokenized email addresses in rule definitions using regex
        emails_updated = 0
        found_email_tokens = set()
        
        for entity in activator_config:
            if entity.get('type') == 'timeSeriesView-v1':
                payload = entity.get('payload', {})
                definition = payload.get('definition', {})
                if definition.get('type') == 'Rule':
                    instance_str = definition.get('instance', '')
                    if instance_str:
                        try:
                            # Find all email tokens in the instance string using regex
                            found_tokens_in_instance = re.findall(email_token_pattern, instance_str)
                            found_email_tokens.update(found_tokens_in_instance)
                            
                            # Replace all found email tokens with the new email
                            updated_instance_str = instance_str
                            for email_token in found_tokens_in_instance:
                                updated_instance_str = updated_instance_str.replace(email_token, activator_alerts_email)
                                emails_updated += 1
                                print(f"   Updated email token '{email_token}' to '{activator_alerts_email}'")
                            
                            # Update the instance string
                            definition['instance'] = updated_instance_str
                            
                        except Exception as e:
                            print(f"   Warning: Could not process instance for email replacement: {e}")
        
        if emails_updated > 0:
            print(f"   Updated {emails_updated} email token(s) in activator rules")
            print(f"   Found and replaced email tokens: {', '.join(found_email_tokens)}")
        else:
            print(f"   No email tokens found to update")
    else:
        print(f"   Skipping email address updates (activator_alerts_email not provided)")
    
    return activator_config

def update_activator_definition(workspace_id: str,
                              activator_id: str,
                              activator_file_path: str,
                              eventstream_id: str = None,
                              eventstream_name: str = None,
                              activator_alerts_email: str = None):
    """
    Update the definition of an existing Activator (Reflex) in the specified workspace.
    
    Args:
        workspace_id: ID of the workspace where the activator exists (required)
        activator_id: ID of the existing activator to update (required)
        activator_file_path: Path to the JSON file containing the activator configuration (required)
        eventstream_id: ID of the eventhouse stream for the activator (optional)
        eventstream_name: Name for the event source (optional)
        activator_alerts_email: Email address to replace in alert configurations (optional)

    Returns:
        Dictionary with activator information if successful
        
    Raises:
        Exception: If activator update fails
    """
    try:
        # Validate required parameters
        if not workspace_id or not workspace_id.strip():
            raise ValueError("workspace_id is required and cannot be empty")
        
        if not activator_id or not activator_id.strip():
            raise ValueError("activator_id is required and cannot be empty")
        
        # Initialize the Fabric API client
        print("🚀 Initializing Fabric API client...")
        fabric_client = FabricWorkspaceApiClient(workspace_id=workspace_id)

        # Verify the activator exists
        print(f"🔍 Verifying activator exists (ID: {activator_id})...")
        existing_activator = fabric_client.get_activator_by_id(activator_id)
        if not existing_activator:
            print(f"❌ Activator with ID '{activator_id}' not found in workspace")
            raise ValueError(f"Activator with ID '{activator_id}' not found in workspace '{workspace_id}'")
        
        activator_name = existing_activator.get('displayName', 'Unknown')
        print(f"✅ Found activator: {activator_name}")

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

        # Update the existing activator
        print(f"🔄 Updating activator definition (ID: {activator_id})...")
        
        update_success = fabric_client.update_activator_definition(
            activator_id=activator_id,
            definition_base64=activator_base64
        )
        
        if update_success:
            print(f"✅ Successfully updated activator definition")
            
            # Get updated activator information
            updated_activator = fabric_client.get_activator_by_id(activator_id)
            return updated_activator
        else:
            print(f"❌ Failed to update activator definition")
            raise Exception(f"Failed to update activator definition")
        
    except (FabricApiError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"❌ Error in activator definition update: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute the activator definition update."""
    parser = argparse.ArgumentParser(
        description="Update the definition of an existing Activator (Reflex) in a Fabric workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with required parameters:
  python fabric_activator_definition.py --workspace-id "12345678-1234-1234-1234-123456789012" --activator-id "87654321-4321-4321-4321-210987654321" --activator-file "ReflexEntities.json"
  
  # With custom parameters to override JSON values:
  python fabric_activator_definition.py --workspace-id "12345678-1234-1234-1234-123456789012" --activator-id "87654321-4321-4321-4321-210987654321" --activator-file "ReflexEntities.json" --eventstream-id "11111111-1111-1111-1111-111111111111" --activator-alerts-email "alerts@contoso.com"
        """
    )
    
    parser.add_argument(
        "--workspace-id", 
        required=True, 
        help="ID of the workspace where the activator exists"
    )
    
    parser.add_argument(
        "--activator-id", 
        required=True, 
        help="ID of the existing activator to update"
    )
    
    parser.add_argument(
        "--activator-file", 
        required=True, 
        help="Path to the JSON file containing the activator configuration"
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
    
    print(f"📊 Activator Definition Update Script")
    print(f"  Workspace ID: {args.workspace_id}")
    print(f"  Activator ID: {args.activator_id}")
    print(f"  Activator File: {args.activator_file}")
    print(f"  Eventstream ID: {args.eventstream_id or '(not provided)'}")
    print(f"  Eventstream Name: {args.eventstream_name or '(preserve original)'}")
    print(f"  Activator Alerts Email: {args.activator_alerts_email or '(not provided)'}")
    print("=" * 60)
    
    # Execute the main logic
    try:
        result = update_activator_definition(
            workspace_id=args.workspace_id,
            activator_id=args.activator_id,
            activator_file_path=args.activator_file,
            eventstream_id=args.eventstream_id,
            eventstream_name=args.eventstream_name,
            activator_alerts_email=args.activator_alerts_email
        )
        
        print(f"\n🎉 Activator definition update completed successfully.")
        if result:
            print(f"Activator ID: {result.get('id')}")
            print(f"Activator Name: {result.get('displayName')}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()