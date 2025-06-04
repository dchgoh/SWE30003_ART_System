# models/payment.py
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .base_model import BaseModel
from .constants import PAYMENT_DATA_FILE
from .json_helpers import _load_data

class Payment(BaseModel):
    FILE_PATH = PAYMENT_DATA_FILE
    PRIMARY_KEY_FIELD = 'paymentID'

    def __init__(self, orderID: str, amount: float, method: str = "MockCard",
                 status: str = "Completed", paymentID: Optional[str] = None, # camelCase params
                 paymentDatetime: Optional[datetime] = None): # camelCase params
        self.paymentID: str = paymentID or str(uuid.uuid4()) # camelCase attr
        self.orderID: str = orderID # camelCase attr
        self.amount: float = float(amount)
        self.method: str = method
        self.status: str = status
        if paymentDatetime is None:
            self.paymentDatetime = datetime.now(timezone.utc) # camelCase attr
        elif isinstance(paymentDatetime, datetime):
            self.paymentDatetime = paymentDatetime if paymentDatetime.tzinfo else paymentDatetime.replace(tzinfo=timezone.utc)
        else:
            parsed_dt = self._parse_datetime(str(paymentDatetime))
            if parsed_dt is None: raise ValueError("Could not parse paymentDatetime")
            self.paymentDatetime = parsed_dt

    def to_dict(self) -> Dict[str, Any]:
        return {
            'paymentID': self.paymentID, # Key camelCase
            'orderID': self.orderID, # Key camelCase
            'amount': self.amount,
            'method': self.method,
            'status': self.status,
            'paymentDatetime': self.paymentDatetime.isoformat() # Key camelCase
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Payment']:
        # Expect camelCase keys
        if not isinstance(data, dict) or not all(k in data for k in ['orderID', 'amount', 'paymentID']):
            return None
        try:
            return cls(
                orderID=data['orderID'],
                amount=float(data['amount']),
                method=data.get('method', "MockCard"),
                status=data.get('status', "Completed"),
                paymentID=data['paymentID'],
                paymentDatetime=data.get('paymentDatetime')
            )
        except (ValueError, TypeError) as e:
            print(f"Error deserializing Payment: {e}, data: {data}")
            return None
            
    @classmethod
    def findByOrderID(cls, orderIDToFind: str) -> Optional['Payment']: # Method name camelCase
        all_data = _load_data(cls.FILE_PATH)
        for item_data in all_data:
            if item_data.get('orderID') == orderIDToFind: # Key camelCase
                return cls.from_dict(item_data)
        return None