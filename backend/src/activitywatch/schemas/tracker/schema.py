from typing import Dict, List
from pydantic import BaseModel


class ActivityEvent(BaseModel):
    timestamp: str
    duration: float
    data: Dict
    id: str = None

class ActivityBatch(BaseModel):
    device_id: str
    device_name: str = None
    bucket_id: str = None
    events: List[ActivityEvent]
    sync_token: str = None