# Fabric Data Ingestion Guide

Loads CSV data into Microsoft Fabric database tables using Azure authentication. This document provides guidance on calling the fabric_data_ingester.py script directly to refresh the sample data (including events) within the KQL database in your Fabric workspace. Execute this script to also refresh the historical event data (via the `--refresh-dates` argument) to match up to today's current date and time to ensure the dashboard displays more recent past results. 

NOTE: This script is called automatically during deployment as part of the `azd up` process. Follow this documentation to see how it can be called separately in order to solely focus on refreshing the data in the workspace.

## Requirements

### Local Environment Pre-requisites

```bash
pip install azure-identity azure-kusto-data azure-kusto-ingest pandas
```

### Fabric Workspace

In order to ingest data into the Fabric Workspace, the executing identity will need sufficient permissions to the Workspace. Ensure the identity is assigned [Contributor rights on the Fabric Workspace](https://learn.microsoft.com/en-us/fabric/fundamentals/give-access-workspaces).

The required `CLUSTER_URI` and `DATABASE_NAME` can be retrieved from Fabric. While in Fabric, navigate to the EventHouse to find the KQL Database to get the `DATABASE_NAME`. Select the database and on the right side there will be a `Query Uri` or `Injest Uri` link/button. Selecting either will copy the required `CLUSTER_URI` value to the clipboard. Supply these values in the command below.

## Usage

```bash
az login
```

```bash
python fabric_data_ingester.py --cluster-uri <CLUSTER_URI> --database <DATABASE_NAME> [OPTIONS]
```

### Required Arguments

- `--cluster-uri` - Fabric cluster URI (e.g., `https://mycluster.region.kusto.fabric.microsoft.com`)
- `--database` - Target database name

### Optional Arguments

- `--data-path` - Path to CSV files directory (default: `../data`)
- `--refresh-dates` - Refresh event timestamps to current date
- `--overwrite` - Overwrite existing data in tables

## Examples

Basic ingestion:
```bash
python fabric_data_ingester.py \
  --cluster-uri https://mycluster.westus.kusto.fabric.microsoft.com \
  --database manufacturing_db
```

Refresh dates and overwrite existing data:
```bash
python fabric_data_ingester.py \
  --cluster-uri https://mycluster.westus.kusto.fabric.microsoft.com \
  --database manufacturing_db \
  --refresh-dates \
  --overwrite
```

Custom data path:
```bash
python fabric_data_ingester.py \
  --cluster-uri https://mycluster.westus.kusto.fabric.microsoft.com \
  --database manufacturing_db \
  --data-path /path/to/csv/files
```

## Expected CSV Files

The script expects these CSV files in the data directory:
- `locations.csv`
- `sites.csv`
- `assets.csv`
- `products.csv`
- `events.csv`

## Authentication

Uses `DefaultAzureCredential` for authentication. Ensure you're authenticated via:
- Azure CLI: `az login`
- Managed Identity
- Environment variables

## Notes

- Ingestion is asynchronous - check Fabric for completion status
- Tables with existing data are skipped unless `--overwrite` is specified
- Event timestamps can be adjusted to current date with `--refresh-dates`
