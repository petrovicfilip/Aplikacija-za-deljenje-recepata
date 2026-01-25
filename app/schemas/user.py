from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)

class UserOut(BaseModel):
    id: str
    username:str