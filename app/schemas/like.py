from pydantic import BaseModel, Field

class LikeCreate(BaseModel):
    user_id: str = Field(..., min_length=1)
    recipe_id: str = Field(..., min_length=1)