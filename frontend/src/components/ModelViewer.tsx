import { Box, Grid3x3 } from "lucide-react";

export const ModelViewer = () => {
  return (
    <div className="relative w-full h-full min-h-[400px] bg-card rounded-lg border border-border overflow-hidden">
      {/* Grid background */}
      <div className="absolute inset-0 opacity-20">
        <div className="w-full h-full" style={{
          backgroundImage: `
            linear-gradient(hsl(180 100% 50% / 0.1) 1px, transparent 1px),
            linear-gradient(90deg, hsl(180 100% 50% / 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px'
        }} />
      </div>

      {/* Placeholder content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <Box className="w-24 h-24 text-primary mb-4 animate-pulse" />
        <p className="text-muted-foreground text-lg">3D Preview</p>
        <p className="text-muted-foreground/60 text-sm mt-2">Your model will appear here</p>
      </div>

      {/* Corner indicators */}
      <div className="absolute top-4 left-4 flex items-center gap-2 text-xs text-muted-foreground">
        <Grid3x3 className="w-4 h-4" />
        <span>Viewport</span>
      </div>
    </div>
  );
};
