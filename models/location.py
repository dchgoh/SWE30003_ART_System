# models/location.py
import uuid
from typing import Optional, Dict, Any
from .base_model import BaseModel
from .constants import LOCATION_DATA_FILE

class Location(BaseModel):
    FILE_PATH = LOCATION_DATA_FILE
    PRIMARY_KEY_FIELD = 'locationID'

    def __init__(self, latitude: float, longitude: float, addressLine1: str, # camelCase params
                 city: str, postcode: str, locationID: Optional[str] = None): # camelCase params
        self.locationID: str = locationID or str(uuid.uuid4()) # camelCase attr
        self.latitude: float = float(latitude)
        self.longitude: float = float(longitude)
        self.addressLine1: str = addressLine1 # camelCase attr
        self.city: str = city
        self.postcode: str = str(postcode)

    def setDetails(self, latitude: Optional[float] = None, longitude: Optional[float] = None, # Method name camelCase
                    addressLine1: Optional[str] = None, city: Optional[str] = None, # camelCase params
                    postcode: Optional[str] = None) -> bool:
        if latitude is not None: self.latitude = float(latitude)
        if longitude is not None: self.longitude = float(longitude)
        if addressLine1 is not None: self.addressLine1 = addressLine1
        if city is not None: self.city = city
        if postcode is not None: self.postcode = str(postcode)
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'locationID': self.locationID, # Key camelCase
            'latitude': self.latitude,
            'longitude': self.longitude,
            'addressLine1': self.addressLine1, # Key camelCase
            'city': self.city,
            'postcode': self.postcode
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Location']:
        # Expect camelCase keys (addressLine1)
        if not isinstance(data, dict) or not all(k in data for k in ['latitude', 'longitude', 'addressLine1', 'city', 'postcode']):
            return None
        try:
            return cls(
                latitude=float(data['latitude']),
                longitude=float(data['longitude']),
                addressLine1=data['addressLine1'],
                city=data['city'],
                postcode=data['postcode'],
                locationID=data.get('locationID')
            )
        except (ValueError, TypeError) as e:
            print(f"Error deserializing Location: {e}, data: {data}")
            return None