"""
cache.py - In-memory model storage with TTL for 1 hour.
"""
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
import uuid

@dataclass
class CachedModel:
    """Represents a cached 3D model"""
    model_id: str # Unique ID from schema
    obj_content: str
    modifiers: Dict[str, Any]
    original_prompt: str
    timestamp: float
    
class ModelCache:
    """Simple in-memory cache with TTL (Time To Live)"""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache
        Args: ttl_seconds: Time to live in seconds (default 1 hour)
        """
        self._cache: Dict[str, CachedModel] = {}
        self.ttl_seconds = ttl_seconds
    
    def store(self, obj_content: str, modifiers: Dict[str, Any], prompt: str) -> str:
        """
        Store a model in cache. Called from /api/generate
        Args:
            obj_content: .obj file content
            modifiers: Available modifiers for this model
            prompt: Original user prompt    
        Returns: model_id (UUID string)
        """
        model_id = str(uuid.uuid4())
        
        cached = CachedModel(
            model_id=model_id,
            obj_content=obj_content,
            modifiers=modifiers,
            original_prompt=prompt,
            timestamp=time.time()
        )
        
        self._cache[model_id] = cached
        
        # Cleanup expired entries
        self._cleanup()
        
        return model_id
    
    def get(self, model_id: str) -> Optional[CachedModel]:
        """
        Retrieve a model from cache. Called when /api/modify and /api/download
        Args: model_id: UUID of the model 
        Returns: CachedModel if found and not expired, None otherwise
        """
        if model_id not in self._cache:
            return None
        
        cached = self._cache[model_id]
        
        # Check if expired
        if time.time() - cached.timestamp > self.ttl_seconds:
            del self._cache[model_id]
            return None
        
        return cached
    
    def update(self, model_id: str, obj_content: str):
        """
        Update the OBJ content of a cached model
        Called after /api/modify
        
        Args:
            model_id: UUID of the model
            obj_content: New .obj file content
        """
        if model_id in self._cache:
            self._cache[model_id].obj_content = obj_content
            self._cache[model_id].timestamp = time.time()  # Refreshes timestamp
    
    def delete(self, model_id: str):
        """Delete a model from cache"""
        if model_id in self._cache:
            del self._cache[model_id]
    
    def _cleanup(self):
        """Remove expired entries"""
        current_time = time.time()
        expired = [
            model_id for model_id, cached in self._cache.items()
            if current_time - cached.timestamp > self.ttl_seconds
        ]
        
        for model_id in expired:
            del self._cache[model_id]
    
    # ONLY FOR DEBUGGING
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self._cleanup()
        return {
            "cached_models": len(self._cache),
            "ttl_seconds": self.ttl_seconds,
            "model_ids": list(self._cache.keys())
        }

# Global cache instance
model_cache = ModelCache(ttl_seconds=3600)