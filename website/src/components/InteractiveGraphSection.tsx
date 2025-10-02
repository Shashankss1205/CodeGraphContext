import React from 'react';
import GraphVisualization from '@/components/GraphVisualization';

const InteractiveGraphSection: React.FC = () => {
  return (
    <section className="py-20 px-4 bg-gradient-to-b from-secondary/10 to-background">
      <div className="container mx-auto max-w-7xl">
        <div className="text-center mb-16">
          <h2 className="text-2xl sm:text-3xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-primary via-primary to-accent bg-clip-text text-transparent">
            Interactive Graph Visualization
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-12">
            Explore your code graph with our interactive visualization. Pan, zoom, and export in multiple formats.
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          <GraphVisualization 
            width={1000}
            height={700}
            title="CodeGraphContext Sample Visualization"
            className="mx-auto"
          />
        </div>

        <div className="text-center mt-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">Export as Images</h3>
              <p className="text-muted-foreground text-sm">
                Export your graphs as high-quality PNG or JPEG images with customizable resolution and quality settings.
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">PDF Documents</h3>
              <p className="text-muted-foreground text-sm">
                Generate professional PDF documents of your code graphs, perfect for reports and documentation.
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-2">Customizable Settings</h3>
              <p className="text-muted-foreground text-sm">
                Fine-tune export settings including scale, quality, labels, and visual elements to match your needs.
              </p>
            </div>
          </div>

          <div className="mt-12 p-6 bg-card/50 rounded-lg border border-border/50 max-w-2xl mx-auto">
            <h4 className="text-lg font-semibold mb-4 text-center">How to Export</h4>
            <div className="space-y-3 text-sm text-muted-foreground">
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center text-primary font-medium text-xs">1</span>
                <span>Interact with the graph above - pan, zoom, and arrange nodes as desired</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center text-primary font-medium text-xs">2</span>
                <span>Click the "Export" button to choose your format (PNG, JPEG, or PDF)</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center text-primary font-medium text-xs">3</span>
                <span>Use "Export Settings" for advanced customization like resolution and quality</span>
              </div>
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center text-primary font-medium text-xs">4</span>
                <span>Your file will be automatically downloaded to your device</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default InteractiveGraphSection;