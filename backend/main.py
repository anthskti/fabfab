import os
import shutil
import subprocess
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
import onnxruntime as ort
from rembg import remove
import google.generativeai as genai
from dotenv import load_dotenv


# CONFIG
BLENDER_EXEC_PATH = "/Applications/Blender.app/Contents/MacOS/Blender"
genai.configure(api_key=os.dotenv.GEMINI_API_KEY)

app = FastAPI()

# For frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DIRS = ["temp_uploads", "temp_scripts", "output_models"]
for d in DIRS:
    os.makedirs(d, exist_ok=True)

@app.post("/create-model")
async def create_model(
    file: UploadFile = File(...), 
    length: float = Form(1.0), 
    width: float = Form(1.0),
    height: float = Form(1.0)
):
    session_id = str(uuid.uuid4())
    print(f"Starting job: {session_id}")

    # 1. Save and Clean Image
    input_path = f"temp_uploads/{session_id}_original.png"
    clean_path = f"temp_uploads/{session_id}_clean.png"
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Remove background (Critical for Gemini to understand shape)
    # print("Removing background...")
    # input_img = Image.open(input_path)
    # output_img = remove(input_img)
    # output_img.save(clean_path)
    output_img = Image.open(input_path)

    # 2. Generate Blender Script via Gemini
    print("Consulting Gemini...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    ROLE: You are a Senior Technical Artist specializing in the Blender 5.0 Python API.

    GOAL: Generate valid, execution-ready Python scripts to model 3D objects based on the image attached.

    STRATEGIC WORKFLOW (MANDATORY):
    1. BLOCKOUT: Always start by creating primitive shapes (Cube, Cylinder, UV Sphere, Plane) to establish the object's primary silhouette and dimensions.
    2. REFINEMENT: After the blockout, use 'bmesh' or modifiers (e.g., Bevel, Subdivision) to refine geometry.
    - Do NOT use complex simulation modifiers (Cloth, Fluid).
    - Do NOT use the 'Knife Tool' (it is unreliable in scripts). Use Loop Cuts or Booleans instead.
    3. MATERIALS: Create and assign Principled BSDF materials immediately after generating each mesh part.
    4. ASSEMBLY: Join all parts into a single mesh at the end.

    GEOMETRY STRATEGY (PROCEDURAL):
    1. DO NOT just scale primitives. Use 'bmesh' to iterate over vertices.
    2. USE MATH for organic shapes:
    - For cloth/flags: Use 'math.sin()' and 'math.cos()' to displace Z/Y coordinates based on X distance.
    - For terrain: Use 'math.exp()' or random noise for natural falloff.
    3. SUBDIVISION: Always apply a Subdivision Surface modifier (Level 1 or 2) to organic shapes.
    4. STRUCTURE: Break the script into clear functions: 'create_pole()', 'create_flag()', 'create_ground()'.

    STRICT TECHNICAL CONSTRAINTS:
    1. API VERSION: Blender 5.0 Strict.
    - Use 'bpy.types.Annotation' instead of 'GreasePencil'.
    - Use 'get_transform()' / 'set_transform()' where applicable.
    - Warning: 'mathutils' vectors are now float32; avoid high-precision float64 logic.
    2. OUTPUT FORMAT:
    - Return ONLY valid Python code.
    - NO Markdown backticks (```), NO explanations, NO comments (unless inside code).
    - Code must be copy-paste ready.
    3. VARIABLE NAMING:
    - Use 'snake_case'.
    - Mesh Objects: Prefix with 'geo_' (e.g., 'geo_pole', 'geo_flag').
    - Materials: Prefix with 'mat_' (e.g., 'mat_red_fabric').
    4. SCENE MANAGEMENT:
    - Always wrap logic in a 'main()' function.
    - Start with: 'bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete()'.
    5. MATERIAL LIMITS:
    - Only use these Principled BSDF inputs: Base Color, Metallic, Roughness, Alpha, Normal, Emission Color, Emission Strength.
    6. EXPORT:
    - Final object name: 'geo_final'.
    - Export path: 'output_models/{session_id}.fbx'.

    ERROR PREVENTION:
    - Do NOT output partial code. If logic is complex, break it into helper functions (e.g., 'create_pole()', 'create_flag()').
    - Do NOT try to model "exactly" pixel-perfect from vague descriptions; prioritize clean topology and structural likeness.
    """
    
    response = model.generate_content([prompt, output_img])
    script_content = response.text.replace("```python", "").replace("```", "").strip()
    
    script_path = f"temp_scripts/{session_id}.py"
    with open(script_path, "w") as f:
        f.write(script_content)

    # Execute Blender Headless
    print("Running Blender Factory...")
    output_fbx = f"output_models/{session_id}.fbx"
    
    # The Magic Command
    cmd = [
        BLENDER_EXEC_PATH,
        "--background",      # Run without UI
        "--python", script_path # Run our generated script
    ]
    
    try:
        subprocess.run(cmd, check=True, timeout=60) # 60s timeout
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": "Blender failed to generate model."}

    if os.path.exists(output_fbx):
        return FileResponse(output_fbx, media_type="application/octet-stream", filename="model.fbx")
    else:
        return {"status": "error", "message": "Output file not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)