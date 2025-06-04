# models/trip.py
from datetime import datetime, timezone
from typing import Union, Optional, List, Dict, Any
from .base_model import BaseModel
from .constants import TRIP_DATA_FILE

class Trip(BaseModel):
    FILE_PATH = TRIP_DATA_FILE
    PRIMARY_KEY_FIELD = 'tripID' # This is the key in the JSON, often matches attribute

    def __init__(self, tripID: str, origin: str, destination: str,
                 departureTime: Union[str, datetime], price: float, availableSeats: int): # Parameters to camelCase
        self.tripID: str = tripID
        self.origin: str = origin
        self.destination: str = destination

        if isinstance(departureTime, str):
            parsed_dt = self._parse_datetime(departureTime)
            if parsed_dt is None:
                 raise ValueError(f"Could not parse departureTime string: {departureTime}")
            self.departureTime: datetime = parsed_dt
        elif isinstance(departureTime, datetime):
            if departureTime.tzinfo is None or departureTime.tzinfo.utcoffset(departureTime) is None:
                self.departureTime = departureTime.replace(tzinfo=timezone.utc)
            else:
                self.departureTime = departureTime
        else:
            raise TypeError("departureTime must be a string or datetime object")

        self.price: float = float(price) # price was likely already lowercase
        self.availableSeats: int = int(availableSeats) # Attribute to camelCase

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tripID': self.tripID,
            'origin': self.origin,
            'destination': self.destination,
            'departureTime': self.departureTime.isoformat(), # Key is camelCase
            'price': self.price,
            'availableSeats': self.availableSeats # Key is camelCase
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Trip']:
        # Ensure keys being accessed match the JSON data (which should be camelCase)
        if not isinstance(data, dict) or not all(k in data for k in ['tripID', 'origin', 'destination', 'departureTime', 'price', 'availableSeats']):
            return None
        try:
            return cls(
                tripID=data['tripID'],
                origin=data['origin'],
                destination=data['destination'],
                departureTime=data['departureTime'], # Expect camelCase key
                price=float(data['price']),
                availableSeats=int(data['availableSeats']) # Expect camelCase key
            )
        except (ValueError, TypeError) as e:
            print(f"Error deserializing Trip: {e}, data: {data}")
            return None

    @classmethod
    def search(cls, origin: Optional[str] = None, destination: Optional[str] = None, date_str: Optional[str] = None) -> List['Trip']:
        all_trips = cls.getAll()
        filtered_trips: List['Trip'] = []

        target_date: Optional[datetime.date] = None
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"Warning: Invalid date format for trip search '{date_str}'. Expected YYYY-MM-DD.")

        for trip in all_trips:
            match = True
            if origin and origin.lower() not in trip.origin.lower():
                match = False
            if destination and destination.lower() not in trip.destination.lower():
                match = False
            # Accessing the camelCase attribute on the trip object
            if target_date and trip.departureTime.date() != target_date:
                match = False

            # Accessing the camelCase attribute on the trip object
            if match and trip.availableSeats > 0:
                filtered_trips.append(trip)
        return filtered_trips

    def updateSeats(self, numSeats: int, operation: str = "book") -> bool: # Method name kept as camelCase
        numSeats = int(numSeats)
        if operation == "book":
            if self.availableSeats >= numSeats: # Access camelCase attribute
                self.availableSeats -= numSeats
                return True
            return False
        elif operation == "refund":
            self.availableSeats += numSeats # Access camelCase attribute
            return True
        print(f"Warning: Unknown operation '{operation}' in Trip.updateSeats.")
        return False