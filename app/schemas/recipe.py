from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# DTOs

class IngredientInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    amount: Optional[float] = Field(None, gt=0)          # npr 3, 250, 0.5
    unit: Optional[str] = Field(None, min_length=1, max_length=16)  # "g", "ml", "kom"...

    @field_validator("name")
    @classmethod
    def norm_name(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("unit")
    @classmethod
    def norm_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        return v or None

    @model_validator(mode="after")
    def amount_unit_consistency(self):
        if self.unit is not None and self.amount is None:
            raise ValueError("amount is required when unit is provided")
        return self


class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    ingredients: List[IngredientInput] = Field(..., min_length=1)

    @field_validator("title")
    @classmethod
    def norm_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v

    @field_validator("description")
    @classmethod
    def norm_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @model_validator(mode="after")
    def no_duplicate_ingredients(self):
        names = [i.name for i in self.ingredients]
        if len(names) != len(set(names)):
            raise ValueError("ingredients contain duplicates")
        return self


class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    ingredients: Optional[List[IngredientInput]] = None

    @field_validator("title")
    @classmethod
    def norm_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v

    @field_validator("description")
    @classmethod
    def norm_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v

    @model_validator(mode="after")
    def validate_ingredients_if_present(self):
        if self.ingredients is None:
            return self
        if len(self.ingredients) == 0:
            raise ValueError("ingredients must not be empty")

        names = [i.name for i in self.ingredients]
        if len(names) != len(set(names)):
            raise ValueError("ingredients contain duplicates")
        return self

class RecipeIdsRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1)