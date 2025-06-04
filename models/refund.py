# models/refund.py
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .base_model import BaseModel
from .constants import REFUND_DATA_FILE

class Refund(BaseModel):
    FILE_PATH = REFUND_DATA_FILE
    PRIMARY_KEY_FIELD = 'refundID'

    def __init__(self, paymentID: str, orderID: str, ticketID: str, # camelCase params
                 refundAmount: float, refundReason: str = "User requested", # camelCase params
                 refundID: Optional[str] = None, status: str = "Pending", # camelCase params
                 requestDatetime: Optional[datetime] = None, # camelCase params
                 processedDatetime: Optional[datetime] = None): # camelCase params
        self.refundID: str = refundID or str(uuid.uuid4()) # camelCase attr
        self.paymentID: str = paymentID # camelCase attr
        self.orderID: str = orderID # camelCase attr
        self.ticketID: str = ticketID # camelCase attr
        self.refundAmount: float = float(refundAmount) # camelCase attr
        self.refundReason: str = refundReason # camelCase attr
        self.status: str = status
        
        if requestDatetime is None:
            self.requestDatetime = datetime.now(timezone.utc) # camelCase attr
        elif isinstance(requestDatetime, datetime):
             self.requestDatetime = requestDatetime if requestDatetime.tzinfo else requestDatetime.replace(tzinfo=timezone.utc)
        else:
            parsed_dt = self._parse_datetime(str(requestDatetime))
            if parsed_dt is None: raise ValueError("Could not parse requestDatetime")
            self.requestDatetime = parsed_dt

        if processedDatetime is None:
            self.processedDatetime = None # camelCase attr
        elif isinstance(processedDatetime, datetime):
            self.processedDatetime = processedDatetime if processedDatetime.tzinfo else processedDatetime.replace(tzinfo=timezone.utc)
        else:
            self.processedDatetime = self._parse_datetime(str(processedDatetime), default_now=False)

    def updateStatus(self, newStatus: str) -> None: # Method name camelCase
        self.status = newStatus
        if newStatus in ["Processed", "Failed"] and self.processedDatetime is None:
            self.processedDatetime = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'refundID': self.refundID, # Key camelCase
            'paymentID': self.paymentID, # Key camelCase
            'orderID': self.orderID, # Key camelCase
            'ticketID': self.ticketID, # Key camelCase
            'refundAmount': self.refundAmount, # Key camelCase
            'refundReason': self.refundReason, # Key camelCase
            'status': self.status,
            'requestDatetime': self.requestDatetime.isoformat(), # Key camelCase
            'processedDatetime': self.processedDatetime.isoformat() if self.processedDatetime else None # Key camelCase
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Refund']:
        # Expect camelCase keys
        if not isinstance(data, dict) or not all(k in data for k in ['paymentID', 'orderID', 'ticketID', 'refundAmount', 'refundID']):
            return None
        try:
            return cls(
                paymentID=data['paymentID'],
                orderID=data['orderID'],
                ticketID=data['ticketID'],
                refundAmount=float(data['refundAmount']),
                refundReason=data.get('refundReason', "User requested"),
                refundID=data['refundID'],
                status=data.get('status', 'Pending'),
                requestDatetime=data.get('requestDatetime'),
                processedDatetime=data.get('processedDatetime')
            )
        except (ValueError, TypeError) as e:
            print(f"Error deserializing Refund: {e}, data: {data}")
            return None