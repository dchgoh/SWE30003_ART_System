# models/ticket.py
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base_model import BaseModel
from .constants import TICKET_DATA_FILE
from .json_helpers import _load_data, _save_data

class Ticket(BaseModel):
    FILE_PATH = TICKET_DATA_FILE
    PRIMARY_KEY_FIELD = 'ticketID'

    def __init__(self, userID: str, tripID: str, orderID: str, paymentID: str, # camelCase params
                 seatNumber: Optional[str] = None, issueDatetime: Optional[datetime] = None, # camelCase params
                 ticketID: Optional[str] = None, status: str = "Active"): # camelCase params
        self.ticketID: str = ticketID or str(uuid.uuid4()) # camelCase attr
        self.userID: str = userID # camelCase attr
        self.tripID: str = tripID # camelCase attr
        self.orderID: str = orderID # camelCase attr
        self.paymentID: str = paymentID # camelCase attr
        self.seatNumber: str = seatNumber or "Any Available" # camelCase attr
        if issueDatetime is None:
            self.issueDatetime = datetime.now(timezone.utc) # camelCase attr
        elif isinstance(issueDatetime, datetime):
            self.issueDatetime = issueDatetime if issueDatetime.tzinfo else issueDatetime.replace(tzinfo=timezone.utc)
        else:
            parsed_dt = self._parse_datetime(str(issueDatetime))
            if parsed_dt is None: raise ValueError("Could not parse issueDatetime")
            self.issueDatetime = parsed_dt
        self.status: str = status

    def void(self) -> bool: # Method name lowercase (as per original)
        if self.status == "Active":
            self.status = "Voided"
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticketID': self.ticketID, # Key camelCase
            'userID': self.userID, # Key camelCase
            'tripID': self.tripID, # Key camelCase
            'orderID': self.orderID, # Key camelCase
            'paymentID': self.paymentID, # Key camelCase
            'seatNumber': self.seatNumber, # Key camelCase
            'issueDatetime': self.issueDatetime.isoformat(), # Key camelCase
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Ticket']:
        # Expect camelCase keys
        if not isinstance(data, dict) or not all(k in data for k in ['userID', 'tripID', 'orderID', 'paymentID', 'ticketID']):
            return None
        
        return cls(
            userID=data['userID'],
            tripID=data['tripID'],
            orderID=data['orderID'],
            paymentID=data['paymentID'],
            seatNumber=data.get('seatNumber'),
            ticketID=data['ticketID'],
            status=data.get('status', "Active"),
            issueDatetime=data.get('issueDatetime')
        )

    @classmethod
    def findByOrderID(cls, orderIDToFind: str) -> List['Ticket']: # Method name camelCase
        all_data = _load_data(cls.FILE_PATH)
        items: List['Ticket'] = []
        for item_data in all_data:
            if item_data.get('orderID') == orderIDToFind: # Key camelCase
                obj = cls.from_dict(item_data)
                if obj:
                    items.append(obj)
        return items

    @classmethod
    def deleteByOrderID(cls, orderIDToDelete: str) -> bool: # Method name camelCase
        all_data = _load_data(cls.FILE_PATH)
        initial_count = len(all_data)
        remaining_items = [d for d in all_data if d.get('orderID') != orderIDToDelete] # Key camelCase
        
        if len(remaining_items) < initial_count:
            _save_data(cls.FILE_PATH, remaining_items)
            return True
        return False