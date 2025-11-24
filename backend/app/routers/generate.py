"""
routers/generate.py - API routes for model generation and modification
"""

"""
generate.py - API routes for model generation and modification
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
import asyncio
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import tempfile
import os
from backend.app.services.agent import root_agent

from backend.app.models.schema import (
    GenerateRequest, GenerateResponse,
    ModifyRequest, ModifyResponse,
    ErrorResponse, QueryRequest, ModelResponse
)
from backend.app.services.obj_service import OBJService
from backend.app.utils.cache import model_cache

router = APIRouter()


@router.post("/modify", response_model=ModifyResponse)
async def modify_model(request: ModifyRequest):
    """
    Modify an existing model with new parameter values  
    Args: request: ModifyRequest with model_id and modifiers dict
    Returns: ModifyResponse with modified obj_content
    """
    try:
        # Step 1: Retrieve from cache
        cached = model_cache.get(request.model_id)
        if not cached:
            raise HTTPException(status_code=404, detail="Model not found or expired")
        
        print(f"Modifying model {request.model_id} with params: {request.modifiers}")
        
        # Step 2: Validate modifier keys
        invalid_modifiers = set(request.modifiers.keys()) - set(cached.modifiers.keys())
        if invalid_modifiers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid modifiers: {invalid_modifiers}. Available: {list(cached.modifiers.keys())}"
            )
        
        # Step 3: Validate modifier values
        for key, value in request.modifiers.items():
            modifier_def = cached.modifiers[key]
            
            if modifier_def["type"] == "float" or modifier_def["type"] == "integer":
                if not isinstance(value, (int, float)):
                    raise HTTPException(status_code=400, detail=f"{key} must be a number")
                
                min_val = modifier_def.get("min")
                max_val = modifier_def.get("max")
                
                if min_val is not None and value < min_val:
                    raise HTTPException(status_code=400, detail=f"{key} must be >= {min_val}")
                if max_val is not None and value > max_val:
                    raise HTTPException(status_code=400, detail=f"{key} must be <= {max_val}")
            
            elif modifier_def["type"] == "boolean":
                if not isinstance(value, bool):
                    raise HTTPException(status_code=400, detail=f"{key} must be a boolean")
        
        # Step 4: Apply modifiers
        modified_obj = OBJService.apply_modifiers(
            obj_content=cached.obj_content,
            modifiers=request.modifiers
        )
        
        # Step 5: Update cache
        model_cache.update(request.model_id, modified_obj)
        
        print(f"Model {request.model_id} modified successfully")
        
        return ModifyResponse(
            obj_content=modified_obj,
            preview_thumbnail=None  # TODO: Generate thumbnail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in modify_model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{model_id}", response_class=PlainTextResponse)
async def download_model(model_id: str):
    """
    Download the .obj file for a model
    Args: model_id: UUID of the model 
    Returns: .obj file content as plain text
    """
    try:
        cached = model_cache.get(model_id)
        if not cached:
            raise HTTPException(status_code=404, detail="Model not found or expired")
        
        return Response(
            content=cached.obj_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=model_{model_id[:8]}.obj"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in download_model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for debugging"""
    return model_cache.get_stats()

@router.delete("/cache/{model_id}")
async def delete_cached_model(model_id: str):
    """Delete a model from cache"""
    model_cache.delete(model_id)
    return {"status": "deleted", "model_id": model_id}

@router.post("/generate-model", response_model=GenerateResponse)
async def generate_model(request: GenerateRequest):
    """
    Generate a 3D model from a text description.

    Args:
        request: QueryRequest with 'query' field

    Returns:
        ModelResponse with OBJ content and metadata
    """
    try:
        if not request.query or request.query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Run the agent
        result = root_agent.run(request.query)

        # Post-process the output
        obj_content = result.data["formatted_output"]
        obj_content = obj_content.replace("\\n", "\n")

        # Calculate stats
        stats = {
            "vertices": obj_content.count('\nv '),
            "faces": obj_content.count('\nf '),
            "normals": obj_content.count('\nvn '),
            "texture_coords": obj_content.count('\nvt ')
        }

        return GenerateResponse(
            obj_content=obj_content
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating model: {str(e)}")
