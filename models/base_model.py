# models/base_model.py
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TypeVar, Type
from .json_helpers import _load_data, _save_data # Relative import

T = TypeVar('T', bound='BaseModel') # Bound to BaseModel for type safety

class BaseModel:
    FILE_PATH: str = ""
    PRIMARY_KEY_FIELD: str = ""

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement to_dict")

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> Optional[T]:
        raise NotImplementedError("Subclasses must implement from_dict")

    def save(self) -> bool:
        if not self.FILE_PATH or not self.PRIMARY_KEY_FIELD:
            raise ValueError("FILE_PATH and PRIMARY_KEY_FIELD must be set in subclass.")

        all_data = _load_data(self.FILE_PATH)
        instance_dict = self.to_dict()
        primary_key_value = getattr(self, self.PRIMARY_KEY_FIELD)

        updated = False
        for i, item_data in enumerate(all_data):
            if item_data.get(self.PRIMARY_KEY_FIELD) == primary_key_value:
                all_data[i] = instance_dict
                updated = True
                break
        if not updated:
            all_data.append(instance_dict)

        _save_data(self.FILE_PATH, all_data)
        return True

    @classmethod
    def findByID(cls: Type[T], item_id: str) -> Optional[T]:
        if not cls.FILE_PATH or not cls.PRIMARY_KEY_FIELD:
            raise ValueError("FILE_PATH and PRIMARY_KEY_FIELD must be set in subclass.")

        all_data = _load_data(cls.FILE_PATH)
        for item_data in all_data:
            if item_data.get(cls.PRIMARY_KEY_FIELD) == item_id:
                return cls.from_dict(item_data)
        return None

    @classmethod
    def getAll(cls: Type[T]) -> List[T]:
        if not cls.FILE_PATH:
            raise ValueError("FILE_PATH must be set in subclass.")

        all_data = _load_data(cls.FILE_PATH)
        items: List[T] = []
        for item_data in all_data:
            obj = cls.from_dict(item_data)
            if obj:
                items.append(obj)
        return items

    @classmethod
    def _parse_datetime(cls, dateStr: Optional[str], default_now: bool = True) -> Optional[datetime]:
        if dateStr:
            try:
                if dateStr.endswith('Z'):
                    dt = datetime.fromisoformat(dateStr.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(dateStr)
                
                # If naive, assume UTC. If already timezone-aware, keep it.
                if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            except (TypeError, ValueError):
                print(f"Warning ({cls.__name__}): Could not parse date string '{dateStr}'.")
        if default_now:
            return datetime.now(timezone.utc)
        return None