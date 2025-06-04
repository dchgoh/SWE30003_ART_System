# models/order_line_item.py
import uuid
from typing import Optional, Dict, Any, List
from .base_model import BaseModel
from .constants import ORDER_LINE_ITEM_DATA_FILE
from .json_helpers import _load_data

class OrderLineItem(BaseModel):
    FILE_PATH = ORDER_LINE_ITEM_DATA_FILE
    PRIMARY_KEY_FIELD = 'lineItemID'

    def __init__(self, orderID: str, itemID: str, itemType: str, # camelCase params
                 quantity: int, unitPrice: float, lineItemID: Optional[str] = None): # camelCase params
        self.lineItemID: str = lineItemID if lineItemID else str(uuid.uuid4()) # camelCase attr
        self.orderID: str = orderID # camelCase attr
        self.itemID: str = itemID # camelCase attr
        self.itemType: str = itemType # camelCase attr
        self.quantity: int = int(quantity)
        self.unitPrice: float = float(unitPrice) # camelCase attr

    def calculateLineTotal(self) -> float: # Method name camelCase
        return self.quantity * self.unitPrice

    def to_dict(self) -> Dict[str, Any]:
        return {
            'lineItemID': self.lineItemID, # Key camelCase
            'orderID': self.orderID, # Key camelCase
            'itemID': self.itemID, # Key camelCase
            'itemType': self.itemType, # Key camelCase
            'quantity': self.quantity,
            'unitPrice': self.unitPrice # Key camelCase
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['OrderLineItem']:
        # Expect camelCase keys
        if not isinstance(data, dict) or not all(k in data for k in ['orderID', 'itemID', 'itemType', 'quantity', 'unitPrice']):
            return None
        try:
            return cls(
                orderID=data['orderID'],
                itemID=data['itemID'],
                itemType=data['itemType'],
                quantity=int(data['quantity']),
                unitPrice=float(data['unitPrice']),
                lineItemID=data.get('lineItemID')
            )
        except (ValueError, TypeError) as e:
            print(f"Error deserializing OrderLineItem: {e}, data: {data}")
            return None

    @classmethod
    def findByOrderID(cls, orderIDToFind: str) -> List['OrderLineItem']: # Method name camelCase
        all_data = _load_data(cls.FILE_PATH)
        items: List['OrderLineItem'] = []
        for item_data in all_data:
            if item_data.get('orderID') == orderIDToFind: # Key is camelCase
                obj = cls.from_dict(item_data)
                if obj:
                    items.append(obj)
        return items