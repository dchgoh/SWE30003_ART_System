# models/route.py
import uuid
from typing import Optional, List, Dict, Any
from .base_model import BaseModel
from .constants import ROUTE_DATA_FILE
from .stop import Stop

class Route(BaseModel):
    FILE_PATH = ROUTE_DATA_FILE
    PRIMARY_KEY_FIELD = 'routeID'

    def __init__(self, routeName: str, description: str, # camelCase params
                 routeID: Optional[str] = None, stopIDs: Optional[List[str]] = None): # camelCase params
        self.routeID: str = routeID if routeID else str(uuid.uuid4()) # camelCase attr
        self.routeName: str = routeName # camelCase attr
        self.description: str = description
        self.stopIDs: List[str] = stopIDs if stopIDs is not None else [] # camelCase attr

    def addStopID(self, stopID: str) -> bool: # Method name camelCase
        if stopID not in self.stopIDs:
            self.stopIDs.append(stopID)
            return True
        return False
    
    def removeStopID(self, stopID: str) -> bool: # Method name camelCase
        if stopID in self.stopIDs:
            self.stopIDs.remove(stopID)
            return True
        return False

    def findStopID(self, stopIDToFind: str) -> Optional[str]: # Method name camelCase
        return stopIDToFind if stopIDToFind in self.stopIDs else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'routeID': self.routeID, # Key camelCase
            'routeName': self.routeName, # Key camelCase
            'description': self.description,
            'stopIDs': self.stopIDs # Key camelCase
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Route']:
        # Expect camelCase keys
        if not isinstance(data, dict) or not data.get('routeName') or not data.get('routeID'):
            return None
        return cls(
            routeName=data['routeName'],
            description=data.get('description', ''),
            routeID=data['routeID'],
            stopIDs=data.get('stopIDs', [])
        )

    def getStopsObjects(self) -> List[Stop]: # Method name camelCase
        stops: List[Stop] = []
        for stop_id_val in self.stopIDs: # Renamed to avoid conflict
            stop_obj = Stop.findByID(stop_id_val) # Stop.findByID should be correct
            if stop_obj:
                stops.append(stop_obj)
        return stops