import random
import uuid
from datetime import datetime, timedelta, timezone
import pandas as pd
import os
from event import Event
from asset import Asset, AssetType

def generate_locations():
    city_country_map = {
        "Ho Chi Minh City": "Vietnam"
    }

    locations = []
    for city, country in city_country_map.items():
        location_id = len(locations) + 1
        # Note: see fabric_database.py for schema
        locations.append({
            "Id": location_id,
            "City": city,
            "Country": country
        })

    return pd.DataFrame(locations)

def generate_sites(num, locations_df: pd.DataFrame):
    locations_list = locations_df.to_dict('records')
    sites = []
    
    for i in range(num):
        id = i
        # Note: see fabric_database.py for schema
        sites.append({
            "Id": id,
            "Name": f"Site {id}",
            "LocationId":  random.choice(locations_list)["Id"],
            "PlantType": random.choice(["Assembly", "Supplier", "Warehouse"])
        })
    
    return pd.DataFrame(sites)

def generate_assets(num_assets_per_site: int, sites_df: pd.DataFrame):
    asset_name_type_map = Asset.get_type_map()
    asset_names = list(asset_name_type_map.keys())
    assets: list[Asset] = []
    sites_list = sites_df.to_dict('records')
    
    name_counter = {}
    
    for site_index, site in enumerate(sites_list):
        for i in range(num_assets_per_site):
            # reset list if empty - to ensure all asset types are represented
            if len(asset_names) == 0:
                asset_names = list(asset_name_type_map.keys())

            name = random.choice(asset_names)

            # remove name from list to ensure all assets can be represented
            asset_names.remove(name)

            type = asset_name_type_map[name]
            name_counter[name] = name_counter.get(name, 0) + 1

            # Note: see fabric_database.py for schema
            assets.append(Asset(Id=f"A_{1000 + site_index * num_assets_per_site + i}",
                Name=f"{name} {name_counter[name]}",
                SiteId=site.get('Id'),
                Type=type,
                SerialNumber=str(uuid.uuid4()),
                MaintenanceStatus=random.choice(["Done", "Pending", "Scheduled"])
            ))
    
    assets_data = [asset.to_dict() for asset in assets]
    
    return pd.DataFrame(assets_data)

def generate_products(num):
    category_id_map = { 
        "Camping Tables": 1,
        "Camping Stoves": 2
    }

    product_name_type_map = {
        "BaseCamp Folding Table": "Camping Tables",
        "EcoFire Camping Stove": "Camping Stoves",
        "TrekMaster Camping Chair": "Camping Tables",
        "PowerBurner Camping Stove": "Camping Stoves",
        "Adventure Dining Table": "Camping Tables",
        "CompactCook Camping Stove": "Camping Stoves"
    }
    names = list(product_name_type_map.keys())
    products = []
    
    for i in range(num):
        name = random.choice(names)
        category_name = product_name_type_map[name]
        list_price = round(random.uniform(50, 100), 2)
        unit_cost = round((list_price / 2) + random.uniform(1, (list_price / 4)), 2)

        # Note: see fabric_database.py for schema
        products.append({
            "Id": f"P_{1000+i}",
            "CategoryId": category_id_map[category_name],
            "CategoryName": category_name,
            "Name": name,
            "Description": name,
            "BrandName": random.choice(["Contoso Outdoors"]),
            "Number": str(uuid.uuid4()),
            "Status":  random.choice(["Active"]),
            "Color": random.choice(["Red", "Blue", "Green", "Yellow"]),
            "ListPrice": list_price,
            "UnitCost": unit_cost,
            "IsoCurrencyCode": "USD"
        })
    
    return pd.DataFrame(products)

def generate_historical_events(
    assets_df: pd.DataFrame, 
    products_df: pd.DataFrame,
    asset_event_anomaly_rates: list[float],
    start_date: datetime, 
    days_back: int,
    mins_between_events: int
):
    if start_date is None:
        start_date = datetime.now(timezone.utc)
    
    # Validate days_back parameter
    if days_back > 90:
        print(f"Warning: days_back ({days_back}) exceeds maximum of 90 days. Setting to 90.")
        days_back = 90
    
    # Calculate end date (going back in time)
    end_date = start_date - timedelta(days=days_back)
    
    # Get lists of available assets and products
    assets_list = assets_df.to_dict('records')
    products_list = products_df.to_dict('records')
    
    events: list[Event] = []

    # Generate batch IDs (one batch per hour approximately)
    current_time = end_date
    batch_counter = 1
    current_batch_id = f"BATCH_{batch_counter:06d}"
    next_batch_time = current_time + timedelta(hours=1)
    asset_types = AssetType.get_types()
    
    print(f"Generating historical events from {end_date.strftime('%Y-%m-%d %H:%M')} to {start_date.strftime('%Y-%m-%d %H:%M')}...")
    
    # Generate one event per minute
    while current_time <= start_date:
        if current_time >= next_batch_time:
            batch_counter += 1
            current_batch_id = f"BATCH_{batch_counter:06d}"
            next_batch_time = current_time + timedelta(hours=1)
        
        for index, asset in enumerate(assets_list):
            product = random.choice(products_list)

            asset_type = asset_types[asset.get("Type")]
            anomaly_rate = asset_event_anomaly_rates[index % len(asset_event_anomaly_rates)]
            event = asset_type.create_random_event(asset_id=asset["Id"], 
                               product_id=product["Id"],
                               batch_id=current_batch_id,
                               timestamp=current_time,
                               anomaly=random.random() < anomaly_rate)

            events.append(event)

        current_time += timedelta(minutes=mins_between_events)

    print(f"✅ Generated {len(events)} historical events across {len(assets_list)} assets ({days_back} days of data)")

    events_data = [event.to_dict() for event in events]
    return pd.DataFrame(events_data)

def generate_sample_data(
    num_sites: int,
    num_assets_per_site: int,
    num_products: int,
    random_seed: int,
    override_existing: bool,
    include_events: bool,
    asset_event_anomaly_rates: list[float],
    event_start_date: datetime,
    event_days_back: int,
    mins_between_events: int

):
    random.seed(random_seed)
    
    try:
        # Set path as a relative directory in the current script directory
        path = "../data"
        
        print(f"Generating sample data...")
        print(f"Output directory: {os.path.abspath(path)}")

        os.makedirs(path, exist_ok=True)

        csv_files = {
            "locations": os.path.join(path, "locations.csv"),
            "sites": os.path.join(path, "sites.csv"),
            "assets": os.path.join(path, "assets.csv"),
            "products": os.path.join(path, "products.csv")
        }
        
        if include_events:
            csv_files["events"] = os.path.join(path, "events.csv")
        
        if not override_existing:
            existing_files = [name for name, path in csv_files.items() if os.path.exists(path)]
            if existing_files:
                raise FileExistsError(
                    f"CSV file(s) already exist: {', '.join(existing_files)}. "
                    f"Set override_existing=True to overwrite or remove existing files."
                )
        
        print(f"Generating {num_sites} sites, {num_assets_per_site} assets per site, {num_products} products...")
        locations_df = generate_locations()
        sites_df = generate_sites(num_sites, locations_df)
        assets_df = generate_assets(num_assets_per_site, sites_df)
        products_df = generate_products(num_products)
        
        events_df = None
        if include_events:
            print(f"Generating historical events for {event_days_back} days...")
            events_df = generate_historical_events(
                assets_df, 
                products_df,
                asset_event_anomaly_rates, 
                event_start_date, 
                event_days_back,
                mins_between_events
            )
        
        print(f"Saving CSV files...")
        locations_df.to_csv(csv_files["locations"], index=False)
        sites_df.to_csv(csv_files["sites"], index=False)
        assets_df.to_csv(csv_files["assets"], index=False)
        products_df.to_csv(csv_files["products"], index=False)
        
        if include_events and events_df is not None:
            events_df.to_csv(csv_files["events"], index=False)

        print(f"✅ Sample data generated successfully!")
        
        result = {
            "locations_df": locations_df,
            "sites_df": sites_df,
            "assets_df": assets_df,
            "products_df": products_df
        }
        
        if include_events and events_df is not None:
            result["events_df"] = events_df
            
        return result
    
    except FileExistsError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

if __name__ == "__main__":    
    result = generate_sample_data(
        num_sites=2,
        num_assets_per_site=1,
        num_products=20,
        random_seed=36,
        override_existing=True,
        include_events=True,
        asset_event_anomaly_rates=[0.02, 0.06],
        event_start_date=datetime.now(timezone.utc),
        event_days_back=90,
        mins_between_events=1
    )