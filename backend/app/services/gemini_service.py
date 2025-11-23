"""
gemini_service.py - Google Gemini AI integration for 3D model generation
"""
import google.generativeai as genai
import os
import json
import base64
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import io

# Configure Gemini API

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize models
generation_model = genai.GenerativeModel('gemini-2.0-flash-exp')
feature_model = genai.GenerativeModel('gemini-2.0-flash-exp')

# System prompts
GENERATION_SYSTEM_PROMPT = """You are an expert 3D modeler. Generate valid Wavefront .obj file content based on user descriptions.

CRITICAL RULES:
1. Output ONLY the .obj file content, no explanations
2. Use simple, clean geometry (50-500 vertices for low-poly)
3. Include vertex normals (vn) for proper lighting
4. Use triangular faces (3 vertices per face)
5. Add comments to tag semantic groups: # GROUP:leaf, # GROUP:stem, etc.
6. Ensure manifold geometry (no holes or duplicate vertices)

EXAMPLE OBJ FORMAT:
# Object: strawberry
o Strawberry
# GROUP:body
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.5 1.0 0.0
vn 0.0 0.0 1.0
vn 0.0 0.0 1.0
vn 0.0 0.0 1.0
f 1//1 2//2 3//3
# GROUP:leaf
v 0.5 1.2 0.0
v 0.6 1.5 0.1
...

Now generate a {style} style .obj file for: {prompt}"""

FEATURE_EXTRACTION_PROMPT = """Analyze this .obj 3D model and identify meaningful modifiers that users could adjust.

INPUT OBJ:
{obj_content}

ORIGINAL PROMPT: {prompt}

Extract 3-5 intuitive modifiers that make sense for this object. For each modifier, determine:
1. Name (snake_case)
2. Type (float, boolean, or integer)
3. Range (min/max for numbers)
4. Default value
5. Description

OUTPUT ONLY VALID JSON in this exact format:
{{
  "overall_size": {{
    "type": "float",
    "min": 0.1,
    "max": 5.0,
    "default": 1.0,
    "description": "Overall scale of the entire object"
  }},
  "example_modifier": {{
    "type": "boolean",
    "default": false,
    "description": "Example boolean toggle"
  }}
}}

Respond with ONLY the JSON, no markdown formatting."""

class GeminiService:
    """Service for AI-powered 3D generation"""
    
    @staticmethod
    def decode_image(base64_str: str) -> Optional[Image.Image]:
        """Decode base64 image string to PIL Image"""
        try:
            # Remove data URL prefix if present
            if "," in base64_str:
                base64_str = base64_str.split(",")[1]
            
            image_data = base64.b64decode(base64_str)
            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            print(f"Error decoding image: {e}")
            return None
    
    @staticmethod
    async def generate_obj(prompt: str, style: str, image_base64: Optional[str] = None) -> str:
        """
        Generate .obj file content using Gemini
        
        Args:
            prompt: User's text description
            style: Style preference (realistic, low-poly, stylized)
            image_base64: Optional base64 encoded reference image
            
        Returns:
            Complete .obj file content as string
        """
        try:
            formatted_prompt = GENERATION_SYSTEM_PROMPT.format(style=style, prompt=prompt)
            
            # Prepare content for generation
            content = [formatted_prompt]
            
            # Add image if provided
            if image_base64:
                image = GeminiService.decode_image(image_base64)
                if image:
                    content.append(image)
            
            # Generate with timeout
            response = generation_model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=8192,
                ),
                request_options={"timeout": 30}
            )
            
            obj_content = response.text.strip()
            
            # Validate basic OBJ structure
            if not obj_content.startswith(("#", "o ", "v ")) or "v " not in obj_content:
                raise ValueError("Generated content is not valid OBJ format")
            
            # Clean up any markdown formatting if present
            if "```" in obj_content:
                obj_content = obj_content.split("```")[1]
                if obj_content.startswith("obj\n"):
                    obj_content = obj_content[4:]
            
            return obj_content
            
        except Exception as e:
            print(f"Error generating OBJ: {e}")
            # Return fallback cube geometry
            return GeminiService._get_fallback_geometry(prompt)
    
    @staticmethod
    async def extract_features(obj_content: str, original_prompt: str) -> Dict[str, Any]:
        """
        Extract available modifiers from generated model
        
        Args:
            obj_content: Generated .obj file content
            original_prompt: User's original prompt
            
        Returns:
            Dictionary of available modifiers
        """
        try:
            # Truncate OBJ content if too long
            truncated_obj = obj_content[:2000] + "\n..." if len(obj_content) > 2000 else obj_content
            
            formatted_prompt = FEATURE_EXTRACTION_PROMPT.format(
                obj_content=truncated_obj,
                prompt=original_prompt
            )
            
            response = feature_model.generate_content(
                formatted_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                ),
                request_options={"timeout": 15}
            )
            
            # Parse JSON response
            feature_text = response.text.strip()
            
            # Remove markdown if present
            if "```" in feature_text:
                feature_text = feature_text.split("```")[1]
                if feature_text.startswith("json\n"):
                    feature_text = feature_text[5:]
            
            features = json.loads(feature_text)
            
            # Validate structure
            if not isinstance(features, dict):
                raise ValueError("Features must be a dictionary")
            
            # Ensure overall_size is always present
            if "overall_size" not in features:
                features["overall_size"] = {
                    "type": "float",
                    "min": 0.1,
                    "max": 5.0,
                    "default": 1.0,
                    "description": "Overall scale of the object"
                }
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            # Return default modifiers
            return {
                "overall_size": {
                    "type": "float",
                    "min": 0.1,
                    "max": 5.0,
                    "default": 1.0,
                    "description": "Overall scale of the object"
                },
                "smoothness": {
                    "type": "integer",
                    "min": 0,
                    "max": 100,
                    "default": 50,
                    "description": "Surface smoothness"
                }
            }
    
    @staticmethod
    def _get_fallback_geometry(prompt: str) -> str:
        """Return simple cube geometry as fallback"""
        return """# Fallback geometry
o SimpleCube
# GROUP:body
v -0.5 -0.5 -0.5
v 0.5 -0.5 -0.5
v 0.5 0.5 -0.5
v -0.5 0.5 -0.5
v -0.5 -0.5 0.5
v 0.5 -0.5 0.5
v 0.5 0.5 0.5
v -0.5 0.5 0.5
vn 0.0 0.0 -1.0
vn 0.0 0.0 1.0
vn -1.0 0.0 0.0
vn 1.0 0.0 0.0
vn 0.0 -1.0 0.0
vn 0.0 1.0 0.0
f 1//1 2//1 3//1
f 1//1 3//1 4//1
f 5//2 6//2 7//2
f 5//2 7//2 8//2
f 1//3 4//3 8//3
f 1//3 8//3 5//3
f 2//4 6//4 7//4
f 2//4 7//4 3//4
f 1//5 2//5 6//5
f 1//5 6//5 5//5
f 4//6 3//6 7//6
f 4//6 7//6 8//6
"""