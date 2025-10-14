from pydantic import BaseModel, Field
from typing import List

class IngestRequest(BaseModel):
    days: int = 365  # 1년

class SketchRequest(BaseModel):
    y: List[float] = Field(..., min_items=10)  # 스케치 y값 (0~1 권장)
    target_len: int = 200

class SimilarResponseItem(BaseModel):
    ticker: str
    score: float
    rank: int

class SimilarResponse(BaseModel):
    items: List[SimilarResponseItem]