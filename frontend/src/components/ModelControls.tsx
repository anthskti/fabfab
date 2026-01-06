import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Download, Settings2 } from "lucide-react";
import { toast } from "sonner";
import modelAPI from '../routes.js';
export const ModelControls = () => {
  const [size, setSize] = useState([1]);
  const [quality, setQuality] = useState([80]);
  const [fileSize, setFileSize] = useState([1]);
  const handleDownload = () => {
    toast.success("Model downloaded successfully!");
  };
  return <div className="space-y-6 p-6 bg-card rounded-lg border border-border">
      <div className="flex items-center gap-2 mb-6">
        <Settings2 className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-semibold text-foreground">Model Settings</h3>
      </div>

      <div className="space-y-6">
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <Label className="text-foreground">Model Size</Label>
            <span className="text-sm text-muted-foreground">{size[0]}x</span>
          </div>
          <Slider value={size} onValueChange={setSize} min={0.1} max={5} step={0.1} className="[&_[role=slider]]:bg-primary [&_[role=slider]]:border-primary [&_[role=slider]]:shadow-glow-primary" />
        </div>

        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <Label className="text-foreground">Quality</Label>
            <span className="text-sm text-muted-foreground">{quality[0]}%</span>
          </div>
          <Slider value={quality} onValueChange={setQuality} min={10} max={100} step={10} className="[&_[role=slider]]:bg-primary [&_[role=slider]]:border-primary [&_[role=slider]]:shadow-glow-primary" />
        </div>

        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <Label className="text-foreground">File Size Target</Label>
            <span className="text-sm text-muted-foreground">{fileSize[0]} MB</span>
          </div>
          <Slider value={fileSize} onValueChange={setFileSize} min={0.1} max={10} step={0.1} className="[&_[role=slider]]:bg-primary [&_[role=slider]]:border-primary [&_[role=slider]]:shadow-glow-primary" />
        </div>
      </div>

      <Button onClick={handleDownload} className="w-full hover:opacity-90 text-accent-foreground font-semibold py-5 shadow-glow-accent transition-all bg-[285a4b]">
        <Download className="w-5 h-5 mr-2" />
        Download OBJ
      </Button>
    </div>;
};