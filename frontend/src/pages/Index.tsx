import { useState } from "react";
import { GenerationForm } from "@/components/GenerationForm";
import { ModelViewer } from "@/components/ModelViewer";
import { ModelControls } from "@/components/ModelControls";
import { Box } from "lucide-react";
const Index = () => {
  const [isModelGenerated, setIsModelGenerated] = useState(false);
  return <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-primary rounded-lg shadow-glow-primary">
              <Box className="w-6 h-6 text-primary-foreground" />
            </div>
            <h1 className="font-bold text-gradient-primary text-[27594a] text-[#27594a]">
              3D Model Generator
            </h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-12 space-y-4">
            <h2 className="text-4xl font-bold text-gradient-primary leading-tight md:text-[#  28594a] bg-inherit text-[#28594a]">
              Create 3D Models from Text & Images
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Transform your ideas into high-quality 3D models instantly. Powered by AI.
            </p>
          </div>

          {/* Main Grid */}
          <div className={`grid gap-6 ${isModelGenerated ? 'lg:grid-cols-3' : 'lg:grid-cols-2 max-w-5xl mx-auto'}`}>
            {/* Left Column - Input Form */}
            <div className="lg:col-span-1">
              <div className="sticky top-24">
                <GenerationForm onModelGenerated={() => setIsModelGenerated(true)} />
              </div>
            </div>

            {/* Middle Column - 3D Viewer */}
            <div className="lg:col-span-1">
              <ModelViewer />
            </div>

            {/* Right Column - Controls */}
            {isModelGenerated && <div className="lg:col-span-1">
                <div className="sticky top-24">
                  <ModelControls />
                </div>
              </div>}
          </div>
        </div>
      </main>
    </div>;
};
export default Index;