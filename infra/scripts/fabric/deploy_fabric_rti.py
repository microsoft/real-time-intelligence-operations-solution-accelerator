#!/usr/bin/env python3
"""
Data pipeline initialization orchestrator script.

This script coordinates the execution of all data pipeline initialization functions
in the correct order, with proper error handling and logging. It uses environment
variables for configuration and calls each function directly.

Functions executed in order:
1. setup_workspace - Create and configure Fabric workspace
2. setup_eventhouse - Set up Eventhouse in the workspace  
3. setup_fabric_database - Set up database tables and schema
4. load_data_to_fabric - Load sample data into Fabric
5. setup_eventhub_connection - Configure Event Hub connection
6. setup_real_time_dashboard - Create real-time dashboard in Fabric
7. create_eventstream - Create Eventstream (empty)
8. create_activator - Create Activator (empty)
9. update_activator_definition - Configure Activator (Reflex) for real-time alerts
10. update_eventstream_definition - Configure Eventstream with Event Hub to Eventhouse flow

Usage:
    python deploy_fabric_rti.py

Environment Variables (from Bicep outputs):
    AZURE_FABRIC_CAPACITY_NAME - Name of the Fabric capacity
    AZURE_FABRIC_WORKSPACE_NAME - Name of the Fabric workspace 
    AZURE_EVENTHOUSE_NAME - Name of the Eventhouse to create
    AZURE_KUSTO_CLUSTER_URI - Kusto cluster connection URI
    AZURE_KUSTO_DATABASE_NAME - Name of the Kusto database
    AZURE_EVENT_HUB_CONNECTION_NAME - Event Hub connection name
    AZURE_EVENT_HUB_NAMESPACE_NAME - Event Hub namespace name
    AZURE_EVENT_HUB_NAME - Event Hub name
    SOLUTION_SUFFIX - Suffix to append to resource names
"""

import os
import sys
from datetime import datetime

# Add current directory to path so we can import local modules
sys.path.append(os.path.dirname(__file__))

# Import pipeline functions
from fabric_workspace import setup_workspace
from fabric_eventhouse import setup_eventhouse  
from fabric_database import setup_fabric_database
from fabric_data_ingester import load_data_to_fabric
from fabric_event_hub import setup_eventhub_connection
from fabric_real_time_dashboard import setup_real_time_dashboard
from fabric_eventstream import create_eventstream
from fabric_activator import create_activator
from fabric_eventstream_definition import update_eventstream_definition
from fabric_activator_definition import update_activator_definition

def execute_step(step_num: int, total_steps: int, description: str, func, **kwargs):
    """
    Execute a single pipeline step.
    
    Args:
        step_num: Current step number
        total_steps: Total number of steps
        description: Description of what this step does
        func: Function to execute
        **kwargs: Arguments to pass to the function
        
    Returns:
        Function result, or None if failed
    """
    print(f"\n📋 Step {step_num}/{total_steps}: {description}")
    print(f"🚀 Executing: {func.__name__}")
    
    if kwargs:
        args_str = ", ".join([f"{k}={v}" for k, v in kwargs.items() if "key" not in k.lower()])
        print(f"   Parameters: {args_str}")

    try:
        result = func(**kwargs)
        print(f"✅ Successfully completed: {func.__name__}")
        return result
            
    except Exception as e:
        print(f"❌ Exception while executing {func.__name__}: {e}")
        return None

def print_summary(executed_steps: list, failed_step: str = None):
    """Print execution summary."""
    print("\n" + "="*60)
    print("📊 EXECUTION SUMMARY")
    print("="*60)
    
    if executed_steps:
        print("✅ Successfully executed functions:")
        for step in executed_steps:
            print(f"   ✓ {step}")
    
    if failed_step:
        print(f"\n❌ Failed at function: {failed_step}")
        print(f"\n💡 To resume from failed point, fix the issue and re-run the deploy_fabric_rti.py script")
    else:
        print(f"\n🎉 All {len(executed_steps)} functions completed successfully!")

def get_required_env_var(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        print(f"❌ Missing required environment variable: {var_name}")
        sys.exit(1)
    return value

def main():
    # Calculate repository root directory (3 levels up from this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    
    # Load configuration from environment variables
    solution_name = get_required_env_var("AZURE_ENV_NAME")
    solution_suffix = get_required_env_var("SOLUTION_SUFFIX")
    subscription_id = get_required_env_var("AZURE_SUBSCRIPTION_ID")
    resource_group_name = get_required_env_var("AZURE_RESOURCE_GROUP")
    capacity_name = get_required_env_var("AZURE_FABRIC_CAPACITY_NAME")
    event_hub_name = get_required_env_var("AZURE_EVENT_HUB_NAME")
    event_hub_namespace_name = get_required_env_var("AZURE_EVENT_HUB_NAMESPACE_NAME")
    event_hub_authorization_rule_name = os.getenv("AZURE_EVENT_HUB_AUTHORIZATION_RULE_NAME", "RootManageSharedAccessKey")
    workspace_name = os.getenv("FABRIC_WORKSPACE_NAME", f"Real-Time Intelligence for Operations - {solution_suffix}")
    eventhouse_name = os.getenv("FABRIC_EVENTHOUSE_NAME", f"rti_eventhouse_{solution_suffix}")
    eventhouse_database_name = os.getenv("FABRIC_EVENTHOUSE_DATABASE_NAME", f"rti_kqldb_{solution_suffix}")
    event_hub_connection_name = os.getenv("FABRIC_EVENT_HUB_CONNECTION_NAME", f"rti_eventhub_connection_{solution_suffix}")
    dashboard_title = os.getenv("FABRIC_RTIDASHBOARD_NAME", f"rti_dashboard_{solution_suffix}")
    eventstream_name = os.getenv("FABRIC_EVENTSTREAM_NAME", f"rti_eventstream_{solution_suffix}")
    activator_name = os.getenv("FABRIC_ACTIVATOR_NAME", f"rti_activator_{solution_suffix}")
    activator_alerts_email = os.getenv("FABRIC_ACTIVATOR_ALERTS_EMAIL", "alerts@contoso.com")

    # The database will be created with the eventhouse and then renamed to the desired name
    # A database of the same name as the eventhouse is auto-created when creating an eventhouse
    # We will rename it to the desired database name using the KQL database API
    print(f"🏭 {solution_name} Initialization")
    print("="*60)
    print(f"Capacity: {capacity_name}")
    print(f"Workspace: {workspace_name}")
    print(f"Eventhouse Name: {eventhouse_name}")
    print(f"Kusto Database Name: {eventhouse_database_name}")
    print(f"Event Hub Connection Name: {event_hub_connection_name}")
    print(f"Event Hub Namespace Name: {event_hub_namespace_name}")
    print(f"Event Hub Name: {event_hub_name}")
    print(f"Activator Name: {activator_name}")
    print(f"Activator Alerts Email: {activator_alerts_email}")
    print(f"Solution Suffix: {solution_suffix}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    executed_steps = []
    
    workspace_result = execute_step(
        1, 10, "Setting up Fabric workspace and capacity assignment",
        setup_workspace,
        capacity_name=capacity_name,
        workspace_name=workspace_name
    )
    if workspace_result is None:
        print_summary(executed_steps, failed_step="setup_workspace")
        sys.exit(1)
    executed_steps.append("setup_workspace")
    workspace_id = workspace_result.get('id')
    
    eventhouse_result = execute_step(
        2, 10, "Setting up Fabric Eventhouse",
        setup_eventhouse,
        eventhouse_name=eventhouse_name,
        workspace_id=workspace_id,
        database_name=eventhouse_database_name
    )
    if eventhouse_result is None:
        print_summary(executed_steps, failed_step="setup_eventhouse")
        sys.exit(1)
    executed_steps.append("setup_eventhouse")

    kusto_cluster_uri = eventhouse_result.get('properties')['queryServiceUri']
    eventhouse_database_id = eventhouse_result.get('properties').get('databasesItemIds')[0]
    
    result = execute_step(
        3, 10, "Setting up Fabric database and table schemas",
        setup_fabric_database,
        cluster_uri=kusto_cluster_uri,
        database_name=eventhouse_database_name
    )
    if result is None:
        print_summary(executed_steps, failed_step="setup_fabric_database")
        sys.exit(1)
    executed_steps.append("setup_fabric_database")
    
    result = execute_step(
        4, 10, "Loading sample data into Fabric database",
        load_data_to_fabric,
        cluster_uri=kusto_cluster_uri,
        database_name=eventhouse_database_name,
        data_path=os.path.join(repo_dir, "infra", "data"),
        refresh_event_dates=True,
        overwrite_existing=True
    )
    if result is None:
        print_summary(executed_steps, failed_step="load_data_to_fabric")
        sys.exit(1)
    executed_steps.append("load_data_to_fabric")
    
    eventhub_connection_result = execute_step(
        5, 10, "Setting up Event Hub connection",
        setup_eventhub_connection,
        connection_name=event_hub_connection_name,
        namespace_name=event_hub_namespace_name,
        event_hub_name=event_hub_name,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        authorization_rule_name=event_hub_authorization_rule_name
    )
    if eventhub_connection_result is None:
        print_summary(executed_steps, failed_step="setup_eventhub_connection")
        sys.exit(1)
    executed_steps.append("setup_eventhub_connection")
    
    # Extract the connection ID for use in eventstream setup
    eventhub_connection_id = eventhub_connection_result.get('id') if eventhub_connection_result else None

    # Build dashboard file path relative to repository root
    rti_dashboard_file_path = os.path.join(repo_dir, "src", "realTimeDashboard", "RealTimeDashboard.json")
    
    dashboard_result = execute_step(
        6, 10, "Setting up Real-time Dashboard",
        setup_real_time_dashboard,
        workspace_id=workspace_id,
        dashboard_title=dashboard_title,
        rti_dashboard_file_path=rti_dashboard_file_path,
        cluster_uri=kusto_cluster_uri,
        eventhouse_database_id=eventhouse_database_id
    )
    if dashboard_result is None:
        print_summary(executed_steps, failed_step="setup_real_time_dashboard")
        sys.exit(1)
    executed_steps.append("setup_real_time_dashboard")

    eventstream_result = execute_step(
        7, 10, "Creating Eventstream",
        create_eventstream,
        workspace_id=workspace_id,
        eventstream_name=eventstream_name
    )
    if eventstream_result is None:
        print_summary(executed_steps, failed_step="create_eventstream")
        sys.exit(1)
    executed_steps.append("create_eventstream")
    eventstream_id = eventstream_result.get('id') if eventstream_result else None

    activator_result = execute_step(
        8, 10, "Creating Activator",
        create_activator,
        workspace_id=workspace_id,
        activator_name=activator_name,
        activator_description=f"Real-time alerts and notifications for {solution_name}"
    )
    if activator_result is None:
        print_summary(executed_steps, failed_step="create_activator")
        sys.exit(1)
    executed_steps.append("create_activator")
    activator_id = activator_result.get('id') if activator_result else None

    # Build activator file path relative to repository root
    activator_file_path = os.path.join(repo_dir, "src", "activator", "ReflexEntities.json")
    
    activator_definition_result = execute_step(
        9, 10, "Updating Activator Definition",
        update_activator_definition,
        workspace_id=workspace_id,
        activator_id=activator_id,
        activator_file_path=activator_file_path,
        eventstream_id=eventstream_id,
        eventstream_name=eventstream_name,
        activator_alerts_email=activator_alerts_email
    )
    if activator_definition_result is None:
        print_summary(executed_steps, failed_step="update_activator_definition")
        sys.exit(1)
    executed_steps.append("update_activator_definition")

    # Build eventstream file path relative to repository root
    eventstream_file_path = os.path.join(repo_dir, "src", "eventstream", "eventstream.json")
    
    eventstream_definition_result = execute_step(
        10, 10, "Updating Eventstream Definition",
        update_eventstream_definition,
        workspace_id=workspace_id,
        eventstream_id=eventstream_result.get('id') if eventstream_result else None,
        eventstream_file_path=eventstream_file_path,
        eventhouse_database_id=eventhouse_database_id,
        eventhouse_database_name=eventhouse_database_name,
        eventhouse_table_name="events",
        eventhub_connection_id=eventhub_connection_id,
        source_name=event_hub_name,
        eventhouse_name=eventhouse_name,
        stream_name=eventstream_name,
        activator_name=activator_name,
        activator_id=activator_id
    )
    if eventstream_definition_result is None:
        print_summary(executed_steps, failed_step="update_eventstream_definition")
        sys.exit(1)
    executed_steps.append("update_eventstream_definition")
    
    # Success!
    print(f"\n🎉 {solution_name} data initialization completed successfully!")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print_summary(executed_steps)

    # Construct URLs for the resources
    dashboard_id = dashboard_result.get('id') if dashboard_result else None
    eventstream_id = eventstream_result.get('id') if eventstream_result else None
    activator_id = activator_result.get('id') if activator_result else None
    eventhub_connection_id = eventhub_connection_result.get('id') if eventhub_connection_result else None
    eventhouse_id = eventhouse_result.get('id') if eventhouse_result else None
    
    workspace_url = f"https://app.fabric.microsoft.com/groups/{workspace_id}?experience=fabric-developer"
    capacity_url = f"https://portal.azure.com/#@/resource/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Fabric/capacities/{capacity_name}/overview"
    eventhouse_url = f"https://app.fabric.microsoft.com/groups/{workspace_id}/eventhouses/{eventhouse_id}?experience=fabric-developer" if eventhouse_id else None
    kql_database_url = f"https://app.fabric.microsoft.com/groups/{workspace_id}/databases/{eventhouse_database_id}?experience=fabric-developer" if eventhouse_database_id else None
    dashboard_url = f"https://app.fabric.microsoft.com/groups/{workspace_id}/kustodashboards/{dashboard_id}?experience=fabric-developer" if dashboard_id else None
    eventstream_url = f"https://app.fabric.microsoft.com/groups/{workspace_id}/eventstreams/{eventstream_id}?experience=fabric-developer" if eventstream_id else None
    activator_url = f"https://app.fabric.microsoft.com/groups/{workspace_id}/reflexes/{activator_id}?experience=fabric-developer" if activator_id else None
    eventhub_connection_url = f"https://app.fabric.microsoft.com/groups/{workspace_id}/gateways?experience=fabric-developer"
    eventhub_namespace_url = f"https://portal.azure.com/#@/resource/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.EventHub/namespaces/{event_hub_namespace_name}/overview"

    print(f"\n" + "="*60)
    print(f"🎉 {solution_name.upper()} DEPLOYMENT COMPLETE!")
    print(f"="*60)
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏷️  Solution: {solution_suffix}")
    
    print(f"\n📋 DEPLOYED RESOURCES:")
    print(f"   🏠 Workspace:    {workspace_name}")
    print(f"   🏛️  Eventhouse:   {eventhouse_name}")
    print(f"   🗄️  Database:     {eventhouse_database_name} (✅ Data loaded)")
    print(f"   📊 Dashboard:    {dashboard_title}")
    print(f"   🌊 Eventstream:  {eventstream_name}")
    print(f"   � Activator:    {activator_name}")
    print(f"   �🔗 Connection:   {event_hub_connection_name}")
    
    print(f"\n🏢 AZURE RESOURCES:")
    print(f"   � Capacity:     {capacity_url}")
    print(f"   📡 Event Hub:    {eventhub_namespace_url}")
    
    print(f"\n🔧 FABRIC RESOURCES:")
    print(f"   🏠 Workspace:    {workspace_url}")
    print(f"   🏛️  Eventhouse:   {eventhouse_url}")
    print(f"   🗄️  Database:     {kql_database_url}")
    print(f"   📊 Dashboard:    {dashboard_url}")
    print(f"   🌊 Eventstream:  {eventstream_url}")
    print(f"   🚨 Activator:    {activator_url}")
    print(f"   🔗 Connections:  {eventhub_connection_url}")
    
    print(f"\n✨ Your real-time intelligence solution is ready!")
    print(f"="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except UnicodeEncodeError as e:
        print(f"\n[ERROR] Unicode encoding error detected:")
        print(f"Your console doesn't support the Unicode characters used in this script.")
        print(f"This is common on Windows systems with certain console configurations.")
        print(f"\nSolutions:")
        print(f"1. Run the script in Windows Terminal or VS Code terminal")
        print(f"2. Use PowerShell 7+ instead of Windows PowerShell")
        print(f"3. Set environment variable: set PYTHONIOENCODING=utf-8")
        print(f"4. Use command: chcp 65001 (to set UTF-8 codepage)")
        print(f"\nTechnical details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)