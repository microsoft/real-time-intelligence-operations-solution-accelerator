#!/usr/bin/env python3
"""
Fabric Real-Time Dashboard Setup Script

This script creates or updates a Microsoft Fabric KQL (Real-Time) dashboard in a specified workspace.
It loads dashboard configuration from a JSON file, encodes it to Base64, and creates the dashboard
using the Fabric API.

Usage:
    python fabric_real_time_dashboard.py --workspace-id "workspace-id" --dashboard-title "Dashboard Title" --dashboard-file "dashboard.json" --cluster-uri "cluster-uri" --eventhouse-database-id "database-id"

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

def setup_real_time_dashboard(workspace_id: str,
                              dashboard_title: str,
                              rti_dashboard_file_path: str,
                              cluster_uri: str,
                              eventhouse_database_id: str):
    """
    Create or update a Real-Time Dashboard (KQL Dashboard) in the specified workspace.
    
    Args:
        workspace_id: ID of the workspace where the dashboard will be created
        dashboard_title: Title/name for the dashboard
        rti_dashboard_file_path: Path to the JSON file containing the dashboard configuration
        cluster_uri: URI of the KQL cluster for the dashboard data sources
        eventhouse_database_id: ID of the eventhouse database for the dashboard data sources

    Returns:
        Dictionary with dashboard information if successful
        
    Raises:
        Exception: If dashboard creation/update fails
    """
    try:
        # Initialize the Fabric API client
        print("🚀 Initializing Fabric API client...")
        fabric_client = FabricWorkspaceApiClient(workspace_id=workspace_id)

        # Verify the dashboard file exists
        if not os.path.exists(rti_dashboard_file_path):
            print(f"❌ Dashboard file not found: {rti_dashboard_file_path}")
            raise FileNotFoundError(f"Dashboard file not found: {rti_dashboard_file_path}")

        # Load JSON configuration
        print(f"📄 Loading dashboard configuration from: {rti_dashboard_file_path}")
        with open(rti_dashboard_file_path, "r", encoding="utf-8") as json_file:
            dashboard_config = json.load(json_file)

        # Update the dashboard title in the configuration
        dashboard_config["title"] = dashboard_title
        print(f"📝 Updated dashboard title to: {dashboard_title}")

        # Update dataSources in the configuration
        dashboard_config['dataSources'][0]["clusterUri"] = cluster_uri
        dashboard_config['dataSources'][0]["database"] = eventhouse_database_id
        dashboard_config['dataSources'][0]["workspace"] = workspace_id

        # Encode dashboard configuration to Base64
        print("🔄 Encoding dashboard configuration to Base64...")
        dashboard_base64 = base64.b64encode(json.dumps(dashboard_config).encode('utf-8')).decode('utf-8')
        print(f"✅ Dashboard configuration encoded ({len(dashboard_base64)} characters)")

        # List all available dashboards to check if one with this title already exists
        print("🔍 Checking for existing dashboards...")
        existing_dashboard = fabric_client.get_kql_dashboard_by_name(dashboard_title)
        
        if existing_dashboard:
            # Update the existing dashboard
            print(f"🔄 Updating existing dashboard '{dashboard_title}' (ID: {existing_dashboard.get('id')})...")
            dashboard_id = existing_dashboard.get('id')
            
            update_success = fabric_client.update_kql_dashboard_content(
                dashboard_id=dashboard_id,
                dashboard_definition_base64=dashboard_base64
            )
            
            if update_success:
                print(f"✅ Successfully updated dashboard '{dashboard_title}' (ID: {dashboard_id})")
                return existing_dashboard
            else:
                print(f"❌ Failed to update dashboard '{dashboard_title}'")
                raise Exception(f"Failed to update dashboard '{dashboard_title}'")
        else:
            # Create a new dashboard
            print(f"📊 Creating new dashboard '{dashboard_title}'...")
            dashboard_result = fabric_client.create_kql_dashboard(
                display_name=dashboard_title,
                description=f"Real-Time Intelligence Dashboard: {dashboard_title}",
                dashboard_definition_base64=dashboard_base64
            )
            
            dashboard_id = dashboard_result.get('id')
            print(f"✅ Successfully created dashboard '{dashboard_title}' (ID: {dashboard_id})")
            
            return dashboard_result
        
    except (FabricApiError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"❌ Error in dashboard setup: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

def main():
    """Main function to handle command line arguments and execute the dashboard setup."""
    parser = argparse.ArgumentParser(
        description="Create or update a Real-Time Dashboard in a Fabric workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_real_time_dashboard.py --workspace-id "12345678-1234-1234-1234-123456789012" --dashboard-title "Manufacturing RTI Dashboard" --dashboard-file "rti-dashboard.json" --cluster-uri "https://cluster.kusto.windows.net" --eventhouse-database-id "d032514a-dc48-4347-b476-ce71f9aa7597"
        """
    )
    
    parser.add_argument(
        "--workspace-id", 
        required=True, 
        help="ID of the workspace where the dashboard will be created"
    )
    
    parser.add_argument(
        "--dashboard-title", 
        required=True, 
        help="Title/name for the dashboard"
    )
    
    parser.add_argument(
        "--dashboard-file", 
        required=True, 
        help="Path to the JSON file containing the dashboard configuration"
    )
    
    parser.add_argument(
        "--cluster-uri", 
        required=True, 
        help="URI of the KQL cluster for the dashboard data sources"
    )
    
    parser.add_argument(
        "--eventhouse-database-id", 
        required=True, 
        help="ID of the eventhouse database for the dashboard data sources"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"📊 Real-Time Dashboard Setup Script")
    print(f"  Workspace ID: {args.workspace_id}")
    print(f"  Dashboard Title: {args.dashboard_title}")
    print(f"  Dashboard File: {args.dashboard_file}")
    print(f"  Cluster URI: {args.cluster_uri}")
    print(f"  Database ID: {args.eventhouse_database_id}")
    print("=" * 60)
    
    # Execute the main logic
    try:
        result = setup_real_time_dashboard(
            workspace_id=args.workspace_id,
            dashboard_title=args.dashboard_title,
            rti_dashboard_file_path=args.dashboard_file,
            cluster_uri=args.cluster_uri,
            eventhouse_database_id=args.eventhouse_database_id
        )
        
        print(f"\n🎉 Real-Time Dashboard setup completed successfully.")
        print(f"Dashboard ID: {result.get('id')}")
        print(f"Dashboard Name: {result.get('displayName')}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
