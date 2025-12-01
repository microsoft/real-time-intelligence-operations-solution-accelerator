#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Fabric Event Hub Connection Setup Module

This module provides Event Hub connection setup functionality for Microsoft Fabric operations.
It can automatically retrieve Event Hub access keys using Azure credentials,
or use provided keys to set up connections.

Features:
- Automatically retrieve Event Hub access keys using DefaultAzureCredential
- Create or update Event Hub connections in Microsoft Fabric
- Support for both hub-level and namespace-level key retrieval

Usage:
    python fabric_eventhub.py --connection-name "MyConnection" --namespace-name "namespace" --event-hub-name "hub"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Contributor permissions in the target workspace
    - Event Hub Contributor role for automatic key retrieval
    - azure-mgmt-eventhub package: pip install azure-mgmt-eventhub

Environment Setup:
    pip install azure-mgmt-eventhub azure-identity
"""

import argparse
import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.eventhub import EventHubManagementClient
from fabric_api import FabricApiClient, FabricWorkspaceApiClient, FabricApiError


def get_event_hub_primary_key(namespace_name: str, hub_name: str, subscription_id: str, resource_group_name: str, authorization_rule_name: str = "RootManageSharedAccessKey") -> dict:
    """
    Get the primary access key from an Azure Event Hub using DefaultAzureCredential.
    
    Args:
        namespace_name: Name of the Event Hub namespace
        hub_name: Name of the Event Hub
        subscription_id: Azure subscription ID
        resource_group_name: Name of the resource group containing the Event Hub
        authorization_rule_name: Name of the authorization rule (default: RootManageSharedAccessKey)
        
    Returns:
        Dictionary containing access keys and connection string:
        {
            'primary_key': str,
            'secondary_key': str,
            'primary_connection_string': str,
            'secondary_connection_string': str,
            'key_name': str
        }
        
    Raises:
        Exception: If unable to retrieve access keys
    """
    try:
        print(f"🔑 Retrieving access keys for Event Hub: {hub_name} in namespace: {namespace_name}")
        
        # Initialize Azure credential
        credential = DefaultAzureCredential()
        
        # Create Event Hub management client
        eventhub_client = EventHubManagementClient(credential, subscription_id)
        
        # Get the authorization rule keys
        keys = eventhub_client.event_hubs.list_keys(
            resource_group_name=resource_group_name,
            namespace_name=namespace_name,
            event_hub_name=hub_name,
            authorization_rule_name=authorization_rule_name
        )
        
        result = {
            'primary_key': keys.primary_key,
            'secondary_key': keys.secondary_key,
            'primary_connection_string': keys.primary_connection_string,
            'secondary_connection_string': keys.secondary_connection_string,
            'key_name': authorization_rule_name
        }
        
        print(f"✅ Successfully retrieved access keys for Event Hub: {hub_name}")
        return result
        
    except Exception as e:
        print(f"❌ Failed to retrieve Event Hub access keys: {e}")
        raise


def get_event_hub_namespace_primary_key(namespace_name: str, subscription_id: str, resource_group_name: str, authorization_rule_name: str = "RootManageSharedAccessKey") -> dict:
    """
    Get the primary access key from an Event Hub namespace (for all Event Hubs in the namespace).
    
    Args:
        namespace_name: Name of the Event Hub namespace
        subscription_id: Azure subscription ID
        resource_group_name: Name of the resource group containing the Event Hub namespace
        authorization_rule_name: Name of the authorization rule (default: RootManageSharedAccessKey)
        
    Returns:
        Dictionary containing access keys and connection string:
        {
            'primary_key': str,
            'secondary_key': str,
            'primary_connection_string': str,
            'secondary_connection_string': str,
            'key_name': str
        }
        
    Raises:
        Exception: If unable to retrieve access keys
    """
    try:
        print(f"🔑 Retrieving namespace access keys for: {namespace_name}")
        
        # Initialize Azure credential
        credential = DefaultAzureCredential()
        
        # Create Event Hub management client
        eventhub_client = EventHubManagementClient(credential, subscription_id)
        
        # Get the namespace authorization rule keys
        keys = eventhub_client.namespaces.list_keys(
            resource_group_name=resource_group_name,
            namespace_name=namespace_name,
            authorization_rule_name=authorization_rule_name
        )
        
        result = {
            'primary_key': keys.primary_key,
            'secondary_key': keys.secondary_key,
            'primary_connection_string': keys.primary_connection_string,
            'secondary_connection_string': keys.secondary_connection_string,
            'key_name': authorization_rule_name
        }
        
        print(f"✅ Successfully retrieved namespace access keys for: {namespace_name}")
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def setup_eventhub_connection(
    fabric_client: FabricApiClient,
    connection_name: str,
    namespace_name: str,
    event_hub_name: str,
    subscription_id: str,
    resource_group_name: str,
    authorization_rule_name: str
):
    """
    Create or update an Event Hub connection in Microsoft Fabric.
    
    This function automatically retrieves Event Hub access keys using Azure credentials
    and creates or updates the connection in Microsoft Fabric.
    
    If a connection with the same name already exists, it will be updated
    with the new parameters. Otherwise, a new connection will be created.
    
    Args:
        fabric_client: Authenticated FabricApiClient instance
        connection_name: Display name for the connection
        namespace_name: Event Hub namespace name
        event_hub_name: Event Hub name
        subscription_id: Azure subscription ID
        resource_group_name: Resource group name
        authorization_rule_name: Name of the authorization rule (default: RootManageSharedAccessKey)
        
    Returns:
        Dictionary with connection information if successful
        
    Raises:
        Exception: If connection creation/update fails
    """
    try:
        # Retrieve access key automatically
        print(f"🔑 Retrieving access key for Event Hub: {event_hub_name}")
        key_info = get_event_hub_namespace_primary_key(
            namespace_name=namespace_name,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            authorization_rule_name=authorization_rule_name
        )
        access_key = key_info['primary_key']
        print(f"✅ Successfully retrieved access key")
        
        # Use the passed fabric_client instead of creating a new one
        client = fabric_client

        connections = client.list_connections()

        # Check if connection already exists
        existing_connection = next(
            (conn for conn in connections 
             if isinstance(conn.get('displayName'), str) and conn['displayName'].lower() == connection_name.lower()), 
            None
        )
        
        if existing_connection:
            print(f"🔄 Connection '{connection_name}' already exists with ID: {existing_connection.get('id')}")
            print(f"Updating existing connection with new parameters...")
            
            # Update the existing connection
            result = client.update_eventhub_connection(
                connection_id=existing_connection.get('id'),
                name=connection_name, 
                namespace_name=namespace_name, 
                event_hub_name=event_hub_name, 
                shared_access_policy_name=authorization_rule_name, 
                shared_access_key=access_key
            )
            
            print(f"✅ Successfully updated Event Hub connection '{connection_name}' (ID: {result.get('id')})")
            return result
        
        # Create new connection
        result = client.create_eventhub_connection(
            name=connection_name, 
            namespace_name=namespace_name, 
            event_hub_name=event_hub_name, 
            shared_access_policy_name=authorization_rule_name, 
            shared_access_key=access_key
        )
        
        print(f"✅ Successfully created Event Hub connection '{connection_name}' (ID: {result.get('id')})")
        return result
        
    except FabricApiError as e:
        print(f"❌ Fabric API error: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error occurred: {e}")
        raise


def main():
    """Main function to handle command line arguments and execute Event Hub connection setup."""
    parser = argparse.ArgumentParser(
        description="Setup Event Hub connection in Microsoft Fabric",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_eventhub.py --connection-name "MyConnection" --namespace-name "mynamespace" --event-hub-name "myhub" --subscription-id "sub-id" --resource-group "rg-name"
        """
    )
    
    parser.add_argument(
        "--connection-name", 
        required=True,
        help="Name for the Event Hub connection"
    )
    
    parser.add_argument(
        "--namespace-name", 
        required=True,
        help="Event Hub namespace name"
    )
    
    parser.add_argument(
        "--event-hub-name", 
        required=True,
        help="Event Hub name"
    )
    
    parser.add_argument(
        "--subscription-id", 
        required=True,
        help="Azure subscription ID"
    )
    
    parser.add_argument(
        "--resource-group", 
        required=True,
        help="Resource group name"
    )
    
    parser.add_argument(
        "--authorization-rule",
        default="RootManageSharedAccessKey",
        help="Authorization rule name (default: RootManageSharedAccessKey)"
    )
    
    args = parser.parse_args()
    
    # Execute the main logic
    fabric_client = FabricApiClient()
    
    result = setup_eventhub_connection(
        fabric_client=fabric_client,
        connection_name=args.connection_name,
        namespace_name=args.namespace_name,
        event_hub_name=args.event_hub_name,
        subscription_id=args.subscription_id,
        resource_group_name=args.resource_group,
        authorization_rule_name=args.authorization_rule
    )
    
    print(f"\n✅ Connection ID: {result.get('id')}")
    print(f"✅ Connection Name: {result.get('displayName')}")


if __name__ == "__main__":
    main()
