from pydantic import BaseModel
from typing import List, Optional

class VideoInfoRequest(BaseModel):
    url: str

class VideoFormat(BaseModel):
    format_id: Optional[str] = None
    ext: Optional[str] = None
    resolution: Optional[str] = None
    note: Optional[str] = None
    filesize: Optional[int] = None

class VideoInfoResponse(BaseModel):
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    formats: List[VideoFormat] = []
