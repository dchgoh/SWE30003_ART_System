# models/art_passenger.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from .user import User

class ArtPassenger(User):
    def __init__(self, username: str, email: str, password: Optional[str],
                 userID: Optional[str] = None, phone: Optional[str] = None,
                 firstName: Optional[str] = None, lastName: Optional[str] = None, # camelCase params
                 dateRegistered: Optional[datetime] = None, accountStatus: str = "Active", # camelCase params
                 paymentMethods: Optional[List[Any]] = None, # camelCase param
                 bookingHistory: Optional[List[Any]] = None, # camelCase param
                 preferences: Optional[Dict[str, Any]] = None,
                 loyaltyPoints: int = 0): # camelCase param
        super().__init__(username, email, password, userID, phone, firstName, lastName,
                         dateRegistered, accountStatus, isAdmin=False)
        self.paymentMethods: List[Any] = paymentMethods or [] # camelCase attr
        self.bookingHistory: List[Any] = bookingHistory or [] # camelCase attr
        self.preferences: Dict[str, Any] = preferences or {}
        self.loyaltyPoints: int = int(loyaltyPoints) # camelCase attr

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'paymentMethods': self.paymentMethods, # Key camelCase
            'bookingHistory': self.bookingHistory, # Key camelCase
            'preferences': self.preferences,
            'loyaltyPoints': self.loyaltyPoints # Key camelCase
        })
        return data