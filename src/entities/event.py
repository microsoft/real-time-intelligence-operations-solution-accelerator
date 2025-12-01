from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class Event:
    Id: str
    AssetId: str
    ProductId: str
    BatchId: str
    Vibration: Decimal
    Temperature: Decimal
    Humidity: Decimal
    Speed: Decimal
    DefectProbability: Decimal
    Timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "Id": self.Id,
            "AssetId": self.AssetId,
            "ProductId": self.ProductId,
            "Timestamp": self.Timestamp.isoformat(),
            "BatchId": self.BatchId,
            "Vibration": float(self.Vibration),
            "Temperature": float(self.Temperature),
            "Humidity": float(self.Humidity),
            "Speed": float(self.Speed),
            "DefectProbability": float(self.DefectProbability)
        }

    @staticmethod
    def get_table_schema() -> str:
        return """(
            Id: string,
            AssetId: string,
            ProductId: string,
            Timestamp: datetime,
            BatchId: string,
            Vibration: real,
            Temperature: real,
            Humidity: real,
            Speed: real,
            DefectProbability: real
        )"""


    
    