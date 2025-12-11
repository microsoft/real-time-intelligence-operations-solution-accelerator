# System Architecture and Flow Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [System Flow Diagram](#system-flow-diagram)
3. [Component Architecture](#component-architecture)
4. [Deployment Flow](#deployment-flow)
5. [Runtime Flow](#runtime-flow)
6. [Component Details](#component-details)

---

## Overview

The **Real-Time Intelligence Operations Solution Accelerator** is a comprehensive manufacturing IoT solution that simulates, processes, and analyzes sensor data from manufacturing assets in real-time. It combines Azure Event Hub for data ingestion with Microsoft Fabric for analytics and visualization.

### Key Capabilities
- ✅ Real-time sensor data simulation
- ✅ Streaming data pipeline
- ✅ Time-series analytics with KQL
- ✅ Interactive dashboards
- ✅ Anomaly detection and alerting
- ✅ Automated deployment via Azure Developer CLI

---

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT PHASE                                    │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  Azure CLI   │
    │  azd up      │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │  Infrastructure Provisioning (Bicep)                             │
    │  ┌────────────────────────────────────────────────────────────┐ │
    │  │ • Fabric Capacity                                          │ │
    │  │ • Event Hub Namespace + Event Hub                          │ │
    │  │ • Resource Group                                           │ │
    │  │ • Role Assignments (Azure Event Hubs Data Sender)          │ │
    │  └────────────────────────────────────────────────────────────┘ │
    └───────────────────────────────┬──────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │  Post-Deployment Hook: deploy_fabric_rti.py                      │
    │                                                                   │
    │  Step 1: setup_workspace()                                       │
    │  ├─ Create Fabric workspace                                      │
    │  └─ Assign to Fabric capacity                                    │
    │                                                                   │
    │  Step 2: setup_eventhouse()                                      │
    │  ├─ Create Eventhouse (Kusto cluster)                            │
    │  └─ Rename default database                                      │
    │                                                                   │
    │  Step 3: setup_fabric_database()                                 │
    │  ├─ Create tables: Assets, Events, Sites, Locations, Products    │
    │  └─ Define schemas with KQL                                      │
    │                                                                   │
    │  Step 4: load_data_to_fabric()                                   │
    │  ├─ Generate sample CSV data                                     │
    │  └─ Ingest into Kusto tables                                     │
    │                                                                   │
    │  Step 5: setup_eventhub_connection()                             │
    │  └─ Create Event Hub connection in Fabric                        │
    │                                                                   │
    │  Step 6: setup_real_time_dashboard()                             │
    │  └─ Deploy real-time dashboard with KQL queries                  │
    │                                                                   │
    │  Step 7: create_eventstream()                                    │
    │  └─ Create empty Eventstream item                                │
    │                                                                   │
    │  Step 8: create_activator()                                      │
    │  └─ Create empty Activator (Reflex) item                         │
    │                                                                   │
    │  Step 9: update_activator_definition()                           │
    │  ├─ Configure vibration threshold alerts                         │
    │  └─ Set up email/Teams notifications                             │
    │                                                                   │
    │  Step 10: update_eventstream_definition()                        │
    │  ├─ Connect Event Hub source                                     │
    │  └─ Configure Eventhouse destination                             │
    └───────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                          RUNTIME PHASE                                       │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │ event_simulator  │
    │     .py          │
    └────────┬─────────┘
             │
             │ Reads asset configuration
             ▼
    ┌──────────────────┐
    │   assets.csv     │◄─── Generated by sample_data.py
    │   products.csv   │
    └────────┬─────────┘
             │
             │ For each asset, every N seconds:
             │
    ┌────────▼─────────────────────────────────────────┐
    │  AssetSimulator Threads                          │
    │  ┌────────────────────────────────────────────┐  │
    │  │ Asset 1: Generate sensor readings          │  │
    │  │  • Vibration: 45.2 Hz                      │  │
    │  │  • Temperature: 72.5°C                     │  │
    │  │  • Humidity: 58%                           │  │
    │  │  • Speed: 1250 RPM                         │  │
    │  │  • DefectProbability: 0.15                 │  │
    │  └────────────────────────────────────────────┘  │
    │  ┌────────────────────────────────────────────┐  │
    │  │ Asset 2: Generate sensor readings          │  │
    │  └────────────────────────────────────────────┘  │
    │  ┌────────────────────────────────────────────┐  │
    │  │ Asset N: Generate sensor readings          │  │
    │  └────────────────────────────────────────────┘  │
    └────────┬───────────────────────────────────────┘
             │
             │ JSON event payload
             ▼
    ┌──────────────────────┐
    │  EventHubService     │
    │  send_event()        │
    └────────┬─────────────┘
             │
             │ HTTPS/AMQP
             ▼
    ┌───────────────────────────────────────────────┐
    │         Azure Event Hub                       │
    │  ┌─────────────────────────────────────────┐  │
    │  │  Event Buffer (Partitioned)             │  │
    │  │  • Partition 0: Events 1, 4, 7...       │  │
    │  │  • Partition 1: Events 2, 5, 8...       │  │
    │  │  • Partition 2: Events 3, 6, 9...       │  │
    │  └─────────────────────────────────────────┘  │
    └────────┬──────────────────────────────────────┘
             │
             │ Fabric Eventstream pulls data
             ▼
    ┌────────────────────────────────────────────────┐
    │     Microsoft Fabric Eventstream               │
    │  ┌──────────────────────────────────────────┐  │
    │  │  Source: Event Hub Connection            │  │
    │  │    ↓                                     │  │
    │  │  Transformation: (Optional)              │  │
    │  │    ↓                                     │  │
    │  │  Destination: Eventhouse KQL Database    │  │
    │  └──────────────────────────────────────────┘  │
    └────────┬───────────────────────────────────────┘
             │
             │ Continuous ingestion
             ▼
    ┌────────────────────────────────────────────────┐
    │    Microsoft Fabric Eventhouse                 │
    │    (Kusto/ADX Database)                        │
    │  ┌──────────────────────────────────────────┐  │
    │  │  Table: Events                           │  │
    │  │  ├─ Id, AssetId, ProductId              │  │
    │  │  ├─ Vibration, Temperature, Humidity     │  │
    │  │  ├─ Speed, DefectProbability             │  │
    │  │  └─ Timestamp, BatchId                   │  │
    │  │                                          │  │
    │  │  Table: Assets                           │  │
    │  │  ├─ Id, Name, SiteId                     │  │
    │  │  └─ Type, SerialNumber                   │  │
    │  │                                          │  │
    │  │  Tables: Sites, Locations, Products      │  │
    │  └──────────────────────────────────────────┘  │
    └────────┬───────────────┬───────────────────────┘
             │               │
             │               │ KQL Queries
    ┌────────▼────────┐     ┌▼──────────────────────┐
    │  Real-Time      │     │  Fabric Activator     │
    │  Dashboard      │     │  (Reflex)             │
    │                 │     │                       │
    │  Page 1:        │     │  Rule 1:              │
    │  • Asset KPIs   │     │  IF Vibration > 60Hz  │
    │  • Event volume │     │  THEN Send alert      │
    │  • Defects      │     │  ├─ Email             │
    │                 │     │  └─ Teams message     │
    │  Page 2:        │     │                       │
    │  • Trends       │     │  Rule 2:              │
    │  • Anomalies    │     │  IF DefectProb > 0.8  │
    │  • Analytics    │     │  THEN Send alert      │
    └─────────────────┘     └───────────────────────┘
             │                       │
             │                       │
             ▼                       ▼
    ┌─────────────────────────────────────────┐
    │         End Users                       │
    │  • Operations Manager                   │
    │  • Plant Engineers                      │
    │  • Quality Assurance Team               │
    └─────────────────────────────────────────┘
```

---

## Component Architecture

### 🏗️ Infrastructure Layer (Azure)

```
┌─────────────────────────────────────────────────────────┐
│                    Azure Subscription                    │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Resource Group                             │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  Event Hub Namespace                         │ │ │
│  │  │  ├─ Event Hub: manufacturing-events          │ │ │
│  │  │  ├─ Partitions: 2-32                         │ │ │
│  │  │  └─ Retention: 1-7 days                      │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  Fabric Capacity (F2/F4/F8...)               │ │ │
│  │  │  ├─ Compute Units: 2-2048                    │ │ │
│  │  │  └─ Workspaces: 1+                           │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 📊 Microsoft Fabric Layer

```
┌──────────────────────────────────────────────────────────────┐
│              Fabric Workspace                                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Eventhouse                                            │ │
│  │  └─ KQL Database (Azure Data Explorer)                │ │
│  │     ├─ High-performance time-series storage           │ │
│  │     ├─ Columnar compression                           │ │
│  │     └─ KQL query engine                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Eventstream                                           │ │
│  │  └─ No-code data pipeline builder                     │ │
│  │     ├─ Source: Event Hub                              │ │
│  │     ├─ Transformations: (Optional)                    │ │
│  │     └─ Destination: Eventhouse                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Real-Time Dashboard                                   │ │
│  │  └─ KQL-based visualizations                          │ │
│  │     ├─ Auto-refresh: 30s intervals                    │ │
│  │     ├─ Interactive filters                            │ │
│  │     └─ Multiple pages                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Activator (Reflex)                                    │ │
│  │  └─ Real-time alerting engine                         │ │
│  │     ├─ Rule-based triggers                            │ │
│  │     ├─ Threshold monitoring                           │ │
│  │     └─ Actions: Email, Teams, Power Automate          │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Deployment Flow

### Phase 1: Infrastructure Provisioning (Bicep)

```yaml
File: infra/main.bicep
├─ Creates Azure resources
│  ├─ Resource Group
│  ├─ Event Hub Namespace
│  │  └─ Event Hub
│  └─ Fabric Capacity
│
└─ Outputs environment variables
   ├─ AZURE_EVENT_HUB_NAMESPACE_HOSTNAME
   ├─ AZURE_EVENT_HUB_NAME
   ├─ AZURE_FABRIC_CAPACITY_NAME
   └─ AZURE_KUSTO_CLUSTER_URI
```

### Phase 2: Fabric Configuration (Python)

```python
# Orchestrated by: deploy_fabric_rti.py

Step 1: Workspace Setup
  ├─ File: fabric_workspace.py
  ├─ Function: setup_workspace()
  └─ Actions:
     ├─ Create workspace or use existing
     └─ Assign to Fabric capacity

Step 2: Eventhouse Creation
  ├─ File: fabric_eventhouse.py
  ├─ Function: setup_eventhouse()
  └─ Actions:
     ├─ Create Eventhouse item
     ├─ Wait for provisioning (LRO)
     └─ Rename default database

Step 3: Database Schema
  ├─ File: fabric_database.py
  ├─ Function: setup_fabric_database()
  └─ Actions:
     └─ Create tables:
        ├─ Assets(Id, Name, SiteId, Type, SerialNumber, MaintenanceStatus)
        ├─ Events(Id, AssetId, ProductId, Timestamp, Vibration, Temp, ...)
        ├─ Sites(Id, Name, LocationId, PlantType)
        ├─ Locations(Id, City, Country)
        └─ Products(Id, Name, CategoryId, ListPrice, UnitCost)

Step 4: Data Loading
  ├─ File: fabric_data_ingester.py + sample_data.py
  ├─ Function: load_data_to_fabric()
  └─ Actions:
     ├─ Generate sample CSV files
     │  ├─ 1 location (Ho Chi Minh City)
     │  ├─ 5 sites
     │  ├─ 20 assets (4 per site)
     │  ├─ 6 products
     │  └─ 500 historical events
     └─ Ingest via Kusto Ingestion Client

Step 5: Event Hub Connection
  ├─ File: fabric_event_hub.py
  ├─ Function: setup_eventhub_connection()
  └─ Actions:
     └─ Create Event Hub connection item in Fabric

Step 6: Dashboard Creation
  ├─ File: fabric_real_time_dashboard.py
  ├─ Function: setup_real_time_dashboard()
  └─ Actions:
     └─ Upload dashboard JSON definition
        ├─ Page 1: Operations Overview
        └─ Page 2: Analytics & Trends

Step 7-8: Create Items
  ├─ Files: fabric_eventstream.py, fabric_activator.py
  └─ Create empty Eventstream and Activator items

Step 9: Activator Configuration
  ├─ File: fabric_activator_definition.py
  ├─ Function: update_activator_definition()
  └─ Actions:
     └─ Configure alert rules:
        ├─ Vibration threshold (>60 Hz)
        └─ Actions: Email alerts

Step 10: Eventstream Configuration
  ├─ File: fabric_eventstream_definition.py
  ├─ Function: update_eventstream_definition()
  └─ Actions:
     └─ Configure data flow:
        ├─ Source: Event Hub connection
        └─ Destination: Eventhouse/Events table
```

---

## Runtime Flow

### Data Generation & Ingestion

```
┌─────────────────────────────────────────────────┐
│  1. Event Simulator Initialization              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  File: event_simulator.py                       │
│                                                  │
│  • Read assets.csv (20 assets)                  │
│  • Read products.csv (6 products)               │
│  • Initialize EventHubService                   │
│  • Create AssetSimulator per asset              │
│  • Start simulation threads                     │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  2. Asset Simulation Loop (per thread)          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Class: AssetSimulator                          │
│                                                  │
│  Every N seconds (default: 5s):                 │
│  1. Select random product                       │
│  2. Generate sensor readings:                   │
│     • Vibration: Normal(50, 5) Hz               │
│     • Temperature: Normal(70, 5) °C             │
│     • Humidity: Normal(50, 10) %                │
│     • Speed: Normal(1200, 100) RPM              │
│  3. Calculate defect probability:               │
│     • Formula based on thresholds               │
│  4. Create Event object                         │
│  5. Convert to JSON                             │
│  6. Send to Event Hub                           │
│                                                  │
│  Anomaly Mode:                                  │
│  • Vibration * 2-3x                             │
│  • Temperature +20-30°C                         │
│  • Defect probability >> 0.8                    │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  3. Event Hub Service                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Class: EventHubService                         │
│  File: event_hub_service.py                     │
│                                                  │
│  • Authenticate with DefaultAzureCredential     │
│  • Create EventData with JSON payload           │
│  • Set content-type metadata                    │
│  • Send to Event Hub partition                  │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  4. Azure Event Hub                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                  │
│  • Partitioned buffer (2-32 partitions)         │
│  • FIFO ordering per partition                  │
│  • Retention: 1-7 days                          │
│  • Throughput: Up to 1 GB/s                     │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  5. Fabric Eventstream                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                  │
│  • Continuously polls Event Hub                 │
│  • Deserializes JSON events                     │
│  • Optional transformations                     │
│  • Batch writes to Eventhouse                   │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  6. Eventhouse (Kusto)                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                  │
│  • Columnar storage (compressed)                │
│  • Automatic indexing                           │
│  • Materialized views for aggregations          │
│  • Query optimization                           │
└─────────────────────────────────────────────────┘
```

### Data Consumption

```
┌─────────────────────────────────────────────────┐
│  Real-Time Dashboard                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                  │
│  KQL Queries (auto-refresh every 30s):          │
│                                                  │
│  • Asset Event Volume:                          │
│    Events                                       │
│    | summarize count() by bin(Timestamp, 5m)   │
│                                                  │
│  • Average Vibration by Asset:                  │
│    Events                                       │
│    | summarize avg(Vibration) by AssetId       │
│                                                  │
│  • Defect Rate Trends:                          │
│    Events                                       │
│    | where DefectProbability > 0.5             │
│    | summarize DefectRate = count() * 100.0    │
│      / toscalar(Events | count())              │
│                                                  │
│  • Asset Details (with joins):                  │
│    Events                                       │
│    | join kind=inner Assets on $left.AssetId   │
│      == $right.Id                               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Fabric Activator (Reflex)                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                  │
│  Rule 1: High Vibration Alert                   │
│  ───────────────────────────────                │
│  Trigger:                                       │
│    Events                                       │
│    | where Vibration > 60                       │
│                                                  │
│  Action:                                        │
│    Send Email:                                  │
│    └─ Subject: "High Vibration Alert"          │
│       Body: "Asset {AssetId} vibration is      │
│              {Vibration} Hz"                    │
│                                                  │
│  Rule 2: Defect Probability Alert               │
│  ─────────────────────────────────────          │
│  Trigger:                                       │
│    Events                                       │
│    | where DefectProbability > 0.8              │
│                                                  │
│  Action:                                        │
│    Send Teams Message:                          │
│    └─ Channel: Quality Assurance               │
│       Message: "High defect probability        │
│                 detected"                       │
└─────────────────────────────────────────────────┘
```

---

## Component Details

### 📦 Python Modules

#### **Data Models**

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `asset.py` | Asset data structure | `Asset`, `AssetMetric`, `AssetType` |
| `event.py` | Event data structure | `Event` with sensor readings |

#### **Data Generation**

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `sample_data.py` | Generate sample CSV data | `generate_locations()`, `generate_sites()`, `generate_assets()`, `generate_products()`, `generate_events()` |

#### **Event Simulation**

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `event_simulator.py` | Real-time event generator | `AssetSimulator`, `SimulationController`, interactive commands |
| `event_hub_service.py` | Azure Event Hub client | `EventHubService.send_event()` |

#### **Deployment Orchestration**

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `deploy_fabric_rti.py` | Main deployment orchestrator | `execute_step()`, calls all setup functions |
| `remove_fabric_rti.py` | Workspace cleanup | Deletes Fabric workspace |

#### **Fabric API Clients**

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `fabric_api.py` | Core Fabric REST API | `FabricApiClient`, `FabricWorkspaceApiClient` |
| `graph_api.py` | Microsoft Graph API | `GraphApiClient` for identity lookups |

#### **Fabric Resource Provisioning**

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `fabric_workspace.py` | Workspace creation | `setup_workspace()` |
| `fabric_eventhouse.py` | Eventhouse setup | `setup_eventhouse()` |
| `fabric_database.py` | Table schema creation | `setup_fabric_database()`, `create_table()` |
| `fabric_event_hub.py` | Event Hub connection | `setup_eventhub_connection()` |
| `fabric_eventstream.py` | Eventstream item | `create_eventstream()` |
| `fabric_activator.py` | Activator item | `create_activator()` |
| `fabric_real_time_dashboard.py` | Dashboard deployment | `setup_real_time_dashboard()` |

#### **Fabric Configuration**

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `fabric_eventstream_definition.py` | Configure data pipeline | `update_eventstream_definition()` |
| `fabric_activator_definition.py` | Configure alert rules | `update_activator_definition()` |

#### **Data Operations**

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `fabric_data_ingester.py` | Load CSV into Kusto | `ingest_data_to_fabric()`, `create_ingestion_client()` |

#### **Access Management**

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `add_fabric_workspace_admins.py` | Add workspace admins | `add_admin_to_workspace()`, `detect_principal_type()` |

#### **Utilities**

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `azd_env_loader.py` | Load AZD environment | `AZDEnvironmentLoader`, reads `.azure/<env>/.env` |

---

### 🗄️ Database Schema

#### **Events Table** (Time-series data)
```sql
Events (
    Id: string,               -- Unique event identifier
    AssetId: string,          -- Reference to Assets.Id
    ProductId: string,        -- Reference to Products.Id
    Timestamp: datetime,      -- Event timestamp (UTC)
    BatchId: string,          -- Manufacturing batch
    Vibration: real,          -- Hz
    Temperature: real,        -- °C
    Humidity: real,           -- %
    Speed: real,              -- RPM
    DefectProbability: real   -- 0.0 - 1.0
)
```

#### **Assets Table** (Reference data)
```sql
Assets (
    Id: string,               -- Unique asset identifier
    Name: string,             -- Display name
    SiteId: int,              -- Reference to Sites.Id
    Type: string,             -- Assembly/Press/Conveyor/Packaging
    SerialNumber: string,     -- Hardware serial
    MaintenanceStatus: string -- Done/Pending/Scheduled
)
```

#### **Sites Table**
```sql
Sites (
    Id: int,
    Name: string,
    LocationId: int,          -- Reference to Locations.Id
    PlantType: string         -- Assembly/Supplier/Warehouse
)
```

#### **Locations Table**
```sql
Locations (
    Id: int,
    City: string,
    Country: string
)
```

#### **Products Table**
```sql
Products (
    Id: string,
    Name: string,
    CategoryId: int,
    CategoryName: string,
    ListPrice: real,
    UnitCost: real
)
```

---

### 🎯 Key KQL Queries

#### Asset Performance
```kql
Events
| where Timestamp > ago(1h)
| join kind=inner Assets on $left.AssetId == $right.Id
| summarize 
    AvgVibration = avg(Vibration),
    AvgTemp = avg(Temperature),
    EventCount = count(),
    AvgDefectProb = avg(DefectProbability)
    by AssetId, Name, Type
| order by AvgDefectProb desc
```

#### Anomaly Detection
```kql
Events
| where Timestamp > ago(30m)
| where Vibration > 60 or Temperature > 90 or DefectProbability > 0.8
| join kind=inner Assets on $left.AssetId == $right.Id
| project Timestamp, Name, Vibration, Temperature, DefectProbability
| order by Timestamp desc
```

#### Time-Series Trends
```kql
Events
| where Timestamp > ago(24h)
| summarize 
    AvgVibration = avg(Vibration),
    AvgTemp = avg(Temperature),
    DefectRate = countif(DefectProbability > 0.5) * 100.0 / count()
    by bin(Timestamp, 15m)
| render timechart
```

---

### 🚨 Alerting Rules

#### Vibration Threshold Alert
- **Trigger Condition**: `Vibration > 60 Hz`
- **Frequency**: Real-time (streaming)
- **Action**: Send email notification
- **Recipients**: Operations team
- **Priority**: High

#### Defect Probability Alert
- **Trigger Condition**: `DefectProbability > 0.8`
- **Frequency**: Real-time (streaming)
- **Action**: Send Teams message
- **Channel**: Quality Assurance
- **Priority**: Critical

---

### 🔐 Security & Authentication

#### Azure Authentication
- **Method**: DefaultAzureCredential
- **Supports**: 
  - Azure CLI (`az login`)
  - Managed Identity
  - Service Principal
  - Visual Studio
  - Environment variables

#### Fabric Authentication
- **Method**: Azure CLI credential → Fabric API token
- **Scope**: `https://api.fabric.microsoft.com/.default`
- **Token Lifetime**: Cached with automatic refresh

#### Role Assignments
- **Event Hub**: Azure Event Hubs Data Sender
- **Fabric**: Workspace Admin (for deployment)

---

### 📊 Performance Characteristics

#### Event Simulator
- **Throughput**: ~4 events/second per asset (configurable)
- **Concurrency**: Multi-threaded (one thread per asset)
- **Event Size**: ~250 bytes JSON per event
- **Total Rate**: 20 assets × 4 events/s = 80 events/s = ~20 KB/s

#### Event Hub
- **Partitions**: 2 (default, configurable)
- **Retention**: 1 day (configurable up to 7 days)
- **Throughput Units**: 1 TU = 1 MB/s ingress

#### Eventhouse (Kusto)
- **Ingestion Latency**: <10 seconds (typical)
- **Query Latency**: <1 second for most queries
- **Compression**: ~10x (typical for time-series data)
- **Retention**: Configurable (default: unlimited)

---

### 🛠️ Interactive Commands (Event Simulator)

During runtime, the event simulator supports these commands:

| Command | Description | Example |
|---------|-------------|---------|
| `anomaly` or `a` | Switch all assets to anomaly mode | `a` |
| `anomaly [#]` | Switch specific asset to anomaly mode | `a 3` |
| `normal` or `n` | Switch all assets to normal mode | `n` |
| `normal [#]` | Switch specific asset to normal mode | `n 2` |
| `status` or `s` | Show current simulation status | `s` |
| `stats` | Show detailed per-asset statistics | `stats` |
| `help` or `h` | Show available commands | `h` |
| `stop` or `q` | Stop the simulation | `q` |

---

### 📈 Sample Dashboard Pages

#### Page 1: Operations Overview
- **Event Volume Chart**: Events per 5-minute window
- **Asset Health Grid**: Current metrics for all assets
- **Defect Rate Gauge**: Real-time defect percentage
- **Recent Alerts**: Last 10 anomalies

#### Page 2: Analytics & Trends
- **Vibration Trends**: Time-series by asset type
- **Temperature Heatmap**: By site and time
- **Product Quality**: Defect rate by product category
- **Maintenance Status**: Asset distribution

---

## 🚀 Getting Started

### Prerequisites
```bash
# Azure CLI
az login

# Azure Developer CLI
azd auth login

# Python packages
pip install -r requirements.txt
```

### Deployment
```bash
# Deploy infrastructure + Fabric resources
azd up

# Add workspace administrators (optional)
python infra/scripts/fabric/add_fabric_workspace_admins.py \
    --fabricAdmins user@contoso.com
```

### Start Event Simulation
```bash
cd infra/scripts
python event_simulator.py --interval 5

# In another terminal, monitor
# Type 'anomaly' to simulate failures
# Type 'status' to see statistics
```

### Access Resources
- **Fabric Workspace**: https://app.fabric.microsoft.com
- **Dashboard**: Navigate to workspace → Real-Time Dashboard
- **Event Hub**: Azure Portal → Event Hubs → Metrics

---

## 📚 References

- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [Azure Event Hubs](https://learn.microsoft.com/azure/event-hubs/)
- [Kusto Query Language (KQL)](https://learn.microsoft.com/azure/data-explorer/kusto/query/)
- [Real-Time Intelligence in Fabric](https://learn.microsoft.com/fabric/real-time-intelligence/)
- [Fabric Activator](https://learn.microsoft.com/fabric/data-activator/)

---

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

---

*Last Updated: November 28, 2025*
