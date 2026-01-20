from pydantic import BaseModel
from typing import Optional

class PillPayload(BaseModel):
    v: int = 1
    pid: str
    iat: int

class IssueRequest(BaseModel):
    pid: str
    iat: int

class IssueResponse(BaseModel):
    pill: str

class BurnRequest(BaseModel):
    pill: str

class SwapRequest(BaseModel):
    pill: str

class SwapResponse(BaseModel):
    token: str
    expires_in: int
