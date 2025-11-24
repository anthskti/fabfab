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

print(f"✓ Gemini API configured with key: {GOOGLE_API_KEY[:10]}...")

# Initialize models - using Gemini 2.5 Flash (latest stable)
generation_model = genai.GenerativeModel('gemini-2.5-flash')
feature_model = genai.GenerativeModel('gemini-2.5-flash')

# System prompts
GENERATION_SYSTEM_PROMPT = """You are an expert 3D modeler. Generate a COMPLETE valid Wavefront .obj file.

CRITICAL RULES:
1. Output ONLY the .obj file content - no explanations, no markdown backticks
2. Generate a COMPLETE model with ALL vertices and ALL faces
3. Use simple geometry (100-300 vertices for low-poly, 300-800 for realistic)
4. MUST include both vertices (v) AND faces (f) - never stop mid-generation
5. Include vertex normals (vn) for proper lighting
6. Use triangular faces (3 vertices per face): f v1//n1 v2//n2 v3//n3
7. Add group comments: # GROUP:seat, # GROUP:legs (on separate lines, not inline)
8. NEVER add inline comments after v, vn, vt, or f lines

CORRECT FORMAT:
# Object: chair
o Chair
# GROUP:seat
v -0.5 0.5 -0.5
v 0.5 0.5 -0.5
v 0.5 0.5 0.5
v -0.5 0.5 0.5
vn 0.0 1.0 0.0
vn 0.0 1.0 0.0
vn 0.0 1.0 0.0
f 1//1 2//2 3//3
f 1//1 3//3 4//1
# GROUP:legs
v -0.4 0.0 -0.4
v -0.3 0.0 -0.4
v -0.3 0.5 -0.4
vn 0.0 0.0 -1.0
f 5//4 6//4 7//4

Generate a COMPLETE {style} style .obj file for: {prompt}

Remember: Output the ENTIRE model including ALL faces. Do not truncate."""

FEATURE_EXTRACTION_PROMPT = """You are analyzing a 3D model to extract modifiable parameters.

OBJ FILE PREVIEW:
{obj_content}

ORIGINAL PROMPT: {prompt}

Identify 3-5 intuitive modifiers. For each:
- Name in snake_case
- Type: "float", "boolean", or "integer"
- For numbers: min, max, default
- For booleans: default (true/false)
- Brief description

RESPOND WITH ONLY THIS JSON FORMAT (no markdown, no backticks):
{{
  "overall_size": {{
    "type": "float",
    "min": 0.1,
    "max": 5.0,
    "default": 1.0,
    "description": "Overall scale"
  }},
  "seat_height": {{
    "type": "float",
    "min": 0.3,
    "max": 1.0,
    "default": 0.6,
    "description": "Height of seat from ground"
  }}
}}

Output ONLY valid JSON, nothing else."""

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
            
            print("=" * 60)
            print("GENERATING OBJ FILE")
            print(f"Prompt: '{prompt}'")
            print(f"Style: {style}")
            print(f"Prompt length: {len(formatted_prompt)} chars")
            print("=" * 60)
            
            # Prepare content for generation
            content = [formatted_prompt]
            
            # Add image if provided
            if image_base64:
                image = GeminiService.decode_image(image_base64)
                if image:
                    content.append(image)
                    print(f"✓ Added reference image: {image.size}")
            
            print("→ Calling Gemini API...")
            
            # Generate
            response = generation_model.generate_content(
                content,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=16384,  # Increased from 8192
                    candidate_count=1,
                )
            )
            
            print("✓ Received response from Gemini")
            
            # Handle multi-part responses (new API format)
            try:
                obj_content = response.text.strip()
            except ValueError as e:
                # Response is multi-part, need to extract manually
                print("→ Response is multi-part, extracting content...")
                obj_content = ""
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            obj_content += part.text
                obj_content = obj_content.strip()
                print(f"✓ Extracted from {len(response.candidates)} candidates")
            
            print(f"✓ Response length: {len(obj_content)} chars")
            
            # Check finish reason
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                print(f"→ Finish reason: {finish_reason}")
                if finish_reason != 1:  # 1 = STOP (normal completion)
                    print(f"⚠ WARNING: Generation may be incomplete (reason: {finish_reason})")
            
            print(f"First 300 chars:\n{obj_content[:300]}\n")
            
            # Clean up markdown formatting if present
            if "```" in obj_content:
                print("→ Cleaning markdown formatting...")
                parts = obj_content.split("```")
                # Find the part with actual OBJ content
                for i, part in enumerate(parts):
                    if "v " in part or "f " in part:
                        obj_content = part
                        print(f"✓ Found OBJ content in part {i}")
                        break
                
                # Remove language identifier
                if obj_content.startswith("obj\n"):
                    obj_content = obj_content[4:]
                elif obj_content.startswith("obj"):
                    obj_content = obj_content[3:].lstrip()
            
            # Remove inline comments (e.g., "v 1.0 2.0 3.0 # comment")
            print("→ Cleaning inline comments...")
            cleaned_lines = []
            for line in obj_content.split('\n'):
                stripped = line.strip()
                
                # Keep empty lines and standalone comments
                if not stripped or stripped.startswith('#'):
                    cleaned_lines.append(line)
                    continue
                
                # For OBJ commands, remove inline comments
                if any(stripped.startswith(cmd) for cmd in ['v ', 'vn ', 'vt ', 'f ', 'o ', 'g ', 'usemtl ', 's ']):
                    # Split on # and take only the first part
                    if '#' in stripped:
                        cleaned = stripped.split('#')[0].rstrip()
                        cleaned_lines.append(cleaned)
                    else:
                        cleaned_lines.append(stripped)
                else:
                    cleaned_lines.append(line)
            
            obj_content = '\n'.join(cleaned_lines)
            
            print(f"✓ Cleaned content length: {len(obj_content)} chars")
            
            # Count vertices and faces
            vertex_count = obj_content.count('\nv ') + (1 if obj_content.startswith('v ') else 0)
            face_count = obj_content.count('\nf ') + (1 if obj_content.startswith('f ') else 0)
            
            print(f"✓ Found {vertex_count} vertices, {face_count} faces")
            
            # Validate basic OBJ structure
            if vertex_count == 0:
                raise ValueError("Generated content has no vertices")
            
            if face_count == 0:
                raise ValueError("Generated content has no faces")
            
            # Optional: Flip face winding if needed (uncomment if issues persist)
            obj_content = GeminiService._flip_face_winding(obj_content)
            
            print("✓ SUCCESS - Valid OBJ file generated")
            print("=" * 60)
            
            return obj_content
            
        except Exception as e:
            print("=" * 60)
            print(f"✗ EXCEPTION: {type(e).__name__}")
            print(f"✗ Error: {e}")
            print("=" * 60)
            import traceback
            traceback.print_exc()
            print("=" * 60)
            print("→ Returning fallback cube geometry")
            print("=" * 60)
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
            print("=" * 60)
            print("EXTRACTING FEATURES")
            print("=" * 60)
            
            # Truncate OBJ content if too long
            truncated_obj = obj_content[:2000] + "\n..." if len(obj_content) > 2000 else obj_content
            
            formatted_prompt = FEATURE_EXTRACTION_PROMPT.format(
                obj_content=truncated_obj,
                prompt=original_prompt
            )
            
            print("→ Calling Gemini API for feature extraction...")
            
            response = feature_model.generate_content(
                formatted_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=4096,  # Increased from 2048
                    candidate_count=1,
                )
            )
            
            print("✓ Received feature extraction response")
            
            # Handle multi-part responses
            try:
                feature_text = response.text.strip()
            except (ValueError, AttributeError):
                print("→ Multi-part response, extracting...")
                feature_text = ""
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    feature_text += part.text
                feature_text = feature_text.strip()
                
                # If still empty, check prompt_feedback
                if not feature_text:
                    print(f"⚠ Empty response from API")
                    if hasattr(response, 'prompt_feedback'):
                        print(f"Prompt feedback: {response.prompt_feedback}")
                    print(f"Response object: {response}")
                    print(f"Candidates: {response.candidates if hasattr(response, 'candidates') else 'None'}")
                    raise ValueError("Empty response from Gemini API")
            
            print(f"Response length: {len(feature_text)} chars")
            print(f"First 200 chars: {feature_text[:200]}")
            
            # Remove markdown if present
            if "```" in feature_text:
                print("→ Cleaning markdown from features...")
                parts = feature_text.split("```")
                # Find the JSON part
                for part in parts:
                    if "{" in part and "}" in part:
                        feature_text = part
                        break
                
                # Remove language identifier
                if feature_text.startswith("json\n"):
                    feature_text = feature_text[5:]
                elif feature_text.startswith("json"):
                    feature_text = feature_text[4:].lstrip()
            
            feature_text = feature_text.strip()
            
            print(f"Cleaned feature text:\n{feature_text}\n")
            
            features = json.loads(feature_text)
            
            # Validate structure
            if not isinstance(features, dict):
                raise ValueError("Features must be a dictionary")
            
            print(f"✓ Extracted {len(features)} features: {list(features.keys())}")
            
            # Ensure overall_size is always present
            if "overall_size" not in features:
                print("→ Adding default overall_size modifier")
                features["overall_size"] = {
                    "type": "float",
                    "min": 0.1,
                    "max": 5.0,
                    "default": 1.0,
                    "description": "Overall scale of the object"
                }
            
            print("✓ Feature extraction complete")
            print("=" * 60)
            
            return features
            
        except Exception as e:
            print("=" * 60)
            print(f"✗ Error extracting features: {e}")
            import traceback
            traceback.print_exc()
            print("=" * 60)
            print("→ Returning default modifiers")
            # Return default modifiers
            return {
                "overall_size": {
                    "type": "float",
                    "min": 0.1,
                    "max": 5.0,
                    "default": 1.0,
                    "description": "Overall scale of the object"
                }
            }
    
    @staticmethod
    def _flip_face_winding(obj_content: str) -> str:
        """Flip the winding order of all faces (reverses normals)"""
        lines = []
        for line in obj_content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('f '):
                # Parse face vertices
                parts = stripped.split()[1:]  # Skip 'f'
                # Reverse the order (keeping first vertex first for consistency)
                if len(parts) > 2:
                    reversed_parts = [parts[0]] + list(reversed(parts[1:]))
                    lines.append('f ' + ' '.join(reversed_parts))
                else:
                    lines.append(line)
            else:
                lines.append(line)
        return '\n'.join(lines)
    
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