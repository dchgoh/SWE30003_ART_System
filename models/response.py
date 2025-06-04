# models/response.py
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base_model import BaseModel
from .constants import RESPONSE_DATA_FILE
from .json_helpers import _load_data # For find_by_feedback_id

class Response(BaseModel):
    FILE_PATH = RESPONSE_DATA_FILE
    PRIMARY_KEY_FIELD = 'responseID'

    def __init__(self, feedbackID: str, responderAdminID: str, responseContent: str,
        responseID: Optional[str] = None, responseDatetime: Optional[datetime] = None):
        self.responseID: str = responseID or str(uuid.uuid4())
        self.feedbackID: str = feedbackID
        self.responderAdminID: str = responderAdminID
        self.responseContent: str = responseContent
        if responseDatetime is None:
            self.responseDatetime = datetime.now(timezone.utc)
        elif isinstance(responseDatetime, datetime):
            self.responseDatetime = responseDatetime if responseDatetime.tzinfo else responseDatetime.replace(tzinfo=timezone.utc)
        else: # Should be a string from from_dict
            parsed_dt = self._parse_datetime(str(responseDatetime))
            if parsed_dt is None: raise ValueError("Could not parse responseDatetime")
            self.responseDatetime = parsed_dt

    def to_dict(self) -> Dict[str, Any]:
        return {
            'responseID': self.responseID,
            'feedbackID': self.feedbackID,
            'responderAdminID': self.responderAdminID,
            'responseContent': self.responseContent,
            'responseDatetime': self.responseDatetime.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Response']:
        if not isinstance(data, dict) or not all(k in data for k in ['feedbackID', 'responderAdminID', 'responseContent']):
            return None
        
        # responseDatetime parsing handled by __init__
        return cls(
            feedbackID=data['feedbackID'],
            responderAdminID=data['responderAdminID'],
            responseContent=data['responseContent'],
            responseID=data.get('responseID'),
            responseDatetime=data.get('responseDatetime') # Pass string or None
        )

    @classmethod
    def find_by_feedback_id(cls, feedback_id_to_find: str) -> List['Response']:
        all_data = _load_data(cls.FILE_PATH)
        items: List['Response'] = []
        for d_item in all_data:
            if d_item.get('feedbackID') == feedback_id_to_find:
                obj = cls.from_dict(d_item)
                if obj:
                    items.append(obj)
        return items