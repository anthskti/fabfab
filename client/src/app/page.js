"use client";
import { useState, Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stage, useFBX } from "@react-three/drei";
import axios from "axios";

// Component to load the generated model
function Model({ url }) {
  const fbx = useFBX(url);
  return <primitive object={fbx} />;
}

export default function Home() {
  const [file, setFile] = useState(null);
  const [modelUrl, setModelUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dims, setDims] = useState({ w: 1, h: 1, d: 1 });

  const handleGenerate = async () => {
    if (!file) return alert("Upload an image first!");
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("width", dims.l);
    formData.append("height", dims.w);
    formData.append("depth", dims.h);

    try {
      // Assuming backend is on port 8000
      const res = await axios.post("http://localhost:8000/create-model", formData, {
        responseType: "blob", // Important for receiving files
      });

      // Create a local URL for the received FBX blob
      const url = URL.createObjectURL(res.data);
      setModelUrl(url);
    } catch (err) {
      console.error(err);
      alert("Generation failed (Check backend console)");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen text-black">
      {/* SIDEBAR */}
      <div className="bg-white p-5">
        <h2 className="text-3xl font-bold">fabfab</h2>
        
        <div className="mb-4">
          <label className="p-1">Reference Image</label>
          <input className="p-1 font-semibold border rounded" type="file" onChange={(e) => setFile(e.target.files[0])} />
        </div>

        <div className="flex flex-col gap-4 mb-20">
          <div className="flex gap-3">
            Length
            <input type="number" placeholder="1" onChange={e=>setDims({...dims, l: e.target.value})} />
            <span>meter(s)</span>
          </div>
          <div className="flex gap-3">
            Width
            <input type="number" placeholder="1" onChange={e=>setDims({...dims, w: e.target.value})} />
            <span>meter(s)</span>
          </div>
          <div className="flex gap-3">
            Height
            <input type="number" placeholder="1" onChange={e=>setDims({...dims, h: e.target.value})} />
            <span>meter(s)</span>
          </div>
        </div>

        <button 
          onClick={handleGenerate} 
          disabled={loading}
          className="w-full p-3 text-white bg-black hover:bg-zinc-500 rounded-2xl transition-colors duration-300"
        >
          {loading ? "Generating (20s)..." : "Generate 3D Asset"}
        </button>
      </div>

      {/* 3D VIEWER */}
      <div className="flex flex-1 bg-[#e0e0e0]">
        <Canvas shadows camera={{ position: [0, 0, 4], fov: 50 }}>
          <Suspense fallback={null}>
            <Stage environment="city" intensity={0.6}>
              {modelUrl && <Model url={modelUrl} />}
            </Stage>
          </Suspense>
          <OrbitControls makeDefault />
        </Canvas>
      </div>
    </div>
  );
}