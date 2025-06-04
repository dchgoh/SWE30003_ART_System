# models/admin.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from .user import User

class Admin(User):
    def __init__(self, username: str, email: str, password: Optional[str],
                 userID: Optional[str] = None, phone: Optional[str] = None,
                 firstName: Optional[str] = None, lastName: Optional[str] = None, # camelCase params
                 dateRegistered: Optional[datetime] = None, accountStatus: str = "Active", # camelCase params
                 adminLevel: str = "staff", # camelCase param
                 permissions: Optional[List[str]] = None,
                 assignedArea: Optional[str] = None):
        super().__init__(username, email, password, userID, phone, firstName, lastName,
                         dateRegistered, accountStatus, isAdmin=True)
        self.adminLevel: str = adminLevel # camelCase attr
        self.permissions: List[str] = permissions or []
        self.assignedArea: Optional[str] = assignedArea

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'adminLevel': self.adminLevel, # Key camelCase
            'permissions': self.permissions,
            'assignedArea': self.assignedArea
        })
        return data