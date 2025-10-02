from pydantic import BaseModel, Field
from typing import List, Optional

class LoginRequest(BaseModel):
    email: str
    CorpKey: str

class ScrubRequest(BaseModel):
    user_id: str
    prompt: str
    target_risk: str = "C3"
    language: Optional[str] = "en"

class DescrubRequest(BaseModel):
    user_id: str
    prompt: str
    all_tokens: bool = False
    token_ids: List[str]
    justification: str
