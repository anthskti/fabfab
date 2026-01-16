# fabFab 

A web application that generates 3D models/assets from user image using Google Gemini.

**Core Problem**: Finding quality 3D assets for game engines, like Unreal Engine, is expensive and time-consuming. \
**Inspiration**: One of the team members struggled with finding game assets, known as **fabs**, for a 3D evironment scene they were designing in Unreal Engine. 

## How it Works
The pipeline goes as such:
1. Import an image that you want to make, turn 3D asset.
2. Set the measurements of the assets. This is important because of file size is an important part in 3D environments. Needing more detailed assets, you might want a more realistic asset.
3. You would click "Run" and a api call will sent to the backend.
4. After a few seconds, you will recieve a, navigatable, 3D asset (.fbx) you can check out on the site and download.

## How we Built it
**Backend**: Python, FastAPI, Google Gemini.

**Frontend**: Javascript, Three.js, Next.js, and Axios. 

