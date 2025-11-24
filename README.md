# fabFab (Incomplete)
Lovable UI

A web application that generates procedural 3D models (.obj files) from user prompts and images using AI, with customizable parameters for real-time modification.
Core Problem
Finding quality 3D assets for game engines like Unreal Engine is expensive and time-consuming. This tool democratizes 3D asset creation through AI-driven procedural generation.

## Inspiration
One participant had struggle finding game assets, known as fabs for a 3d environment and we thought we can create these fab assets with gemini ai. 

## What it does
Firstly creating a system where we can:
1. Input a prompt along with an image (optional) --> generates a ".obj", --> return to the user with modified features --> then the user can adjust --> will remodify the ".obj" to the users demand and return.

In the website, we used three.js to show a sample of the .obj file which can be downloaded afterwards.

## How we built it
Backend:
FastAPI, google gemini, and google adk.

Frontend:
Typescript (lovable), Three.js, and axios to connect to backend (incomplete). 

## Challenges we ran into
Communicating with gemini to give accurate results, but limited to tokens.
Struggled with fitting a gemini's agent to fit our architecture.
Postman commands would stall and fail calling gemini.

## Accomplishments that we're proud of
Developed a secure backend in case of failure.
Developed a friendly frontend that supports 3D obj using Three.js.

## What we learned
Although AI is amazing, AI has trouble developing 3D assets at higher levels unless having a lot of tokens. Similiarly to how AI struggled with artwork and now excels at it, maybe we will explore it in the future.

## What's next for fabFab
Completing it lol. Definitely optimizing our token usage so we can have more refined 3D models. Likely move from obj to other files like fbx. Lastly include textures for the 3D objects for complete fab design.


## Pipeline
### Data Flow
Generation Pipeline:
Input Processing
Validate prompt (sanitize, check length)
Decode/validate image if provided
Store in temporary session

### AI Generation
Send prompt + image to Gemini
Request structured .obj output
Parse and validate geometry

### Feature Analysis
Second Gemini call analyzes generated object
Extracts modifier schema
Maps features to vertex groups

### Storage
Cache model data (Redis/in-memory)
Generate unique ID
Store modifier metadata

### Response
Return .obj string
Include modifier UI schema
Send preview thumbnail

### Modification Pipeline:
Load cached model by ID
Parse .obj into data structure
Apply transformations based on modifiers
Regenerate .obj string
Return modified geometry

