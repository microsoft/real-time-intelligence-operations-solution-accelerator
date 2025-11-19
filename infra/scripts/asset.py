from dataclasses import dataclass
from datetime import datetime
import random
import uuid
from event import Event

@dataclass
class Asset:
    Id: str
    SiteId: int
    Name: str
    Type: str
    SerialNumber: str
    MaintenanceStatus: str

    def to_dict(self) -> dict:
        return {
            "Id": self.Id,
            "Name": self.Name,
            "SiteId": self.SiteId,
            "Type": self.Type,
            "SerialNumber": self.SerialNumber,
            "MaintenanceStatus": self.MaintenanceStatus
        }

    @staticmethod
    def get_table_schema() -> str:
        return """(
            Id: string,
            Name: string,
            SiteId: int,
            Type: string,
            SerialNumber: string,
            MaintenanceStatus: string
        )"""
    
    @staticmethod
    def get_type_map():
        return {
            "Robotic Arm": "Assembly",
            "Automated Press": "Press",
            "Conveyor Belt": "Conveyor",
            "Packaging Line": "Packaging"
        }

@dataclass
class AssetMetric:
    Min: float
    Max: float
    Variation: float
    DefectFactor: int

    def calculate_random_value(self, anomaly: bool, variation_multiplier: float) -> float:
        value = random.uniform(self.Min, self.Max)

        if anomaly:
            anomoly_value = random.uniform(self.Variation * 0.5, self.Variation * 1.5) * variation_multiplier
            if random.choice([True, False]):
                value = self.Max + anomoly_value
            else:
                value = self.Min - anomoly_value

        return round(max(0, value), 2)
    
    def calc_defect_factor(self, value: float) -> float:
        return max(
            0, 
            (value - self.Max) / self.DefectFactor,  # Penalty for high values
            (self.Min - value) / self.DefectFactor   # Penalty for low values
        )

@dataclass
class AssetType:
    Name: str
    Vibration: AssetMetric
    Temperature: AssetMetric
    Humidity: AssetMetric
    Speed: AssetMetric

    def calculate_defect_probability(self, vibration: float, temperature: float, speed: float) -> float:
        vibration_factor = self.Vibration.calc_defect_factor(vibration)  # min(vibration / 1.0, 1.0)  # Normalize to 0-1
        temp_factor = self.Temperature.calc_defect_factor(temperature)
        speed_factor = self.Speed.calc_defect_factor(speed)
        
        defect_probability = round(
            (vibration_factor * 0.4 + temp_factor * 0.3 + speed_factor * 0.3) * 
            random.uniform(0.8, 1.2), # Add some randomness
            2  
        )
        return min(defect_probability, 1.0) # cap at 100%

    def create_random_event(self, asset_id: str, product_id: str, batch_id: str, timestamp: datetime, anomaly: bool, variation_multiplier: float = 1) -> 'Event':
        anomaly_metrics = []
        if anomaly:
            # Randomly select which metrics to create anomalies for
            if random.choice([True, False]):
                anomaly_metrics.append('vibration')
            if random.choice([True, False]):
                anomaly_metrics.append('temperature')
            if random.choice([True, False]):
                anomaly_metrics.append('humidity')
            if random.choice([True, False]):
                anomaly_metrics.append('speed')

            # Ensure at least one metric has an anomaly
            if not anomaly_metrics:
                anomaly_metrics.append(random.choice(['vibration', 'temperature', 'humidity', 'speed']))

        vibration = self.Vibration.calculate_random_value(
            anomaly=anomaly and 'vibration' in anomaly_metrics, 
            variation_multiplier=variation_multiplier)
        
        temperature = self.Temperature.calculate_random_value(
            anomaly=anomaly and 'temperature' in anomaly_metrics, 
            variation_multiplier=variation_multiplier)
        
        humidity = self.Humidity.calculate_random_value(
            anomaly=anomaly and 'humidity' in anomaly_metrics, 
            variation_multiplier=variation_multiplier)
        
        speed = self.Speed.calculate_random_value(
            anomaly=anomaly and 'speed' in anomaly_metrics, 
            variation_multiplier=variation_multiplier)

        defect_probability = self.calculate_defect_probability(vibration, temperature, speed)

        return Event(
            Id=str(uuid.uuid4()),
            AssetId=asset_id,
            ProductId=product_id,
            BatchId=batch_id,
            Vibration=vibration,
            Temperature=temperature,
            Humidity=humidity,
            Speed=speed,
            DefectProbability=defect_probability,
            Timestamp=timestamp
        )
   
    @staticmethod
    def get_types() -> dict[str, 'AssetType']:
        return {
            "Assembly": AssetType(
                Name="Assembly",
                Vibration=AssetMetric(Min=0.1, Max=0.3, Variation=0.08, DefectFactor=0.5),
                Temperature=AssetMetric(Min=20, Max=35, Variation=3, DefectFactor=12),
                Humidity=AssetMetric(Min=30, Max=70, Variation=0, DefectFactor=15),
                Speed=AssetMetric(Min=50, Max=100, Variation=20, DefectFactor=20),
            ),
            "Press": AssetType(
                Name="Press",
                Vibration=AssetMetric(Min=0.2, Max=0.8, Variation=0.08, DefectFactor=0.5),
                Temperature=AssetMetric(Min=25, Max=45, Variation=5, DefectFactor=15),
                Humidity=AssetMetric(Min=30, Max=70, Variation=0, DefectFactor=15),
                Speed=AssetMetric(Min=20, Max=60, Variation=10, DefectFactor=20)
            ),
            "Conveyor": AssetType(
                Name="Conveyor",
                Vibration=AssetMetric(Min=0.05, Max=0.2, Variation=0.08, DefectFactor=0.5),
                Temperature=AssetMetric(Min=18, Max=30, Variation=2, DefectFactor=10),
                Humidity=AssetMetric(Min=30, Max=70, Variation=0, DefectFactor=15),
                Speed=AssetMetric(Min=10, Max=50, Variation=8, DefectFactor=20)
            ),
            "Packaging": AssetType(
                Name="Packaging",
                Vibration=AssetMetric(Min=0.1, Max=0.4, Variation=0.08, DefectFactor=0.5),
                Temperature=AssetMetric(Min=20, Max=40, Variation=3, DefectFactor=12),
                Humidity=AssetMetric(Min=30, Max=70, Variation=0, DefectFactor=15),
                Speed=AssetMetric(Min=30, Max=80, Variation=15, DefectFactor=20)
            )
        }

    