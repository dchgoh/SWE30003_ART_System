# models/feedback.py
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .base_model import BaseModel
from .constants import FEEDBACK_DATA_FILE

class Feedback(BaseModel):
    FILE_PATH = FEEDBACK_DATA_FILE
    PRIMARY_KEY_FIELD = 'feedbackID'

    def __init__(self, submitterUserID: str, feedbackContent: str, # camelCase params
                 rating: Optional[int] = None, relatedTripID: Optional[str] = None, # camelCase params
                 feedbackID: Optional[str] = None, status: str = "New", # camelCase params
                 submissionDatetime: Optional[datetime] = None, # camelCase params
                 responseIDs: Optional[List[str]] = None): # camelCase params
        self.feedbackID: str = feedbackID or str(uuid.uuid4()) # camelCase attr
        self.submitterUserID: str = submitterUserID # camelCase attr
        self.feedbackContent: str = feedbackContent # camelCase attr
        self.rating: Optional[int] = rating
        self.relatedTripID: Optional[str] = relatedTripID # camelCase attr
        self.status: str = status
        if submissionDatetime is None:
            self.submissionDatetime = datetime.now(timezone.utc) # camelCase attr
        elif isinstance(submissionDatetime, datetime):
            self.submissionDatetime = submissionDatetime if submissionDatetime.tzinfo else submissionDatetime.replace(tzinfo=timezone.utc)
        else:
            parsed_dt = self._parse_datetime(str(submissionDatetime))
            if parsed_dt is None: raise ValueError("Could not parse submissionDatetime")
            self.submissionDatetime = parsed_dt
        self.responseIDs: List[str] = responseIDs or [] # camelCase attr

    def updateStatus(self, newStatus: str) -> None: # Method name camelCase
        self.status = newStatus

    def addResponseID(self, responseID: str) -> None: # Method name camelCase
        if responseID not in self.responseIDs:
            self.responseIDs.append(responseID)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'feedbackID': self.feedbackID, # Key camelCase
            'submitterUserID': self.submitterUserID, # Key camelCase
            'feedbackContent': self.feedbackContent, # Key camelCase
            'rating': self.rating,
            'relatedTripID': self.relatedTripID, # Key camelCase
            'status': self.status,
            'submissionDatetime': self.submissionDatetime.isoformat(), # Key camelCase
            'responseIDs': self.responseIDs # Key camelCase
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Feedback']:
        # Expect camelCase keys
        if not isinstance(data, dict) or not all(k in data for k in ['submitterUserID', 'feedbackContent']):
            return None
        
        rating_val = data.get('rating')
        rating = int(rating_val) if rating_val is not None else None
        
        return cls(
            submitterUserID=data['submitterUserID'],
            feedbackContent=data['feedbackContent'],
            rating=rating,
            relatedTripID=data.get('relatedTripID'),
            feedbackID=data.get('feedbackID'),
            status=data.get('status', 'New'),
            submissionDatetime=data.get('submissionDatetime'),
            responseIDs=data.get('responseIDs', [])
        )

    @classmethod
    def getAll(cls, statusFilter: Optional[str] = None) -> List['Feedback']: # Method name camelCase
        all_feedback = super(Feedback, cls).getAll() # type: ignore
        if statusFilter:
            return [fb for fb in all_feedback if fb.status == statusFilter]
        return all_feedback

    def getResponses(self) -> List['Response']: # Method name camelCase, string type hint
        from .response import Response # Local import
        responses: List[Response] = []
        for r_id in self.responseIDs:
            response_obj = Response.findByID(r_id) # Response.findByID should be camelCase
            if response_obj:
                responses.append(response_obj)
        return responses