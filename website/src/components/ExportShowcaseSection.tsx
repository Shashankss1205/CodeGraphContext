import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileImage, Download, Terminal, Palette } from "lucide-react";

const exportFormats = [
  {
    format: "PNG",
    description: "High-quality raster images perfect for documentation",
    command: "cgc export graph.png --dpi 300 --layout spring",
    color: "bg-blue-500/10 border-blue-500/20 text-blue-400"
  },
  {
    format: "SVG", 
    description: "Scalable vector graphics for presentations",
    command: "cgc export graph.svg --format svg --layout circular",
    color: "bg-green-500/10 border-green-500/20 text-green-400"
  },
  {
    format: "PDF",
    description: "Professional documents and reports",
    command: "cgc export report.pdf --format pdf --width 2400 --height 1600",
    color: "bg-red-500/10 border-red-500/20 text-red-400"
  },
  {
    format: "HTML",
    description: "Interactive visualizations with zoom and pan",
    command: "cgc export interactive.html --format html --include-deps",
    color: "bg-purple-500/10 border-purple-500/20 text-purple-400"
  }
];

const layoutAlgorithms = [
  { name: "spring", description: "Force-directed layout (default)" },
  { name: "circular", description: "Nodes arranged in a circle" },
  { name: "kamada_kawai", description: "Kamada-Kawai force-directed" },
  { name: "spectral", description: "Spectral layout using graph Laplacian" }
];

const ExportShowcaseSection = () => {
  return (
    <section className="py-24 px-4 bg-gradient-to-b from-background to-muted/30">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
            <FileImage className="h-5 w-5 text-primary" />
            <span className="text-primary font-medium">Export & Visualization</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-primary bg-clip-text text-transparent">
            Export Beautiful Graph Visualizations
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Generate stunning code graph visualizations in multiple formats using our Python CLI tools
          </p>
        </div>

        <Tabs defaultValue="formats" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="formats">Export Formats</TabsTrigger>
            <TabsTrigger value="cli">CLI Commands</TabsTrigger>
            <TabsTrigger value="layouts">Layout Options</TabsTrigger>
          </TabsList>

          <TabsContent value="formats">
            <div className="grid md:grid-cols-2 gap-6">
              {exportFormats.map((format, index) => (
                <Card 
                  key={format.format}
                  className="bg-gradient-card border-border/50 hover:border-primary/30 transition-smooth group animate-float-up"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between mb-4">
                      <Badge className={format.color}>
                        {format.format}
                      </Badge>
                      <FileImage className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <CardTitle className="text-lg">{format.format} Export</CardTitle>
                    <CardDescription>{format.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="code-block bg-muted/50 rounded-lg p-4 font-mono text-sm">
                      <span className="text-green-400">$</span> {format.command}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="cli">
            <Card className="bg-gradient-card border-border/50">
              <CardHeader>
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 rounded-xl bg-primary/10 border border-primary/20">
                    <Terminal className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <CardTitle>Command Line Interface</CardTitle>
                    <CardDescription>
                      Full control over export parameters via CLI
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-3 text-lg">Basic Export</h4>
                  <div className="code-block bg-muted/50 rounded-lg p-4 font-mono text-sm mb-2">
                    <span className="text-green-400">$</span> cgc export my_graph.png
                  </div>
                  <p className="text-sm text-muted-foreground">Exports a PNG image with default settings</p>
                </div>

                <div>
                  <h4 className="font-semibold mb-3 text-lg">Advanced Options</h4>
                  <div className="code-block bg-muted/50 rounded-lg p-4 font-mono text-sm mb-2">
                    <span className="text-green-400">$</span> cgc export detailed_graph.svg \<br />
                    <span className="ml-4">--format svg \</span><br />
                    <span className="ml-4">--layout kamada_kawai \</span><br />
                    <span className="ml-4">--max-nodes 500 \</span><br />
                    <span className="ml-4">--width 1600 \</span><br />
                    <span className="ml-4">--height 1200 \</span><br />
                    <span className="ml-4">--dpi 300</span>
                  </div>
                  <p className="text-sm text-muted-foreground">High-quality SVG with custom layout and dimensions</p>
                </div>

                <div>
                  <h4 className="font-semibold mb-3 text-lg">Repository Filtering</h4>
                  <div className="code-block bg-muted/50 rounded-lg p-4 font-mono text-sm mb-2">
                    <span className="text-green-400">$</span> cgc export frontend_only.png \<br />
                    <span className="ml-4">--repository "src/frontend" \</span><br />
                    <span className="ml-4">--exclude-deps</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Export only specific parts of your codebase</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="layouts">
            <div className="grid md:grid-cols-2 gap-6">
              {layoutAlgorithms.map((layout, index) => (
                <Card 
                  key={layout.name}
                  className="bg-gradient-card border-border/50 hover:border-primary/30 transition-smooth group animate-float-up"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <CardHeader>
                    <div className="flex items-center gap-4 mb-4">
                      <div className="p-3 rounded-xl bg-accent/10 border border-accent/20">
                        <Palette className="h-6 w-6 text-accent" />
                      </div>
                      <div>
                        <CardTitle className="text-lg capitalize">{layout.name}</CardTitle>
                        <CardDescription>{layout.description}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="code-block bg-muted/50 rounded-lg p-4 font-mono text-sm">
                      <span className="text-green-400">$</span> cgc export graph.png --layout {layout.name}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* Installation CTA */}
        <div className="text-center mt-16">
          <Card className="bg-gradient-card border-primary/20 max-w-2xl mx-auto">
            <CardContent className="pt-8">
              <h3 className="text-2xl font-bold mb-4">Ready to Export Your Code Graphs?</h3>
              <p className="text-muted-foreground mb-6">
                Install the visualization dependencies and start creating beautiful code visualizations
              </p>
              <div className="code-block bg-muted/50 rounded-lg p-4 font-mono text-sm mb-6">
                <span className="text-green-400">$</span> pip install 'codegraphcontext[visualization]'
              </div>
              <Button className="bg-primary hover:bg-primary/90">
                <Download className="h-4 w-4 mr-2" />
                Get Started with Export
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default ExportShowcaseSection;