# models/stop.py
import uuid
from typing import Optional, Dict, Any
from .base_model import BaseModel
from .constants import STOP_DATA_FILE
from .location import Location

class Stop(BaseModel):
    FILE_PATH = STOP_DATA_FILE
    PRIMARY_KEY_FIELD = 'stopID'

    def __init__(self, stopName: str, locationID: str, # camelCase params
                 stopID: Optional[str] = None, stopCode: Optional[str] = None): # camelCase params
        self.stopID: str = stopID if stopID else str(uuid.uuid4()) # camelCase attr
        self.stopName: str = stopName # camelCase attr
        self.locationID: str = locationID # camelCase attr
        self.stopCode: str = stopCode if stopCode else self.stopID[:6].upper() # camelCase attr

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stopID': self.stopID, # Key camelCase
            'stopName': self.stopName, # Key camelCase
            'locationID': self.locationID, # Key camelCase
            'stopCode': self.stopCode # Key camelCase
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Stop']:
        # Expect camelCase keys
        if not isinstance(data, dict) or not all(k in data for k in ['stopName', 'locationID']):
            return None
        return cls(
            stopName=data['stopName'],
            locationID=data['locationID'],
            stopID=data.get('stopID'),
            stopCode=data.get('stopCode')
        )

    def getLocation(self) -> Optional[Location]: # Method name camelCase
        return Location.findByID(self.locationID) # Uses findByID from Location

    def updateLocationDetails(self, newLatitude: float, newLongitude: float, # Method name camelCase
                                newAddressLine1: str, newCity: str, newPostcode: str) -> tuple[bool, str]: # camelCase params
        location = self.getLocation()
        if location:
            location.setDetails(newLatitude, newLongitude, newAddressLine1, newCity, newPostcode) # Calls camelCase method
            location.save()
            return True, "Location details updated successfully."
        return False, f"Location with ID {self.locationID} not found for this stop."