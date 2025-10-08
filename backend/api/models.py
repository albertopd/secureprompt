from pydantic import BaseModel
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


class LLMIngestRequest(BaseModel):
    # Optionally override default data folder
    data_folder: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    row_as_chunk: bool = True


class LLMQueryRequest(BaseModel):
    question: str
    top_k: int = 3
    # Optional explicit max security level like "c2"; otherwise use user role mapping
    max_security: Optional[str] = None
