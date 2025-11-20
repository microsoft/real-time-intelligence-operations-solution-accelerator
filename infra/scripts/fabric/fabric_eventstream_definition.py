#!/usr/bin/env python3
"""
Fabric Eventstream Definition Update Script

This script updates the definition of an existing Microsoft Fabric Eventstream in a specified workspace.
It loads eventstream configuration from a JSON file, transforms it with dynamic values, encodes it to Base64, 
and updates the eventstream using the Fabric API.

Usage:
    python fabric_eventstream_definition.py --workspace-id "workspace-id" --eventstream-id "eventstream-id" --eventstream-file "eventstream.json"
    
    Optional parameters can be provided to customize the eventstream configuration:
    python fabric_eventstream_definition.py --workspace-id "workspace-id" --eventstream-id "eventstream-id" --eventstream-file "eventstream.json" --eventhouse-database-id "eventhouse-id" --database-name "db_name" --source-name "MySource"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Contributor permissions in the target workspace
    - Existing eventstream in the workspace
"""

import argparse
import json
import sys
import base64
import os
from fabric_api import FabricWorkspaceApiClient, FabricApiError

def transform_eventstream_config(eventstream_config: dict,
                               eventhouse_database_id: str = None,
                               eventhouse_database_name: str = None,
                               workspace_id: str = None,
                               eventhouse_table_name: str = "events",
                               eventhub_connection_id: str = None,
                               source_name: str = None,
                               eventhouse_name: str = None,
                               stream_name: str = None,
                               activator_name: str = None,
                               activator_id: str = None) -> dict:
    """
    Transform eventstream configuration with dynamic values.
    
    Args:
        eventstream_config: The original eventstream configuration dictionary
        eventhouse_database_id: ID of the eventhouse database for the eventstream destination (optional)
        eventhouse_database_name: Name of the eventhouse database (optional)
        workspace_id: ID of the workspace (optional)
        eventhouse_table_name: Name of the eventhouse table (defaults to "events")
        eventhub_connection_id: ID of the Event Hub connection for the eventstream source (optional)
        source_name: Name for the source (optional, skips source updates if None)
        eventhouse_name: Name for the eventhouse destination (optional, only applied to Eventhouse destinations)
        stream_name: Name for the stream (optional, skips stream updates if None)
        activator_name: Name for the activator destination (optional, only applied to Activator destinations)
        activator_id: ID of the activator for the eventstream destination (optional)
        
    Returns:
        Transformed eventstream configuration dictionary
    """
    print(f"📝 Updating eventstream configuration with dynamic values...")
    
    # Update sources with configured names only if source_name is provided
    if source_name:
        for source in eventstream_config.get('sources', []):
            original_name = source.get('name')
            source['name'] = source_name
            print(f"   Updated source name from '{original_name}' to '{source_name}'")
    else:
        print(f"   Skipping source name updates (source_name not provided)")

    # Update Event Hub source dataConnectionId if provided
    if eventhub_connection_id:
        for source in eventstream_config.get('sources', []):
            if source.get('type') == 'AzureEventHub':
                original_connection_id = source.get('properties', {}).get('dataConnectionId')
                source.setdefault('properties', {})['dataConnectionId'] = eventhub_connection_id
                print(f"   Updated Event Hub source dataConnectionId from '{original_connection_id}' to '{eventhub_connection_id}'")
    else:
        print(f"   Skipping Event Hub dataConnectionId updates (eventhub_connection_id not provided)")

    # Update destinations with eventhouse information and configured names
    for destination in eventstream_config.get('destinations', []):
        destination_type = destination.get('type')
        
        # Update Eventhouse-specific properties and name
        if destination_type == 'Eventhouse':
            # Update Eventhouse name if provided
            if eventhouse_name:
                original_dest_name = destination.get('name')
                destination['name'] = eventhouse_name
                print(f"   Updated Eventhouse destination name from '{original_dest_name}' to '{eventhouse_name}'")
            
            # Update Eventhouse properties if all required parameters are provided
            if eventhouse_database_id and eventhouse_database_name and workspace_id:
                destination['properties']['itemId'] = eventhouse_database_id
                destination['properties']['databaseName'] = eventhouse_database_name
                destination['properties']['workspaceId'] = workspace_id
                destination['properties']['tableName'] = eventhouse_table_name
                print(f"   Updated Eventhouse destination properties: itemId={eventhouse_database_id}, database={eventhouse_database_name}, table={eventhouse_table_name}")
            else:
                print(f"   Skipping Eventhouse destination properties update (missing required parameters)")
        
        # Update Activator-specific properties and name
        elif destination_type == 'Activator':
            # Update Activator name if provided
            if activator_name:
                original_activator_name = destination.get('name')
                destination['name'] = activator_name
                print(f"   Updated Activator destination name from '{original_activator_name}' to '{activator_name}'")
            
            # Update Activator properties if all required parameters are provided
            if workspace_id and activator_id:
                destination['properties']['workspaceId'] = workspace_id
                destination['properties']['itemId'] = activator_id
                print(f"   Updated Activator destination properties: itemId={activator_id}, workspaceId={workspace_id}")
            else:
                print(f"   Skipping Activator destination properties update (missing required parameters)")

    # Update stream names with configured name only if stream_name is provided
    if stream_name:
        for stream in eventstream_config.get('streams', []):
            original_stream_name = stream.get('name')
            stream['name'] = stream_name
            print(f"   Updated stream name from '{original_stream_name}' to '{stream_name}'")
        
        # Update input node references in destinations to match updated stream names
        for destination in eventstream_config.get('destinations', []):
            if 'inputNodes' in destination:
                for input_node in destination['inputNodes']:
                    if 'name' in input_node:
                        original_name = input_node['name']
                        input_node['name'] = stream_name
                        print(f"   Updated destination input node from '{original_name}' to '{stream_name}'")
            
            if 'inputSchemas' in destination:
                for input_schema in destination['inputSchemas']:
                    if 'name' in input_schema:
                        original_name = input_schema['name']
                        input_schema['name'] = stream_name
                        print(f"   Updated destination input schema from '{original_name}' to '{stream_name}'")
    else:
        print(f"   Skipping stream name updates (stream_name not provided)")

    # Update input node references in streams to match updated source names only if source_name is provided
    if source_name:
        for stream in eventstream_config.get('streams', []):
            if 'inputNodes' in stream:
                for input_node in stream['inputNodes']:
                    if 'name' in input_node:
                        original_name = input_node['name']
                        input_node['name'] = source_name
                        print(f"   Updated stream input node from '{original_name}' to '{source_name}'")
    
    return eventstream_config

def update_eventstream_definition(workspace_id: str,
                                eventstream_id: str,
                                eventstream_file_path: str,
                                eventhouse_database_id: str = None,
                                eventhouse_database_name: str = None,
                                eventhub_connection_id: str = None,
                                eventhouse_table_name: str = "events",
                                source_name: str = None,
                                eventhouse_name: str = None,
                                stream_name: str = None,
                                activator_name: str = None,
                                activator_id: str = None):
    """
    Update the definition of an existing Eventstream in the specified workspace.
    
    Args:
        workspace_id: ID of the workspace where the eventstream exists (required)
        eventstream_id: ID of the existing eventstream to update (required)
        eventstream_file_path: Path to the JSON file containing the eventstream configuration (required)
        eventhouse_database_id: ID of the eventhouse database for the eventstream destination (optional)
        eventhouse_database_name: Name of the eventhouse database (optional)
        eventhub_connection_id: ID of the Event Hub connection for the eventstream source (optional)
        eventhouse_table_name: Name of the eventhouse table (defaults to "events")
        source_name: Name for the source (optional, skips source updates if None)
        eventhouse_name: Name for the eventhouse destination (optional, only applied to Eventhouse destinations)
        stream_name: Name for the stream (optional, skips stream updates if None)
        activator_name: Name for the activator destination (optional, only applied to Activator destinations)
        activator_id: ID of the activator for the eventstream destination (optional)

    Returns:
        Dictionary with eventstream information if successful
        
    Raises:
        Exception: If eventstream update fails
    """
    try:
        # Validate required parameters
        if not workspace_id or not workspace_id.strip():
            raise ValueError("workspace_id is required and cannot be empty")
        
        if not eventstream_id or not eventstream_id.strip():
            raise ValueError("eventstream_id is required and cannot be empty")
        
        # Initialize the Fabric API client
        print("🚀 Initializing Fabric API client...")
        fabric_client = FabricWorkspaceApiClient(workspace_id=workspace_id)

        # Verify the eventstream exists
        print(f"🔍 Verifying eventstream exists (ID: {eventstream_id})...")
        existing_eventstream = fabric_client.get_eventstream_by_id(eventstream_id)
        if not existing_eventstream:
            print(f"❌ Eventstream with ID '{eventstream_id}' not found in workspace")
            raise ValueError(f"Eventstream with ID '{eventstream_id}' not found in workspace '{workspace_id}'")
        
        eventstream_name = existing_eventstream.get('displayName', 'Unknown')
        print(f"✅ Found eventstream: {eventstream_name}")

        # Verify the eventstream file exists
        if not os.path.exists(eventstream_file_path):
            print(f"❌ Eventstream file not found: {eventstream_file_path}")
            raise FileNotFoundError(f"Eventstream file not found: {eventstream_file_path}")

        # Load JSON configuration
        print(f"📄 Loading eventstream configuration from: {eventstream_file_path}")
        with open(eventstream_file_path, "r", encoding="utf-8") as json_file:
            eventstream_config = json.load(json_file)

        # Transform the eventstream configuration with dynamic values
        eventstream_config = transform_eventstream_config(
            eventstream_config=eventstream_config,
            eventhouse_database_id=eventhouse_database_id,
            eventhouse_database_name=eventhouse_database_name,
            workspace_id=workspace_id,
            eventhouse_table_name=eventhouse_table_name,
            eventhub_connection_id=eventhub_connection_id,
            source_name=source_name,
            eventhouse_name=eventhouse_name,
            stream_name=stream_name,
            activator_name=activator_name,
            activator_id=activator_id
        )

        # Encode eventstream configuration to Base64
        print("🔄 Encoding eventstream configuration to Base64...")
        eventstream_json_str = json.dumps(eventstream_config)
        eventstream_base64 = base64.b64encode(eventstream_json_str.encode('utf-8')).decode('utf-8')
        print(f"✅ Eventstream configuration encoded ({len(eventstream_base64)} characters)")

        # Update the existing eventstream
        print(f"🔄 Updating eventstream definition (ID: {eventstream_id})...")
        
        update_success = fabric_client.update_eventstream_content(
            eventstream_id=eventstream_id,
            eventstream_definition_base64=eventstream_base64
        )
        
        if update_success:
            print(f"✅ Successfully updated eventstream definition (ID: {eventstream_id})")
            
            # Get updated eventstream information
            updated_eventstream = fabric_client.get_eventstream_by_id(eventstream_id)
            return updated_eventstream
        else:
            print(f"❌ Failed to update eventstream definition")
            raise Exception(f"Failed to update eventstream definition")
        
    except (FabricApiError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"❌ Error in eventstream definition update: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute the eventstream definition update."""
    parser = argparse.ArgumentParser(
        description="Update the definition of an existing Eventstream in a Fabric workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with required parameters:
  python fabric_eventstream_definition.py --workspace-id "12345678-1234-1234-1234-123456789012" --eventstream-id "87654321-4321-4321-4321-210987654321" --eventstream-file "eventstream.json"
  
  # With custom parameters to override JSON values:
  python fabric_eventstream_definition.py --workspace-id "12345678-1234-1234-1234-123456789012" --eventstream-id "87654321-4321-4321-4321-210987654321" --eventstream-file "eventstream.json" --eventhouse-database-id "11111111-1111-1111-1111-111111111111" --database-name "manufacturing_db" --source-name "MySource"
        """
    )
    
    parser.add_argument(
        "--workspace-id", 
        required=True, 
        help="ID of the workspace where the eventstream exists"
    )
    
    parser.add_argument(
        "--eventstream-id", 
        required=True, 
        help="ID of the existing eventstream to update"
    )
    
    parser.add_argument(
        "--eventstream-file", 
        required=True, 
        help="Path to the JSON file containing the eventstream configuration"
    )
    
    parser.add_argument(
        "--eventhouse-database-id", 
        help="ID of the eventhouse database for the eventstream destination (optional)"
    )
    
    parser.add_argument(
        "--database-name", 
        help="Name of the eventhouse database (optional)"
    )
    
    parser.add_argument(
        "--eventhub-connection-id", 
        help="ID of the Event Hub connection for the eventstream source (optional)"
    )
    
    parser.add_argument(
        "--table-name", 
        default="events",
        help="Name of the eventhouse table (defaults to 'events')"
    )
    
    parser.add_argument(
        "--source-name", 
        help="Name for the source (optional, preserves original if not provided)"
    )
    
    parser.add_argument(
        "--eventhouse-name", 
        help="Name for the eventhouse destination (optional, only applied to Eventhouse destinations)"
    )
    
    parser.add_argument(
        "--stream-name", 
        help="Name for the stream (optional, preserves original if not provided)"
    )
    
    parser.add_argument(
        "--activator-name", 
        help="Name for the activator destination (optional)"
    )
    
    parser.add_argument(
        "--activator-id", 
        help="ID of the activator for the eventstream destination (optional)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"📊 Eventstream Definition Update Script")
    print(f"  Workspace ID: {args.workspace_id}")
    print(f"  Eventstream ID: {args.eventstream_id}")
    print(f"  Eventstream File: {args.eventstream_file}")
    print(f"  Eventhouse Database ID: {args.eventhouse_database_id or '(not provided)'}")
    print(f"  Database Name: {args.database_name or '(not provided)'}")
    print(f"  EventHub Connection ID: {args.eventhub_connection_id or '(not provided)'}")
    print(f"  Table Name: {args.table_name}")
    print(f"  Source Name: {args.source_name or '(preserve original)'}")
    print(f"  Eventhouse Name: {args.eventhouse_name or '(not provided)'}")
    print(f"  Stream Name: {args.stream_name or '(preserve original)'}")
    print(f"  Activator Name: {args.activator_name or '(not provided)'}")
    print(f"  Activator ID: {args.activator_id or '(not provided)'}")
    print("=" * 60)
    
    # Execute the main logic
    try:
        result = update_eventstream_definition(
            workspace_id=args.workspace_id,
            eventstream_id=args.eventstream_id,
            eventstream_file_path=args.eventstream_file,
            eventhouse_database_id=args.eventhouse_database_id,
            eventhouse_database_name=args.database_name,
            eventhub_connection_id=args.eventhub_connection_id,
            eventhouse_table_name=args.table_name,
            source_name=args.source_name,
            eventhouse_name=args.eventhouse_name,
            stream_name=args.stream_name,
            activator_name=args.activator_name,
            activator_id=args.activator_id
        )
        
        print(f"\n🎉 Eventstream definition update completed successfully.")
        if result:
            print(f"Eventstream ID: {result.get('id')}")
            print(f"Eventstream Name: {result.get('displayName')}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()