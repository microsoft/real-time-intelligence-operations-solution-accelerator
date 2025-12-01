# Manufacturing Event Simulator

This event simulator generates realistic manufacturing events for each asset in your `assets.csv` file and sends them to an Azure Event Hub to be ingested into the RTI workspace in Fabric.

## Access Requirement

If you are the owner of the Azure Event Hub deployed with the solution, you already have required access to run this event simulator. If not, you will to be added as the `Azure Event Hubs Data Sender` role by the owner of the Event Hub or your Azure Admin. 

## Quick Start

### 1. Set Environment Variables

NOTE: If the executing environment deployed the resources via AZD following the [deployment guide](./DeploymentGuide.md) in this solution, the required environment variables for the event simulator will be set automatically and this step can be skipped.

If using Powershell, use this [syntax for setting environment variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-7.5#use-the-variable-syntax).

Visit the Azure Portal to get the Event Hub name and connection string of the environment.

```bash
export EVENT_HUB_CONNECTION_STRING="Endpoint=sb://..."
export EVENT_HUB_NAME="<event-hub-name>"
```

### 2. Set Environment Variables (Optional)

```bash
export SIMULATION_INTERVAL="5"        # Seconds between events per asset (default: 5)
export MAX_RUNTIME_SECONDS="300"      # Max runtime in seconds (default: unlimited)
export ASSETS_CSV_PATH="../data/assets.csv"     # Path to assets file
export PRODUCTS_CSV_PATH="../data/products.csv" # Path to products file
```

### 3. Run the Simulator

```bash
cd src/simulator
```

```bash
# Basic usage (runs until Ctrl+C, quit, or q)
python event_simulator.py

# With custom interval (2 seconds between events)
python event_simulator.py --interval 2

# Run for specific duration (5 minutes)
python event_simulator.py --max-runtime 300

# Use custom data files
python event_simulator.py --assets-csv /path/to/assets.csv --products-csv /path/to/products.csv
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--interval` | Seconds between events per asset | 5.0 |
| `--max-runtime` | Maximum runtime in seconds | Unlimited |
| `--assets-csv` | Path to assets.csv file | infra/data/assets.csv |
| `--products-csv` | Path to products.csv file | infra/data/products.csv |

## Interactive Runtime Controls

While the simulator is running, you can control it using these commands:

| Command | Aliases | Description |
|---------|---------|-------------|
| `anomaly [#]` | `a [#]` | Switch to anomaly mode (all assets or specific asset #) |
| `normal [#]` | `n [#]` | Switch to normal mode (all assets or specific asset #) |
| `status` | `s` | Show current mode and statistics |
| `stats` | | Show detailed per-asset breakdown |
| `help` | `h`, `?` | Show available commands |
| `stop` | `q` | Stop the simulation |

### Example Interactive Usage

```bash
# Start the simulator
python event_simulator.py --interval 2

# During runtime, type commands:
anomaly          # Switch ALL assets to anomaly mode
anomaly 2        # Switch only asset #2 to anomaly mode
normal 1         # Switch asset #1 back to normal mode
status           # Check current statistics (shows which assets are in which mode)
stats            # View per-asset breakdown with modes
normal           # Switch ALL assets back to normal mode
stop             # Stop simulation
```

## Event Types

### Normal Mode (Default)
- Realistic operational sensor readings
- Low defect probability (typically < 2%)
- Values within normal operating ranges

### Anomaly Mode
- Extreme sensor readings indicating equipment issues
- High defect probability (typically > 50%)  
- Simulates equipment failures and maintenance needs

## How It Works

### Asset Simulation

Each asset from `assets.csv` gets its own simulator thread that:

1. **Generates Random Event**: Creates realistic readings based on asset type
2. **Calculates Defects**: Uses sensor conditions to estimate defect probability
3. **Sends Events**: Transmits events to Event Hub which will then stream to Eventstream in Fabric
5. **Responds to Mode Changes**: Switches between normal and anomaly events

## Usage Scenarios

### Equipment Failure Testing - Single Asset
1. Start simulation
2. Use `anomaly 2` to simulate equipment failure on asset #2 only
3. Monitor your data pipeline's response to anomalous data from one asset
4. Other assets continue generating normal events for comparison
5. Use `normal 2` to simulate repair completion

### Equipment Failure Testing - All Assets
1. Start simulation
2. Use `anomaly` command to simulate widespread equipment issues
3. Monitor system response to multiple failing assets
4. Use `normal` to simulate all equipment returning to normal

### Quality Control Validation
- Use `stats` command to monitor defect rates per asset in real-time
- Test alerting thresholds with targeted anomaly mode on specific assets
- Validate quality control system responses
