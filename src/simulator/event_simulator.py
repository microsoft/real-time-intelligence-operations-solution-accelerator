#!/usr/bin/env python3
"""
Event Simulator for Manufacturing Assets

This script simulates manufacturing events for each asset found in assets.csv.
It reads the asset data, then continuously generates and sends realistic manufacturing
events to an Azure Event Hub using the Event class and EventHubService class.

Features:
- Reads assets from CSV file
- Generates realistic sensor data (temperature, vibration, humidity, speed)
- Calculates defect probability based on sensor readings
- Sends events to Event Hub on configurable schedule
- Supports multiple concurrent asset simulations
- Interactive runtime controls for switching between normal and anomaly modes
- Real-time statistics and monitoring
- Graceful shutdown on Ctrl+C

Interactive Commands (available during runtime):
- 'anomaly [#]' or 'a [#]' - Switch to anomaly mode (all assets or specific asset #)
- 'normal [#]' or 'n [#]' - Switch to normal mode (all assets or specific asset #)
- 'status' or 's' - Show current simulation status
- 'stats' - Show detailed per-asset statistics
- 'help' or 'h' - Show available commands
- 'stop' or 'q' - Stop the simulation

Usage:
    python event_simulator.py [options]

Environment Variables:
    AZURE_EVENT_HUB_NAMESPACE_HOSTNAME - Azure Event Hub namespace (e.g., myeventhub.servicebus.windows.net)
    AZURE_EVENT_HUB_NAME - Name of the Event Hub
    ASSETS_CSV_PATH - Path to assets.csv file (default: infra/data/assets.csv)
    PRODUCTS_CSV_PATH - Path to products.csv file (default: infra/data/products.csv)
    SIMULATION_INTERVAL - Seconds between events per asset (default: 5)
    MAX_RUNTIME_SECONDS - Maximum runtime in seconds (default: unlimited)

Example:
    python event_simulator.py --interval 2 --max-runtime 300
    # During runtime:
    # Type 'anomaly' to switch all assets to anomaly mode
    # Type 'anomaly 2' to switch only asset #2 to anomaly mode
    # Type 'normal 1' to switch asset #1 back to normal mode
    # Type 'status' to see current statistics
"""

import argparse
import csv
import os
import random
import signal
import sys
import threading
import time
import sys
from pathlib import Path

# Add parent directory to Python path to allow imports from sibling directories
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from typing import List, Dict, Optional

# Import our project classes
from entities.event import Event
from entities.asset import AssetType
from simulator.event_hub_service import EventHubService
from azd_env_loader import AZDEnvironmentLoader

class AssetSimulator:
    """Simulates events for a single manufacturing asset."""
    
    def __init__(self, asset_id: str, asset_name: str, asset_type_name: str, 
                 products: List[Dict], event_hub_service: EventHubService, index: int):
        self.asset_id = asset_id
        self.asset_name = asset_name
        self.asset_type_name = asset_type_name
        self.asset_type = AssetType.get_types()[self.asset_type_name]
        self.products = products
        self.event_hub_service = event_hub_service
        self.index = index
        self.anomaly_mode = False
        self.is_running = False
        self.thread = None
        self.events_sent = 0
        self.anomaly_events_sent = 0
                
        # Current batch being processed
        self.current_batch_id = self._generate_batch_id()
        self.batch_start_time = datetime.now(timezone.utc)
        self.events_in_batch = 0
        self.max_events_per_batch = random.randint(50, 200)
        
    def _generate_batch_id(self) -> str:
        """Generate a new batch ID."""
        return f"BATCH_{self.asset_id}_{int(time.time())}"
    
    def _get_random_product(self) -> str:
        """Get a random product ID from available products."""
        if not self.products:
            return "P_DEFAULT"
        return random.choice(self.products)['Id']
    
    def _check_set_new_batch(self):
        if self.events_in_batch >= self.max_events_per_batch:
            self.current_batch_id = self._generate_batch_id()
            self.batch_start_time = datetime.now(timezone.utc)
            self.events_in_batch = 0
            self.max_events_per_batch = random.randint(50, 200)

    def _create_event(self, anomaly: bool) -> Event:
        self._check_set_new_batch()

        event = self.asset_type.create_random_event(asset_id=self.asset_id,
                                                    product_id=self._get_random_product(),
                                                    batch_id=self.current_batch_id,
                                                    timestamp=datetime.now(timezone.utc),
                                                    anomaly=anomaly,
                                                    variation_multiplier=random.uniform(2,3))

        self.events_in_batch += 1
        return event
    
    def start(self, interval_seconds: float):
        """Start the event simulation for this asset."""
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._simulation_loop, args=(interval_seconds,))
        self.thread.daemon = True
        self.thread.start()
        print(f"🚀 Started simulation for {self.asset_name} (ID: {self.asset_id})")
    
    def stop(self):
        """Stop the event simulation for this asset."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        total_normal = self.events_sent - self.anomaly_events_sent
        print(f"⏹️  Stopped simulation for {self.asset_name} - {self.events_sent} total events "
              f"(Normal: {total_normal}, Anomalies: {self.anomaly_events_sent})")
    
    def _simulation_loop(self, interval_seconds: float):
        """Main simulation loop for this asset."""
        while self.is_running:
            try:
                # Check if we should generate anomaly or normal event
                if self.anomaly_mode:
                    event = self._create_event(anomaly=True)
                    self.anomaly_events_sent += 1
                else:
                    event = self._create_event(anomaly=False)
                
                self.event_hub_service.send_event(event.to_dict())
                self.events_sent += 1
            
                # Wait for next event
                time.sleep(interval_seconds)
                
            except Exception as e:
                print(f"❌ Error in simulation for {self.asset_name}: {e}")
                time.sleep(1)  # Short delay before retrying


class EventSimulatorManager:
    """Manages multiple asset simulators."""
    
    def __init__(self):
        self.simulators: List[AssetSimulator] = []
        self.is_running = False
        self.start_time = None
        self.max_runtime_seconds = None
        self.command_thread = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received shutdown signal ({signum})")
        self.stop_all_simulators()
        sys.exit(0)
    
    def load_assets(self, assets_csv_path: str) -> List[Dict]:
        """Load assets from CSV file."""
        assets = []
        try:
            with open(assets_csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    assets.append(row)
            print(f"📁 Loaded {len(assets)} assets from {assets_csv_path}")
        except FileNotFoundError:
            print(f"❌ Assets file not found: {assets_csv_path}")
            raise
        except Exception as e:
            print(f"❌ Error loading assets: {e}")
            raise
        return assets
    
    def load_products(self, products_csv_path: str) -> List[Dict]:
        """Load products from CSV file."""
        products = []
        try:
            with open(products_csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    products.append(row)
            print(f"📦 Loaded {len(products)} products from {products_csv_path}")
        except FileNotFoundError:
            print(f"⚠️  Products file not found: {products_csv_path} (will use default)")
        except Exception as e:
            print(f"⚠️  Error loading products: {e} (will use default)")
        return products
    
    def create_simulators(self, assets: List[Dict], products: List[Dict], 
                         event_hub_service: EventHubService):
        """Create asset simulators."""
        self.simulators = []
        for i, asset in enumerate(assets, 1):
            simulator = AssetSimulator(
                asset_id=asset['Id'],
                asset_name=asset['Name'],
                asset_type_name=asset['Type'],
                products=products,
                event_hub_service=event_hub_service,
                index=i
            )
            self.simulators.append(simulator)
        print(f"🏭 Created simulators for {len(self.simulators)} assets")
    
    def start_all_simulators(self, interval_seconds: float, max_runtime_seconds: Optional[int] = None):
        """Start all asset simulators."""
        if not self.simulators:
            print("❌ No simulators to start")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        self.max_runtime_seconds = max_runtime_seconds
        
        print(f"\n🚀 Starting event simulation for {len(self.simulators)} assets")
        print(f"⏱️  Event interval: {interval_seconds} seconds")
        if max_runtime_seconds:
            print(f"⏰ Max runtime: {max_runtime_seconds} seconds")
        print("="*60)
        
        # Start all simulators
        for simulator in self.simulators:
            simulator.start(interval_seconds)
        
        # Start interactive command interface
        self._start_command_interface()
        
        # Monitor runtime if specified
        if max_runtime_seconds:
            self._monitor_runtime()
        else:
            self._wait_for_shutdown()
    
    def _start_command_interface(self):
        """Start the interactive command interface in a separate thread."""
        self.command_thread = threading.Thread(target=self._command_loop)
        self.command_thread.daemon = True
        self.command_thread.start()
        
        # Show available commands
        print(f"\n🎛️  Interactive Commands Available:")
        print(f"   Type 'anomaly [#]' to switch to anomaly mode (all assets or specific asset #)")
        print(f"   Type 'normal [#]' to switch to normal mode (all assets or specific asset #)")
        print(f"   Type 'status' to show current status")
        print(f"   Type 'stats' to show detailed statistics")
        print(f"   Type 'help' to show this help")
        print(f"   Type 'stop' or press Ctrl+C to stop simulation")
        print(f"   📝 Command input active in background...")
    
    def _command_loop(self):
        """Interactive command loop running in background thread."""
        try:
            while self.is_running:
                try:
                    # Simple blocking input - works on all platforms
                    print(f"\n💬 Enter command (type 'help' for options): ", end='', flush=True)
                    command = input().strip().lower()
                    if command:  # Only process non-empty commands
                        self._handle_command(command)
                    
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    # Silently handle command loop errors to not interrupt main simulation
                    time.sleep(0.1)
                    continue
                        
        except Exception as e:
            # Silently handle command loop errors to not interrupt main simulation
            pass
    
    def _handle_command(self, command: str):
        """Handle interactive commands."""
        parts = command.split()
        cmd = parts[0] if parts else ''
        
        if cmd in ['anomaly', 'a']:
            asset_num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            self._switch_to_anomaly_mode(asset_num)
        elif cmd in ['normal', 'n']:
            asset_num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            self._switch_to_normal_mode(asset_num)
        elif cmd in ['status', 's']:
            self._show_status()
        elif cmd in ['stats', 'statistics']:
            self._show_detailed_stats()
        elif cmd in ['help', 'h', '?']:
            self._show_help()
        elif cmd in ['stop', 'quit', 'exit', 'q']:
            print(f"\n🛑 Stopping simulation via command...")
            self.stop_all_simulators()
        elif command.strip():
            print(f"❓ Unknown command: '{command}'. Type 'help' for available commands.")
    
    def _switch_to_anomaly_mode(self, asset_num: Optional[int] = None):
        """Switch simulators to anomaly mode."""
        if asset_num is not None:
            if 1 <= asset_num <= len(self.simulators):
                simulator = self.simulators[asset_num - 1]
                simulator.anomaly_mode = True
                print(f"🚨 SWITCHED ASSET #{asset_num} ({simulator.asset_name}) TO ANOMALY MODE")
            else:
                print(f"❌ Invalid asset number. Valid range: 1-{len(self.simulators)}")
        else:
            for simulator in self.simulators:
                simulator.anomaly_mode = True
            print(f"🚨 SWITCHED ALL ASSETS TO ANOMALY MODE")
    
    def _switch_to_normal_mode(self, asset_num: Optional[int] = None):
        """Switch simulators to normal mode."""
        if asset_num is not None:
            if 1 <= asset_num <= len(self.simulators):
                simulator = self.simulators[asset_num - 1]
                simulator.anomaly_mode = False
                print(f"✅ SWITCHED ASSET #{asset_num} ({simulator.asset_name}) TO NORMAL MODE")
            else:
                print(f"❌ Invalid asset number. Valid range: 1-{len(self.simulators)}")
        else:
            for simulator in self.simulators:
                simulator.anomaly_mode = False
            print(f"✅ SWITCHED ALL ASSETS TO NORMAL MODE")
    
    def _show_status(self):
        """Show current simulation status."""
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        total_events = sum(s.events_sent for s in self.simulators)
        total_anomalies = sum(s.anomaly_events_sent for s in self.simulators)
        total_normal = total_events - total_anomalies
        
        anomaly_assets = [s for s in self.simulators if s.anomaly_mode]
        normal_assets = [s for s in self.simulators if not s.anomaly_mode]
        
        print(f"\n📊 SIMULATION STATUS")
        print(f"   Runtime: {elapsed:.1f} seconds")
        print(f"   Active Assets: {len(self.simulators)}")
        print(f"   Anomaly Mode: {len(anomaly_assets)} assets")
        print(f"   Normal Mode: {len(normal_assets)} assets")
        print(f"   Total Events: {total_events} (Normal: {total_normal}, Anomalies: {total_anomalies})")
        print(f"   Events/sec: {total_events/elapsed:.2f}" if elapsed > 0 else "   Events/sec: 0")
        
        if anomaly_assets:
            print(f"\n   Assets in Anomaly Mode:")
            for s in anomaly_assets:
                print(f"      #{s.index} - {s.asset_name}")
    
    def _show_detailed_stats(self):
        """Show detailed per-asset statistics."""
        print(f"\n📈 DETAILED STATISTICS")
        print(f"{'#':<3} {'Asset Name':<20} {'Mode':<8} {'Total':<8} {'Normal':<8} {'Anomaly':<8} {'Anomaly %':<10}")
        print("-" * 75)
        
        for simulator in self.simulators:
            total = simulator.events_sent
            anomalies = simulator.anomaly_events_sent
            normal = total - anomalies
            anomaly_pct = (anomalies / total * 100) if total > 0 else 0
            mode = "ANOMALY" if simulator.anomaly_mode else "NORMAL"
            
            print(f"{simulator.index:<3} {simulator.asset_name:<20} {mode:<8} {total:<8} {normal:<8} {anomalies:<8} {anomaly_pct:<10.1f}%")
    
    def _show_help(self):
        """Show help for available commands."""
        print(f"\n🎛️  AVAILABLE COMMANDS:")
        print(f"   anomaly [#], a [#]  - Switch to anomaly mode (all or specific asset)")
        print(f"   normal [#], n [#]   - Switch to normal mode (all or specific asset)")
        print(f"   status, s           - Show current simulation status")
        print(f"   stats               - Show detailed per-asset statistics")
        print(f"   help, h, ?          - Show this help message")
        print(f"   stop, q             - Stop the simulation")
        print(f"\n   Examples:")
        print(f"      anomaly        - Set all assets to anomaly mode")
        print(f"      anomaly 2      - Set asset #2 to anomaly mode")
        print(f"      normal 1       - Set asset #1 to normal mode")
    
    def _monitor_runtime(self):
        """Monitor runtime and stop when limit is reached."""
        while self.is_running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed >= self.max_runtime_seconds:
                print(f"\n⏰ Maximum runtime ({self.max_runtime_seconds}s) reached")
                self.stop_all_simulators()
                break
            time.sleep(1)
    
    def _wait_for_shutdown(self):
        """Wait for shutdown signal."""
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_all_simulators()
    
    def stop_all_simulators(self):
        """Stop all asset simulators."""
        if not self.is_running:
            return
            
        print(f"\n🛑 Stopping all simulators...")
        self.is_running = False
        
        for simulator in self.simulators:
            simulator.stop()
        
        # Print summary
        total_events = sum(s.events_sent for s in self.simulators)
        total_anomalies = sum(s.anomaly_events_sent for s in self.simulators)
        total_normal = total_events - total_anomalies
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        print("\n" + "="*60)
        print("📊 SIMULATION SUMMARY")
        print("="*60)
        print(f"Runtime: {elapsed:.1f} seconds")
        print(f"Total events sent: {total_events}")
        print(f"  Normal events: {total_normal}")
        print(f"  Anomaly events: {total_anomalies}")
        print(f"  Anomaly rate: {total_anomalies/total_events*100:.1f}%" if total_events > 0 else "  Anomaly rate: 0%")
        print(f"Events per second: {total_events/elapsed:.2f}" if elapsed > 0 else "Events per second: 0")
        print(f"Active assets: {len(self.simulators)}")
        print("\nPer-asset summary:")
        for simulator in self.simulators:
            normal_events = simulator.events_sent - simulator.anomaly_events_sent
            anomaly_pct = (simulator.anomaly_events_sent / simulator.events_sent * 100) if simulator.events_sent > 0 else 0
            print(f"  {simulator.asset_name}: {simulator.events_sent} total "
                  f"(Normal: {normal_events}, Anomalies: {simulator.anomaly_events_sent}, {anomaly_pct:.1f}%)")


def main():
    """Main function."""    
    parser = argparse.ArgumentParser(description='Manufacturing Event Simulator')
    parser.add_argument('--interval', type=float, default=5.0,
                       help='Seconds between events per asset (default: 5.0)')
    parser.add_argument('--max-runtime', type=int, default=None,
                       help='Maximum runtime in seconds (default: unlimited)')
    parser.add_argument('--assets-csv', type=str, default=None,
                       help='Path to assets.csv file')
    parser.add_argument('--products-csv', type=str, default=None,
                       help='Path to products.csv file')
    
    args = parser.parse_args()

    env_loader = AZDEnvironmentLoader(required=False, log_events=True)
    env_loader.set_env_vars()

    src_dir = Path(__file__).parent.parent
    data_dir = (src_dir / '..' / 'infra' / 'data').resolve()
    
    # Get configuration from environment variables or arguments
    event_hub_namespace_fqdn = os.getenv('AZURE_EVENT_HUB_NAMESPACE_HOSTNAME')
    event_hub_name = os.getenv('AZURE_EVENT_HUB_NAME')
    assets_csv_path = args.assets_csv or os.getenv('ASSETS_CSV_PATH', data_dir / 'assets.csv')
    products_csv_path = args.products_csv or os.getenv('PRODUCTS_CSV_PATH', data_dir / 'products.csv')
    interval = args.interval or float(os.getenv('SIMULATION_INTERVAL', '5.0'))
    max_runtime = args.max_runtime or (int(os.getenv('MAX_RUNTIME_SECONDS')) if os.getenv('MAX_RUNTIME_SECONDS') else None)

    # Validate required configuration
    if not event_hub_namespace_fqdn:
        print("❌ ERROR: AZURE_EVENT_HUB_NAMESPACE_HOSTNAME environment variable is required")
        print("Set it using: export AZURE_EVENT_HUB_NAMESPACE_HOSTNAME='your_namespace.servicebus.windows.net' or in Powershell: $env:AZURE_EVENT_HUB_NAMESPACE_HOSTNAME='your_namespace.servicebus.windows.net'")
        sys.exit(1)
    
    if not event_hub_name:
        print("❌ ERROR: AZURE_EVENT_HUB_NAME environment variable is required")
        print("Set it using: export AZURE_EVENT_HUB_NAME='your_event_hub_name' or in Powershell: $env:AZURE_EVENT_HUB_NAME='your_event_hub_name'")
        sys.exit(1)
    
    # Convert relative paths to absolute
    if not Path(assets_csv_path).is_absolute():
        assets_csv_path = (src_dir / assets_csv_path).resolve()
    if not Path(products_csv_path).is_absolute():
        products_csv_path = (src_dir / products_csv_path).resolve()
    
    print("🏭 Manufacturing Event Simulator")
    print("="*60)
    print(f"Event Hub Namespace: {event_hub_namespace_fqdn}")
    print(f"Event Hub: {event_hub_name}")
    print(f"Assets CSV: {assets_csv_path}")
    print(f"Products CSV: {products_csv_path}")
    print(f"Event Interval: {interval} seconds")
    if max_runtime:
        print(f"Max Runtime: {max_runtime} seconds")
    print("="*60)
    
    try:
        # Initialize Event Hub service
        event_hub_service = EventHubService(event_hub_namespace_fqdn, event_hub_name)
        print("✅ Event Hub service initialized")
        
        # Initialize simulator manager
        manager = EventSimulatorManager()
        
        # Load data
        assets = manager.load_assets(str(assets_csv_path))
        products = manager.load_products(str(products_csv_path))
        
        if not assets:
            print("❌ No assets found to simulate")
            sys.exit(1)
        
        # Create and start simulators
        manager.create_simulators(assets, products, event_hub_service)
        manager.start_all_simulators(interval, max_runtime)
        
    except KeyboardInterrupt:
        print("\n⚠️  Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()