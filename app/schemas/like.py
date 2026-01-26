from typing import List
from pydantic import BaseModel, Field, field_validator

class LikeCreate(BaseModel):
    user_id: str = Field(..., min_length=1)
    recipe_id: str = Field(..., min_length=1)

    @field_validator("user_id", "recipe_id")
    @classmethod
    def strip_ids(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("id must not be empty")
        return v

class LikeOut(BaseModel):
    user_id: str
    recipe_id: str

class UserLikesIdsResponse(BaseModel):
    user_id: str
    recipe_ids: List[str]

class UserLikesCountResponse(BaseModel):
    user_id: str
    total: int

class UserLikesIdsPageResponse(BaseModel):
    user_id: str
    skip: int
    limit: int
    total: int
    recipe_ids: List[str]