import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, Sparkles } from "lucide-react";
import { toast } from "sonner";

interface GenerationFormProps {
  onModelGenerated: () => void;
}

export const GenerationForm = ({
  onModelGenerated
}: GenerationFormProps) => {
  const [prompt, setPrompt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error("Please enter a prompt");
      return;
    }

    setIsGenerating(true);
    toast.info("Generating 3D model...");

    // Simulate generation delay
    setTimeout(() => {
      setIsGenerating(false);
      setHasGenerated(true);
      toast.success("3D model generated successfully!");
      onModelGenerated();
    }, 3000);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="prompt" className="text-foreground text-lg font-medium">
          Describe Your 3D Model
        </Label>
        <Textarea
          id="prompt"
          placeholder="E.g., A futuristic sports car with neon lights and aerodynamic design..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          className="min-h-[120px] bg-card border-border text-foreground placeholder:text-muted-foreground resize-none transition-all focus:border-primary focus:shadow-glow-primary"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="image" className="text-foreground text-lg font-medium">
          Reference Image (Optional)
        </Label>
        <div className="relative">
          <Input
            id="image"
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            className="hidden"
          />
          <label
            htmlFor="image"
            className="flex items-center justify-center gap-2 p-8 border-2 border-dashed border-border rounded-lg cursor-pointer hover:border-primary transition-all bg-card/50 hover:bg-card group"
          >
            {imagePreview ? (
              <div className="relative w-full h-48">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-full h-full object-contain rounded"
                />
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" />
                <span className="text-muted-foreground group-hover:text-foreground transition-colors">
                  Click to upload an image
                </span>
              </div>
            )}
          </label>
        </div>
      </div>

      <Button
        onClick={handleGenerate}
        disabled={isGenerating}
        className="w-full hover:opacity-90 text-primary-foreground font-semibold py-6 text-lg shadow-glow-primary transition-all bg-[285a4b]"
      >
        {isGenerating ? (
          <>
            <Sparkles className="w-5 h-5 mr-2 animate-spin" />
            Generating...
          </>
        ) : hasGenerated ? (
          <>
            <Sparkles className="w-5 h-5 mr-2" />
            Generate Again
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5 mr-2" />
            Generate 3D Model
          </>
        )}
      </Button>
    </div>
  );
};