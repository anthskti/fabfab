//still in development

import { useEffect, useRef, useState } from 'react';
import { Box, Grid3x3 } from 'lucide-react';
import * as THREE from 'three';

export const ModelViewer = ({ modelUrl }) => {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const modelRef = useRef(null);
  const [hasModel, setHasModel] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(
      45,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight1.position.set(5, 10, 5);
    scene.add(directionalLight1);

    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight2.position.set(-5, 5, -5);
    scene.add(directionalLight2);

    // Grid helper
    const gridHelper = new THREE.GridHelper(20, 20, 0x00ffff, 0x00ffff);
    gridHelper.material.opacity = 0.2;
    gridHelper.material.transparent = true;
    scene.add(gridHelper);

    // Mouse controls
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    let cameraRotation = { theta: Math.PI / 4, phi: Math.PI / 4 };
    let cameraDistance = 8;

    const updateCameraPosition = () => {
      camera.position.x = cameraDistance * Math.sin(cameraRotation.theta) * Math.cos(cameraRotation.phi);
      camera.position.y = cameraDistance * Math.sin(cameraRotation.phi);
      camera.position.z = cameraDistance * Math.cos(cameraRotation.theta) * Math.cos(cameraRotation.phi);
      camera.lookAt(0, 0, 0);
    };

    const onMouseDown = (e) => {
      isDragging = true;
      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e) => {
      if (!isDragging) return;

      const deltaX = e.clientX - previousMousePosition.x;
      const deltaY = e.clientY - previousMousePosition.y;

      cameraRotation.theta -= deltaX * 0.01;
      cameraRotation.phi -= deltaY * 0.01;
      cameraRotation.phi = Math.max(0.1, Math.min(Math.PI - 0.1, cameraRotation.phi));

      updateCameraPosition();
      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e) => {
      e.preventDefault();
      cameraDistance += e.deltaY * 0.01;
      cameraDistance = Math.max(2, Math.min(50, cameraDistance));
      updateCameraPosition();
    };

    renderer.domElement.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    renderer.domElement.addEventListener('wheel', onWheel);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!containerRef.current) return;
      const width = containerRef.current.clientWidth;
      const height = containerRef.current.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      renderer.domElement.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      renderer.domElement.removeEventListener('wheel', onWheel);
      if (containerRef.current && renderer.domElement) {
        containerRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  const parseOBJ = (text, mtlText = null) => {
    const vertices = [];
    const faces = [];
    const normals = [];
    const uvs = [];
    const colors = [];
    const materials = {};
    let currentMaterial = null;
    const faceMaterials = [];
    let hasVertexColors = false;

    // Parse MTL if provided
    if (mtlText) {
      const mtlLines = mtlText.split('\n');
      let currentMtlName = null;
      
      for (const line of mtlLines) {
        const parts = line.trim().split(/\s+/);
        if (parts[0] === 'newmtl') {
          currentMtlName = parts[1];
          materials[currentMtlName] = { color: new THREE.Color(0xcccccc) };
        } else if (parts[0] === 'Kd' && currentMtlName) {
          materials[currentMtlName].color = new THREE.Color(
            parseFloat(parts[1]),
            parseFloat(parts[2]),
            parseFloat(parts[3])
          );
        }
      }
    }

    const lines = text.split('\n');
    
    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      
      if (parts[0] === 'v') {
        vertices.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
        // Check if vertex has color data (r g b after x y z)
        if (parts.length >= 7) {
          colors.push(parseFloat(parts[4]), parseFloat(parts[5]), parseFloat(parts[6]));
          hasVertexColors = true;
        } else if (hasVertexColors) {
          colors.push(1, 1, 1);
        }
      } else if (parts[0] === 'vn') {
        normals.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
      } else if (parts[0] === 'vt') {
        uvs.push(parseFloat(parts[1]), parseFloat(parts[2]));
      } else if (parts[0] === 'usemtl') {
        currentMaterial = parts[1];
      } else if (parts[0] === 'f') {
        const startIndex = faces.length / 3;
        for (let i = 1; i <= 3; i++) {
          const indices = parts[i].split('/');
          faces.push(parseInt(indices[0]) - 1);
        }
        if (currentMaterial && materials[currentMaterial]) {
          faceMaterials.push({ index: startIndex, material: currentMaterial });
        }
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    
    // Apply vertex colors if available
    if (hasVertexColors && colors.length > 0) {
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    }
    
    // Apply material colors to vertices if MTL materials exist
    if (!hasVertexColors && Object.keys(materials).length > 0 && faceMaterials.length > 0) {
      const vertexColors = new Float32Array(vertices.length);
      vertexColors.fill(0.8); // Default gray
      
      for (const fm of faceMaterials) {
        const mat = materials[fm.material];
        if (mat) {
          const faceIndex = fm.index * 3;
          for (let i = 0; i < 3; i++) {
            const vertexIndex = faces[faceIndex + i];
            vertexColors[vertexIndex * 3] = mat.color.r;
            vertexColors[vertexIndex * 3 + 1] = mat.color.g;
            vertexColors[vertexIndex * 3 + 2] = mat.color.b;
          }
        }
      }
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(vertexColors, 3));
      hasVertexColors = true;
    }
    
    geometry.setIndex(faces);
    geometry.computeVertexNormals();

    return { geometry, hasVertexColors };
  };

  const loadOBJFromURL = async (url) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch model: ${response.statusText}`);
      }
      
      const text = await response.text();
      const { geometry, hasVertexColors } = parseOBJ(text);

      // Remove old model if exists
      if (modelRef.current) {
        sceneRef.current.remove(modelRef.current);
        modelRef.current.geometry.dispose();
        modelRef.current.material.dispose();
      }

      // Create new model with appropriate material
      const material = new THREE.MeshPhongMaterial({
        color: hasVertexColors ? 0xffffff : 0x00ffff,
        shininess: 30,
        flatShading: false,
        vertexColors: hasVertexColors
      });
      const mesh = new THREE.Mesh(geometry, material);

      // Center and scale the model
      geometry.computeBoundingBox();
      const bbox = geometry.boundingBox;
      const center = new THREE.Vector3();
      bbox.getCenter(center);
      
      // Move geometry to center at origin
      geometry.translate(-center.x, -center.y, -center.z);
      
      // Recompute bounding box after translation
      geometry.computeBoundingBox();
      const size = new THREE.Vector3();
      geometry.boundingBox.getSize(size);
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 4 / maxDim;
      mesh.scale.setScalar(scale);
      
      // Position mesh slightly above the grid
      mesh.position.set(0, size.y * scale * 0.5, 0);

      sceneRef.current.add(mesh);
      modelRef.current = mesh;
      setHasModel(true);
      setIsLoading(false);
    } catch (err) {
      setError('Failed to load OBJ file from backend.');
      setIsLoading(false);
      console.error(err);
    }
  };

  // Load model when modelUrl prop changes
  useEffect(() => {
    if (modelUrl && sceneRef.current) {
      loadOBJFromURL(modelUrl);
    }
  }, [modelUrl]);

  return (
    <div className="relative w-full h-full min-h-[400px] bg-card rounded-lg border border-border overflow-hidden">
      {/* 3D Canvas Container */}
      <div ref={containerRef} className="absolute inset-0" />

      {/* Placeholder - Show when no model URL provided */}
      {!modelUrl && !isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <Box className="w-24 h-24 text-primary mb-4 animate-pulse" />
          <p className="text-muted-foreground text-lg">3D Preview</p>
          <p className="text-muted-foreground/60 text-sm mt-2">Waiting for model...</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="text-center">
            <Box className="w-16 h-16 text-primary mb-2 animate-spin mx-auto" />
            <p className="text-muted-foreground">Loading model...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-destructive/90 text-destructive-foreground px-4 py-2 rounded-md text-sm">
          {error}
        </div>
      )}

      {/* Corner indicators */}
      <div className="absolute top-4 left-4 flex items-center gap-2 text-xs text-muted-foreground bg-background/50 backdrop-blur-sm px-2 py-1 rounded">
        <Grid3x3 className="w-4 h-4" />
        <span>Viewport</span>
      </div>

      {/* Controls hint */}
      {hasModel && (
        <div className="absolute bottom-4 left-4 text-xs text-muted-foreground bg-background/50 backdrop-blur-sm px-2 py-1 rounded">
          Drag to rotate • Scroll to zoom
        </div>
      )}
    </div>
  );
};