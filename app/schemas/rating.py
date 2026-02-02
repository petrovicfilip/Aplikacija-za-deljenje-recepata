from typing import Optional
from pydantic import BaseModel, Field

class RatingUpsert(BaseModel):
    value: int = Field(..., ge=1, le=5)

class RatingSummary(BaseModel):
    rating_sum: int
    rating_count: int
    rating_avg: float
    my_rating: Optional[int] = None
