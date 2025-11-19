#!/usr/bin/env python3
"""
Fabric Event Hub Connection Setup Script

This script creates or retrieves an Event Hub connection in Microsoft Fabric.
It can automatically retrieve Event Hub access keys using Azure credentials,
or use provided keys to set up connections.

Features:
- Automatically retrieve Event Hub access keys using DefaultAzureCredential
- Create or update Event Hub connections in Microsoft Fabric
- Support for both hub-level and namespace-level key retrieval

Usage:
    python fabric_event_hub.py

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Contributor permissions in the target workspace
    - Event Hub Contributor role for automatic key retrieval
    - azure-mgmt-eventhub package: pip install azure-mgmt-eventhub

Environment Setup:
    pip install azure-mgmt-eventhub azure-identity
"""

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
        print(f"❌ Failed to retrieve Event Hub namespace access keys: {e}")
        raise


def setup_eventhub_connection(
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
        
        client = FabricApiClient()

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


if __name__ == "__main__":
    # Configuration - update these values for your environment
    CONNECTION_NAME = "MyEventHubConnection"
    EVENT_HUB_NAMESPACE = "<your-namespace>"
    EVENT_HUB_NAME = "<your-event-hub-name>"
    SUBSCRIPTION_ID = "<your-subscription-id>"
    RESOURCE_GROUP_NAME = "<your-resource-group>"
    AUTHORIZATION_RULE_NAME = "<your-authorization-rule-name>" # RootManageSharedAccessKey
    
    try:
        print("Setting up Event Hub connection in Microsoft Fabric...")
        print("="*60)
        
        # Example: Setup connection with automatic key retrieval
        print("Setting up Event Hub connection with automatic key retrieval...")
        result = setup_eventhub_connection(
            connection_name=CONNECTION_NAME,
            namespace_name=EVENT_HUB_NAMESPACE,
            event_hub_name=EVENT_HUB_NAME,
            subscription_id=SUBSCRIPTION_ID,
            resource_group_name=RESOURCE_GROUP_NAME,
            authorization_rule_name=AUTHORIZATION_RULE_NAME
        )
        
        # Example: Just get the keys without setting up Fabric connection
        print("\nAdditionally, showing key retrieval...")
        keys = get_event_hub_namespace_primary_key(
            namespace_name=EVENT_HUB_NAMESPACE,
            subscription_id=SUBSCRIPTION_ID,
            resource_group_name=RESOURCE_GROUP_NAME
        )
        
        print(f"\n✅ Event Hub connection setup complete.")
        print(f"Connection ID: {result.get('id')}")
        print(f"Connection Name: {result.get('displayName')}")
        print(f"Primary Key: {keys['primary_key'][:10]}...")  # Show only first 10 chars for security
        print(f"Key Name: {keys['key_name']}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
