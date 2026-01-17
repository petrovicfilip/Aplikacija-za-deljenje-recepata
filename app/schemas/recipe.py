from typing import List, Optional
from pydantic import BaseModel, Field
# DTO's

class RecipeCreate(BaseModel):
    # id: str = Field(..., min_length=1) sada ga generisem pri pozivu, ne prosledjujem od klijenta
    title: str = Field(..., min_length=1)
    ingredients: List[str] = Field(..., min_length=1)

class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    ingredients: Optional[List[str]] = None
