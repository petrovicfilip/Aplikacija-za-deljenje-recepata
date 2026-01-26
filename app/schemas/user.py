from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)

    @field_validator("username")
    @classmethod
    def norm_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("username must not be empty")
        return v

class UserOut(BaseModel):
    id: str
    username: str

class UserCreateResponse(BaseModel):
    user: UserOut
    created: bool
