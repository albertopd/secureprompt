from pydantic import BaseModel
from typing import List, Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class ScrubRequest(BaseModel):
    prompt: str
    target_risk: str = "C4"
    language: Optional[str] = "en"


class DescrubRequest(BaseModel):
    prompt: str
    all_entitites: bool = False
    entities_ids: List[str]
    justification: str
