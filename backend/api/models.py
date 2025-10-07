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
    descrubbed_text: str

