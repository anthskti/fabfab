import dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.genai import types

dotenv.load_dotenv()

retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1, # Initial delay before first retry (in seconds)
    http_status_codes=[429, 500, 503, 504] # Retry on these HTTP errors
)

# Research agent
research_agent = Agent(
    name="ResearchAgent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=retry_config,
    ),
    instruction="""You are a specialized 3D modeller. Your task is to gather the vertices, 
    face definitions, texture coordinates, vertex normal, and material usage points
    for 3D models based on user queries. Use the tools at your disposal to find the values that are
    connected to the 3D modeling for obj files and to the user's query for type of object.""",
    tools=[google_search],
    output_key="research_findings",
)

# Format Agent
format_agent = Agent(
    name="FormatAgent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=retry_config,
    ),
    instruction="""You are an expert 3D modeler formatter. Generate valid .obj file content based on {research_findings}.
    
    CRITICAL RULES:
    1. Output ONLY the .obj file content, no explanations
    2. Each vertex (v), normal (vn), texture coordinate (vt), and face (f) MUST be on its own line
    3. Use actual newline characters between each line - this is CRITICAL
    4. Use simple, clean geometry (50-500 vertices for low-poly)
    5. Include vertex normals (vn) for proper lighting
    6. Use triangular faces (3 vertices per face)
    7. Ensure manifold geometry (no holes or duplicate vertices)
    
    FORMAT REQUIREMENTS:
    - Each line starts with a directive (v, vn, vt, f, o, mtllib, usemtl, s)
    - Lines are separated by newline characters
    - Example structure:
      v 1.0 -1.0 -1.0
      v 1.0 -1.0 1.0
      v -1.0 -1.0 1.0
    
    EXAMPLE OBJ FORMAT:
    mtllib cube.mtl\n
    o Cube\n
    v 1.000000 -1.000000 -1.000000\n
    v 1.000000 -1.000000 1.000000\n
    v -1.000000 -1.000000 1.000000\n
    v -1.000000 -1.000000 -1.000000\n
    v 1.000000 1.000000 -0.999999"\n
    v 0.999999 1.000000 1.000001\n
    v -1.000000 1.000000 1.000000\n
    v -1.000000 1.000000 -1.000000\n
    vt 1.000000 0.333333\n
    vt 1.000000 0.666667\n
    vt 0.666667 0.666667\n
    vt 0.666667 0.333333\n
    vt 0.666667 0.000000\n
    vt 0.000000 0.333333\n
    vt 0.000000 0.000000\n
    vt 0.333333 0.000000\n
    vt 0.333333 1.000000\n
    vt 0.000000 1.000000\n
    vt 0.000000 0.666667\n
    vt 0.333333 0.333333\n
    vt 0.333333 0.666667\n
    vt 1.000000 0.000000\n
    vn 0.000000 -1.000000 0.000000\n
    vn 0.000000 1.000000 0.000000\n
    vn 1.000000 0.000000 0.000000\n
    vn -0.000000 0.000000 1.000000\n
    vn -1.000000 -0.000000 -0.000000\n
    vn 0.000000 0.000000 -1.000000\n
    usemtl Material\n
    s off\n
    f 2/1/1 3/2/1 4/3/1\n
    f 8/1/2 7/4/2 6/5/2\n
    f 5/6/3 6/7/3 2/8/3\n
    f 6/8/4 7/5/4 3/4/4\n
    f 3/9/5 7/10/5 8/11/5\n
    f 1/12/6 4/13/6 8/11/6\n
    f 1/4/1 2/1/1 4/3/1\n
    f 5/14/2 8/1/2 6/5/2\n
    f 1/12/3 5/6/3 2/8/3\n
    f 2/12/4 6/8/4 3/4/4\n
    f 4/13/5 3/9/5 8/11/5\n
    f 5/6/6 1/12/6 8/11/6\n
    
    Now generate a low-poly .obj file with no headers for the {research_findings}:""",
    output_key="formatted_output",
)

# obj Agent
obj_agent = Agent(
    name="OBJAgent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=retry_config,
    ),
    instruction="""Your task is to make the {formatted_output} into a valid obj format with newlines.""",
    output_key="obj_content",
)

# Root Agent
root_agent = SequentialAgent(
    name="BobThe3DModeler",
    sub_agents=[research_agent, format_agent, obj_agent],
)
