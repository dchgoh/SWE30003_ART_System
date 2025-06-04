# models/order.py
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base_model import BaseModel
from .constants import ORDER_DATA_FILE
from .order_line_item import OrderLineItem # Direct import for getLineItems
from .json_helpers import _load_data # For findByUserID

class Order(BaseModel):
    FILE_PATH = ORDER_DATA_FILE
    PRIMARY_KEY_FIELD = 'orderID'

    def __init__(self, userID: str, orderID: Optional[str] = None,
                 status: str = "PendingPayment", order_datetime: Optional[datetime] = None):
        self.orderID: str = orderID if orderID else str(uuid.uuid4())
        self.userID: str = userID
        if order_datetime is None:
             self.order_datetime = datetime.now(timezone.utc)
        elif isinstance(order_datetime, datetime):
             self.order_datetime = order_datetime if order_datetime.tzinfo else order_datetime.replace(tzinfo=timezone.utc)
        else: # Should be a string from from_dict
            parsed_dt = self._parse_datetime(str(order_datetime))
            if parsed_dt is None: raise ValueError("Could not parse order_datetime")
            self.order_datetime = parsed_dt
        self.status: str = status

    def getLineItems(self) -> List[OrderLineItem]:
        return OrderLineItem.findByOrderID(self.orderID)

    def calculateTotalAmount(self) -> float:
        total = 0.0
        line_items = self.getLineItems()
        for item in line_items:
            total += item.calculateLineTotal()
        return total

    def to_dict(self) -> Dict[str, Any]:
        return {
            'orderID': self.orderID,
            'userID': self.userID,
            'orderDatetime': self.order_datetime.isoformat(),
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Order']:
        if not isinstance(data, dict) or not all(k in data for k in ['userID', 'orderID']):
            return None
        
        # order_datetime parsing handled by __init__
        return cls(
            userID=data['userID'],
            status=data.get('status', 'PendingPayment'),
            orderID=data['orderID'],
            order_datetime=data.get('orderDatetime') # Pass string or None
        )

    @classmethod
    def findByUserID(cls, user_id: str) -> List['Order']:
        all_data = _load_data(cls.FILE_PATH)
        orders: List['Order'] = []
        for item_data in all_data:
            if item_data.get('userID') == user_id:
                obj = cls.from_dict(item_data)
                if obj:
                    orders.append(obj)
        return orders