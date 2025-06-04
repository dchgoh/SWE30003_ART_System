# models/user.py
import uuid
from datetime import datetime, timezone
import hashlib
from typing import List, Dict, Any, Optional, TypeVar, Type
from .constants import USER_DATA_FILE
from .json_helpers import _load_data, _save_data
import models # For polymorphic instantiation in from_dict

U = TypeVar('U', bound='User')

class User:
    FILE_PATH = USER_DATA_FILE

    def __init__(self, username: str, email: str, password: Optional[str],
                 userID: Optional[str] = None,
                 phone: Optional[str] = None, firstName: Optional[str] = None, # camelCase params
                 lastName: Optional[str] = None, # camelCase params
                 dateRegistered: Optional[datetime] = None, # camelCase params
                 accountStatus: str = "Active", # camelCase params
                 isAdmin: bool = False): # camelCase params
        self.userID: str = userID if userID else str(uuid.uuid4())
        self.username: str = username # username is fine as lowercase
        self.email: str = email # email is fine as lowercase
        self.passwordHash: Optional[str] = self._hash_password(password) if password else None # camelCase attr
        self.isAdmin: bool = isAdmin # camelCase attr
        self.phone: Optional[str] = phone
        self.firstName: Optional[str] = firstName # camelCase attr
        self.lastName: Optional[str] = lastName # camelCase attr
        self.dateRegistered: datetime = dateRegistered if dateRegistered else datetime.now(timezone.utc) # camelCase attr
        self.accountStatus: str = accountStatus # camelCase attr

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def checkPassword(self, passwordToCheck: str) -> bool: # Method name camelCase
        if not self.passwordHash or not passwordToCheck:
            return False
        return self.passwordHash == self._hash_password(passwordToCheck)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'userID': self.userID,
            'username': self.username,
            'email': self.email,
            'passwordHash': self.passwordHash, # Key camelCase
            'isAdmin': self.isAdmin, # Key camelCase
            'phone': self.phone,
            'firstName': self.firstName, # Key camelCase
            'lastName': self.lastName, # Key camelCase
            'dateRegistered': self.dateRegistered.isoformat(), # Key camelCase
            'accountStatus': self.accountStatus, # Key camelCase
            '_userType': self.__class__.__name__
        }
        return data

    @classmethod
    def _parse_user_datetime(cls, date_str: Optional[str]) -> datetime:
        if date_str:
            try:
                if date_str.endswith('Z'):
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(date_str)
                if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            except (TypeError, ValueError):
                print(f"Warning (User): Could not parse date string '{date_str}'. Defaulting to current UTC time.")
        return datetime.now(timezone.utc)

    @classmethod
    def from_dict(cls: Type[U], data: Dict[str, Any]) -> Optional[U]:
        if not isinstance(data, dict): return None

        user_type = data.get('_userType')
        userID = data.get('userID') # Expect camelCase keys
        username = data.get('username')
        email = data.get('email')
        passwordHashFromData = data.get('passwordHash') # Expect camelCase key
        phone = data.get('phone')
        firstName = data.get('firstName') # Expect camelCase key
        lastName = data.get('lastName') # Expect camelCase key
        dateRegisteredStr = data.get('dateRegistered') # Expect camelCase key
        accountStatus = data.get('accountStatus', "Active") # Expect camelCase key
        isAdminFlag = data.get('isAdmin', False) # Expect camelCase key

        if not all([userID, username, email, passwordHashFromData]):
            return None

        dateRegistered = cls._parse_user_datetime(dateRegisteredStr)

        instance: Optional[User] = None

        if user_type == "Admin":
            instance = models.Admin(username=username, email=email, password=None,
                                    userID=userID, phone=phone, firstName=firstName, lastName=lastName,
                                    dateRegistered=dateRegistered, accountStatus=accountStatus,
                                    adminLevel=data.get('adminLevel', 'staff'), # Expect camelCase key
                                    permissions=data.get('permissions'), assignedArea=data.get('assignedArea'))
        elif user_type == "ArtPassenger":
            instance = models.ArtPassenger(username=username, email=email, password=None,
                                           userID=userID, phone=phone, firstName=firstName, lastName=lastName,
                                           dateRegistered=dateRegistered, accountStatus=accountStatus,
                                           paymentMethods=data.get('paymentMethods'), # Expect camelCase key
                                           bookingHistory=data.get('bookingHistory'), # Expect camelCase key
                                           preferences=data.get('preferences'),
                                           loyaltyPoints=data.get('loyaltyPoints', 0)) # Expect camelCase key
        elif user_type == "User" or user_type is None:
            instance = cls(username=username, email=email, password=None,
                           userID=userID, phone=phone, firstName=firstName, lastName=lastName,
                           dateRegistered=dateRegistered, accountStatus=accountStatus,
                           isAdmin=isAdminFlag)
        else:
            print(f"Warning: Unknown user type '{user_type}' encountered during deserialization.")
            return None

        if instance:
            instance.passwordHash = passwordHashFromData # Set camelCase attribute
        return instance # type: ignore

    def save(self) -> bool: # Method name kept as lowercase (common for save)
        all_data = _load_data(self.FILE_PATH)
        user_dict = self.to_dict()
        found_existing = False

        for i, d in enumerate(all_data):
            if d.get('userID') == self.userID:
                for other_d in all_data:
                    if other_d.get('userID') != self.userID:
                        if other_d.get('username') == self.username:
                            print(f"Update failed: Username '{self.username}' is already taken.")
                            return False
                        if other_d.get('email') == self.email:
                            print(f"Update failed: Email '{self.email}' is already taken.")
                            return False
                all_data[i] = user_dict
                found_existing = True
                break
        
        if not found_existing:
            for d in all_data:
                if d.get('username') == self.username:
                    print(f"Save failed: Username '{self.username}' already exists.")
                    return False
                if d.get('email') == self.email:
                    print(f"Save failed: Email '{self.email}' already exists.")
                    return False
            all_data.append(user_dict)

        _save_data(self.FILE_PATH, all_data)
        return True

    @classmethod
    def findByID(cls: Type[U], userIDToFind: str) -> Optional[U]: # Method name camelCase
        all_data = _load_data(cls.FILE_PATH)
        for d in all_data:
            if d.get('userID') == userIDToFind: # Key is camelCase
                return cls.from_dict(d)
        return None

    @classmethod
    def findByUsername(cls: Type[U], usernameToFind: str) -> Optional[U]: # Method name camelCase
        all_data = _load_data(cls.FILE_PATH)
        for d in all_data:
            if d.get('username') == usernameToFind:
                return cls.from_dict(d)
        return None

    @classmethod
    def getAll(cls: Type[U]) -> List[U]: # Method name camelCase
        all_data = _load_data(cls.FILE_PATH)
        items: List[U] = []
        for d in all_data:
            if cls.__name__ == "User" or d.get('_userType') == cls.__name__:
                obj = cls.from_dict(d)
                if obj:
                    items.append(obj)
        return items