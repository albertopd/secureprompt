from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class ScrubRequest(BaseModel):
    user_id: str
    prompt: str
    target_risk: str = "C4"
    language: Optional[str] = "en"

class DescrubRequest(BaseModel):
    user_id: str
    prompt: str
    all_tokens: bool = False
    token_ids: List[str]
    justification: str
