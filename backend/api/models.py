from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class DetectedEntity(BaseModel):
    type: str
    start: int
    end: int
    original: str
    replacement: str
    explanation: str
    score: float


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    status: str
    token: str


class ScrubRequest(BaseModel):
    prompt: str
    target_risk: str = "C4"
    language: Optional[str] = "en"


class TextScrubResponse(BaseModel):
    scrub_id: str
    scrubbed_text: str
    entities: List[DetectedEntity]


class FileScrubResponse(BaseModel):
    scrub_id: str
    entities: List[DetectedEntity]
    filename: str
    download_url: str


class DescrubRequest(BaseModel):
    scrub_id: str
    descrub_all: bool = False
    entity_replacements: List[str]
    justification: str


class TextDescrubResponse(BaseModel):
    scrub_id: str
    original_text: str
    scrubbed_text: str
    descrubbed_text: str


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool


class LogRecordResponse(BaseModel):
    id: str
    corp_key: str
    category: str
    action: str
    details: dict
    device_info: str
    browser_info: str
    client_ip: str
    user_agent: str
    timestamp: datetime


class LogListResponse(BaseModel):
    logs: List[LogRecordResponse]
    pagination: PaginationInfo


class LogSearchFilters(BaseModel):
    corp_key: Optional[str] = None
    category: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class LogSearchResponse(BaseModel):
    logs: List[LogRecordResponse]
    pagination: PaginationInfo
    filters: LogSearchFilters
