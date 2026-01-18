from typing import List, Optional
from pydantic import BaseModel, Field
# DTO's

class IngredientInput(BaseModel):
    name: str = Field(..., min_length=1)
    amount: Optional[float] = Field(None, gt=0)   # npr 3, 250, 0.5
    unit: Optional[str] = Field(None, min_length=1)  # "g", "ml", "kom", "kasika"...

class RecipeCreate(BaseModel):
    # id: str = Field(..., min_length=1) sada ga generisem pri pozivu, ne prosledjujem od klijenta
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    ingredients: List[IngredientInput] = Field(..., min_length=1)

class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    ingredients: Optional[List[IngredientInput]] = None