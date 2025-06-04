# models/notification.py
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base_model import BaseModel
from .constants import NOTIFICATION_DATA_FILE
from .json_helpers import _load_data

class Notification(BaseModel):
    FILE_PATH = NOTIFICATION_DATA_FILE
    PRIMARY_KEY_FIELD = 'notificationID'

    def __init__(self, recipientUserID: str, senderUserID: str, messageContent: str, # camelCase params
                 notificationType: str = "General", notificationID: Optional[str] = None, # camelCase params
                 sentDatetime: Optional[datetime] = None, readStatus: bool = False): # camelCase params
        self.notificationID: str = notificationID or str(uuid.uuid4()) # camelCase attr
        self.recipientUserID: str = recipientUserID # camelCase attr
        self.senderUserID: str = senderUserID # camelCase attr
        self.messageContent: str = messageContent # camelCase attr
        self.notificationType: str = notificationType # camelCase attr
        if sentDatetime is None:
            self.sentDatetime = datetime.now(timezone.utc) # camelCase attr
        elif isinstance(sentDatetime, datetime):
            self.sentDatetime = sentDatetime if sentDatetime.tzinfo else sentDatetime.replace(tzinfo=timezone.utc)
        else:
            parsed_dt = self._parse_datetime(str(sentDatetime))
            if parsed_dt is None: raise ValueError("Could not parse sentDatetime")
            self.sentDatetime = parsed_dt
        self.readStatus: bool = readStatus # camelCase attr

    def markAsRead(self) -> None: # Method name camelCase
        self.readStatus = True
        self.save()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'notificationID': self.notificationID, # Key camelCase
            'recipientUserID': self.recipientUserID, # Key camelCase
            'senderUserID': self.senderUserID, # Key camelCase
            'messageContent': self.messageContent, # Key camelCase
            'notificationType': self.notificationType, # Key camelCase
            'sentDatetime': self.sentDatetime.isoformat(), # Key camelCase
            'readStatus': self.readStatus # Key camelCase
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Notification']:
        # Expect camelCase keys
        if not isinstance(data, dict) or not all(k in data for k in ['recipientUserID', 'messageContent']):
            return None
        
        return cls(
            recipientUserID=data['recipientUserID'],
            senderUserID=data.get('senderUserID', 'System'),
            messageContent=data['messageContent'],
            notificationType=data.get('notificationType', 'General'),
            notificationID=data.get('notificationID'),
            sentDatetime=data.get('sentDatetime'),
            readStatus=data.get('readStatus', False)
        )
    
    @classmethod
    def findByRecipientID(cls, userIDToFind: str, unreadOnly: bool = False) -> List['Notification']: # Method name camelCase
        all_data = _load_data(cls.FILE_PATH)
        items: List['Notification'] = []
        for d_item in all_data:
            if d_item.get('recipientUserID') == userIDToFind: # Key camelCase
                obj = cls.from_dict(d_item)
                if obj:
                    if unreadOnly and not obj.readStatus: # Access camelCase attribute
                        items.append(obj)
                    elif not unreadOnly:
                        items.append(obj)
        items.sort(key=lambda n: n.sentDatetime, reverse=True) # Access camelCase attribute
        return items