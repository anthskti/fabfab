"""
app/models/schemas.py - Pydantic data models for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Literal, Union
from uuid import UUID

# BaseModel Class Object
class Modifier(BaseModel):
    type: Literal["float", "boolean", "integer"] # For Slider/Switch
    min: Optional[float] = None
    max: Optional[float] = None
    default: Union[float, bool, int] # Suggested
    description: Optional[str] = None # Desc of Modifier

# Request model for Generation, data validation
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=200, description="Description a 3D model you want to generate!")
    image: Optional[str] = Field(None, description="Base64 encoded image (optional)")
    style: Literal["realistic", "low-poly", "stylized"] = Field(default="low-poly")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()

# Response model for generated 3D object
class GenerateResponse(BaseModel):
    obj_content: str = Field(..., description="Complete .obj file content")
    model_id: str = Field(..., description="Unique id for the model")
    preview_thumbnail: Optional[str] = Field(None, description="Base64 encoded preview image")
    available_modifiers: Dict[str, Modifier] = Field(default_factory=dict)

# Request model for generated 3D, get Id and applies modification
class ModifyRequest(BaseModel):
    model_id: str = Field(..., description="UUID of the model to modify")
    modifiers: Dict[str, Any] = Field(..., description="Dictionary of modifier values")
    
    @validator('modifiers')
    def validate_modifiers(cls, v):
        # Ensure modifiers dict is not empty
        if not v:
            raise ValueError("At least one modifier must be provided")
        return v


# Response Model for modified 3D object
class ModifyResponse(BaseModel):
    obj_content: str = Field(..., description="Modified .obj file content")
    preview_thumbnail: Optional[str] = Field(None, description="Base64 encoded preview image")

# Error Response 
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


