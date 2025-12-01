#!/usr/bin/env python3
"""
Fabric Connection Deletion Module

This module provides connection deletion functionality for Microsoft Fabric operations.

Usage:
    python fabric_connection_delete.py --connection-name "MyConnection"
    python fabric_connection_delete.py --connection-id "12345678-1234-1234-1234-123456789012"

Requirements:
    - fabric_api.py module in the same directory
    - Azure CLI authentication or other Azure credentials configured
    - Appropriate permissions to delete connections
"""

import argparse
import sys
from fabric_api import FabricApiClient, FabricApiError

def delete_connection(fabric_client: FabricApiClient, connection_name: str):
    """
    Delete Event Hub connection by name.
    
    Args:
        fabric_client: Authenticated FabricApiClient instance
        connection_name: Name of the connection to delete
        
    Returns:
        Connection ID if deletion successful, None if connection not found
        
    Raises:
        FabricApiError: If deletion fails due to unexpected error
    """
    try:
        print(f"Looking up connection: '{connection_name}'")
        connections = fabric_client.list_connections()
        
        # Find connection by display name
        connection = None
        for conn in connections:
            if conn.get('displayName', '').lower() == connection_name.lower():
                connection = conn
                break
        
        if not connection:
            print(f"Connection '{connection_name}' not found")
            return None
        
        connection_id = connection.get('id')
        print(f"Found connection: '{connection_name}' (ID: {connection_id})")
        
        # Delete the connection
        deleted_connection_id = fabric_client.delete_connection(connection_id)
        if deleted_connection_id:
            print(f"✅ Successfully completed: delete_connection (deleted: {deleted_connection_id})")
            return deleted_connection_id
        else:
            print(f"Connection {connection_id} was not found during deletion")
            return None
        
    except FabricApiError as e:
        print(f"❌ FabricApiError ({e.status_code}): {e}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

def delete_connection_by_id(fabric_client: FabricApiClient, connection_id: str):
    """
    Delete connection by ID directly.
    
    Args:
        fabric_client: Authenticated FabricApiClient instance
        connection_id: ID of the connection to delete
        
    Returns:
        Connection ID if deletion successful, None if connection not found
        
    Raises:
        FabricApiError: If deletion fails due to unexpected error
    """
    try:
        print(f"Deleting connection with ID: {connection_id}")
        
        # Delete the connection
        deleted_connection_id = fabric_client.delete_connection(connection_id)
        if deleted_connection_id:
            print(f"✅ Successfully completed: delete_connection_by_id (deleted: {deleted_connection_id})")
            return deleted_connection_id
        else:
            print(f"Connection {connection_id} was not found during deletion")
            return None
        
    except FabricApiError as e:
        print(f"❌ Exception while executing delete_connection_by_id: {e}")
        raise
    except Exception as e:
        print(f"❌ Exception while executing delete_connection_by_id: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute connection deletion."""
    parser = argparse.ArgumentParser(
        description="Delete a Fabric connection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_connection_delete.py --connection-name "EventHubConnection"
  python fabric_connection_delete.py --connection-id "12345678-1234-1234-1234-123456789012"
        """
    )
    
    parser.add_argument(
        "--connection-name",
        help="Name of the connection to delete"
    )
    
    parser.add_argument(
        "--connection-id",
        help="ID of the connection to delete"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate arguments
    if not args.connection_name and not args.connection_id:
        print("❌ Error: Must specify either --connection-name or --connection-id")
        sys.exit(1)
    
    if args.connection_name and args.connection_id:
        print("❌ Error: Cannot specify both --connection-name and --connection-id")
        sys.exit(1)
    
    # Execute the main logic
    fabric_client = FabricApiClient()
    
    # Delete connection
    if args.connection_name:
        result = delete_connection(fabric_client, args.connection_name)
    else:
        result = delete_connection_by_id(fabric_client, args.connection_id)
    
    print(f"\n✅ Deleted connection ID: {result if result else 'Failed'}")


if __name__ == "__main__":
    main()