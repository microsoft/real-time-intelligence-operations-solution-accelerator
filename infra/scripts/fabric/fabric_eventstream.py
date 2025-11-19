#!/usr/bin/env python3
"""
Fabric Eventstream Setup Script

This script creates or updates a Microsoft Fabric Eventstream in a specified workspace.
It loads eventstream configuration from a JSON file, encodes it to Base64, and creates or updates 
the eventstream using the Fabric API.

Usage:
    python fabric_eventstream.py --workspace-id "workspace-id" --eventstream-name "My Eventstream" --eventstream-file "eventstream.json"
    
    Optional parameters can be provided to customize the eventstream:
    python fabric_eventstream.py --workspace-id "workspace-id" --eventstream-name "My Eventstream" --eventstream-file "eventstream.json" --eventhouse-id "eventhouse-id" --database-name "db_name" --source-name "MySource"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Contributor permissions in the target workspace
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
                               destination_name: str = None,
                               stream_name: str = None) -> dict:
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
        destination_name: Name for the destination (optional, skips destination name updates if None)
        stream_name: Name for the stream (optional, skips stream updates if None)
        
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
        # Update destination name only if destination_name is provided
        if destination_name:
            original_dest_name = destination.get('name')
            destination['name'] = destination_name
            print(f"   Updated destination name from '{original_dest_name}' to '{destination_name}'")
        
        # Update Eventhouse-specific properties only if all required parameters are provided
        if destination.get('type') == 'Eventhouse' and eventhouse_database_id and eventhouse_database_name and workspace_id:
            destination['properties']['itemId'] = eventhouse_database_id
            destination['properties']['databaseName'] = eventhouse_database_name
            destination['properties']['workspaceId'] = workspace_id
            destination['properties']['tableName'] = eventhouse_table_name
            print(f"   Updated Eventhouse destination properties: itemId={eventhouse_database_id}, database={eventhouse_database_name}, table={eventhouse_table_name}")
        elif destination.get('type') == 'Eventhouse':
            print(f"   Skipping Eventhouse destination properties update (missing required parameters)")

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

def setup_eventstream(workspace_id: str,
                     eventstream_file_path: str,
                     eventstream_name: str = "rti_eventstream",
                     eventhouse_database_id: str = None,
                     eventhouse_database_name: str = None,
                     eventhub_connection_id: str = None,
                     eventhouse_table_name: str = "events",
                     source_name: str = None,
                     destination_name: str = None,
                     stream_name: str = None):
    """
    Create or update an Eventstream in the specified workspace.
    
    Args:
        workspace_id: ID of the workspace where the eventstream will be created (required)
        eventstream_file_path: Path to the JSON file containing the eventstream configuration (required)
        eventstream_name: Name for the eventstream (required, whitespaces will be removed)
        eventhouse_database_id: ID of the eventhouse database for the eventstream destination (optional)
        eventhouse_database_name: Name of the eventhouse database (optional)
        eventhub_connection_id: ID of the Event Hub connection for the eventstream source (optional)
        eventhouse_table_name: Name of the eventhouse table (defaults to "events")
        source_name: Name for the source (optional, skips source updates if None)
        destination_name: Name for the destination (optional, skips destination name updates if None)
        stream_name: Name for the stream (optional, skips stream updates if None)

    Returns:
        Dictionary with eventstream information if successful
        
    Raises:
        Exception: If eventstream creation/update fails
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
            destination_name=destination_name,
            stream_name=stream_name
        )

        # Encode eventstream configuration to Base64
        print("🔄 Encoding eventstream configuration to Base64...")
        eventstream_json_str = json.dumps(eventstream_config)
        eventstream_base64 = base64.b64encode(eventstream_json_str.encode('utf-8')).decode('utf-8')
        print(f"✅ Eventstream configuration encoded ({len(eventstream_base64)} characters)")

        # Check if eventstream already exists
        print("🔍 Checking for existing eventstream...")
        existing_eventstream = fabric_client.get_eventstream_by_name(eventstream_name)
        
        if existing_eventstream:
            # Update the existing eventstream
            print(f"🔄 Updating existing eventstream '{eventstream_name}' (ID: {existing_eventstream.get('id')})...")
            eventstream_id = existing_eventstream.get('id')
            
            update_success = fabric_client.update_eventstream_content(
                eventstream_id=eventstream_id,
                eventstream_definition_base64=eventstream_base64
            )
            
            if update_success:
                print(f"✅ Successfully updated eventstream '{eventstream_name}' (ID: {eventstream_id})")
                return existing_eventstream
            else:
                print(f"❌ Failed to update eventstream '{eventstream_name}'")
                raise Exception(f"Failed to update eventstream '{eventstream_name}'")
        else:
            # Create a new eventstream
            print(f"📊 Creating new eventstream '{eventstream_name}'...")
            eventstream_result = fabric_client.create_eventstream(
                display_name=eventstream_name,
                description=f"Eventstream: {eventstream_name}",
                eventstream_definition_base64=eventstream_base64
            )
            
            eventstream_id = eventstream_result.get('id')
            print(f"✅ Successfully created eventstream '{eventstream_name}' (ID: {eventstream_id})")
            
            return eventstream_result
        
    except (FabricApiError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"❌ Error in eventstream setup: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute the eventstream setup."""
    parser = argparse.ArgumentParser(
        description="Create or update an Eventstream in a Fabric workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with required parameters:
  python fabric_eventstream.py --workspace-id "12345678-1234-1234-1234-123456789012" --eventstream-name "MyEventstream" --eventstream-file "eventstream.json"
  
  # With custom parameters to override JSON values:
  python fabric_eventstream.py --workspace-id "12345678-1234-1234-1234-123456789012" --eventstream-name "MyEventstream" --eventstream-file "eventstream.json" --eventhouse-id "87654321-4321-4321-4321-210987654321" --database-name "manufacturing_db" --source-name "MySource"
  
  Note: Eventstream names cannot contain whitespaces and will be automatically removed.
        """
    )
    
    parser.add_argument(
        "--workspace-id", 
        required=True, 
        help="ID of the workspace where the eventstream will be created"
    )
    
    parser.add_argument(
        "--eventstream-file", 
        required=True, 
        help="Path to the JSON file containing the eventstream configuration"
    )
    
    parser.add_argument(
        "--eventstream-name",
        default="rti_eventstream",
        help="Name for the eventstream (whitespaces will be automatically removed)"
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
        "--destination-name", 
        help="Name for the destination (optional, preserves original if not provided)"
    )
    
    parser.add_argument(
        "--stream-name", 
        help="Name for the stream (optional, preserves original if not provided)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"📊 Eventstream Setup Script")
    print(f"  Workspace ID: {args.workspace_id}")
    print(f"  Eventstream File: {args.eventstream_file}")
    print(f"  Eventstream Name: {args.eventstream_name or '(not provided)'}")
    print(f"  Eventhouse Database ID: {args.eventhouse_database_id or '(not provided)'}")
    print(f"  Database Name: {args.database_name or '(not provided)'}")
    print(f"  EventHub Connection ID: {args.eventhub_connection_id or '(not provided)'}")
    print(f"  Table Name: {args.table_name}")
    print(f"  Source Name: {args.source_name or '(preserve original)'}")
    print(f"  Destination Name: {args.destination_name or '(preserve original)'}")
    print(f"  Stream Name: {args.stream_name or '(preserve original)'}")
    print("=" * 60)
    
    # Execute the main logic
    try:
        result = setup_eventstream(
            workspace_id=args.workspace_id,
            eventstream_file_path=args.eventstream_file,
            eventstream_name=args.eventstream_name,
            eventhouse_database_id=args.eventhouse_database_id,
            eventhouse_database_name=args.database_name,
            eventhub_connection_id=args.eventhub_connection_id,
            eventhouse_table_name=args.table_name,
            source_name=args.source_name,
            destination_name=args.destination_name,
            stream_name=args.stream_name
        )
        
        print(f"\n🎉 Eventstream setup completed successfully.")
        print(f"Eventstream ID: {result.get('id')}")
        print(f"Eventstream Name: {result.get('displayName')}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()