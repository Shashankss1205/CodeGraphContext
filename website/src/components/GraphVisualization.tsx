import React, { useRef, useState, useCallback, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Download, 
  FileImage, 
  FileType, 
  Settings,
  ZoomIn,
  ZoomOut,
  RotateCcw
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { exportElement, ExportFormat, ExportOptions, getOptimalExportSettings } from '@/utils/exportUtils';
import { toast } from '@/hooks/use-toast';

// Define interfaces for graph data
interface GraphNode {
  id: string;
  name: string;
  type: 'function' | 'class' | 'module' | 'variable';
  size: number;
  color: string;
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
}

interface GraphLink {
  source: string;
  target: string;
  type: 'calls' | 'imports' | 'inherits' | 'uses';
  value: number;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface GraphVisualizationProps {
  data?: GraphData;
  width?: number;
  height?: number;
  title?: string;
  className?: string;
}

// Sample data for demonstration
const sampleData: GraphData = {
  nodes: [
    { id: 'main', name: 'main.py', type: 'module', size: 20, color: '#8b5cf6' },
    { id: 'utils', name: 'utils.py', type: 'module', size: 15, color: '#06b6d4' },
    { id: 'models', name: 'models.py', type: 'module', size: 18, color: '#10b981' },
    { id: 'process_data', name: 'process_data()', type: 'function', size: 12, color: '#f59e0b' },
    { id: 'DataProcessor', name: 'DataProcessor', type: 'class', size: 16, color: '#ef4444' },
    { id: 'validate_input', name: 'validate_input()', type: 'function', size: 10, color: '#f59e0b' },
    { id: 'BaseModel', name: 'BaseModel', type: 'class', size: 14, color: '#ef4444' },
    { id: 'UserModel', name: 'UserModel', type: 'class', size: 12, color: '#ef4444' },
  ],
  links: [
    { source: 'main', target: 'utils', type: 'imports', value: 1 },
    { source: 'main', target: 'models', type: 'imports', value: 1 },
    { source: 'main', target: 'process_data', type: 'calls', value: 2 },
    { source: 'process_data', target: 'DataProcessor', type: 'uses', value: 1 },
    { source: 'process_data', target: 'validate_input', type: 'calls', value: 1 },
    { source: 'UserModel', target: 'BaseModel', type: 'inherits', value: 1 },
    { source: 'DataProcessor', target: 'validate_input', type: 'calls', value: 1 },
  ]
};

const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  data = sampleData,
  width = 800,
  height = 600,
  title = "Code Graph Visualization",
  className = ""
}) => {
  const graphRef = useRef<any>();
  const containerRef = useRef<HTMLDivElement>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: ExportFormat.PNG,
    filename: 'code-graph',
    quality: 0.9,
    scale: 2,
    backgroundColor: '#0f0f23'
  });

  // Graph visualization settings
  const [graphSettings, setGraphSettings] = useState({
    nodeSize: 1,
    linkWidth: 1,
    linkOpacity: 0.6,
    showLabels: true,
    enablePhysics: true,
  });

  const handleExport = useCallback(async (format?: ExportFormat) => {
    if (!containerRef.current) {
      toast({
        title: "Export Failed",
        description: "Graph container not found",
        variant: "destructive",
      });
      return;
    }

    setIsExporting(true);
    
    try {
      const finalOptions = {
        ...exportOptions,
        ...(format && { format }),
        ...getOptimalExportSettings(containerRef.current, format || exportOptions.format),
      };

      await exportElement(containerRef.current, finalOptions);
      
      toast({
        title: "Export Successful",
        description: `Graph exported as ${(format || exportOptions.format).toUpperCase()}`,
      });
      
      setExportDialogOpen(false);
    } catch (error) {
      toast({
        title: "Export Failed", 
        description: error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  }, [exportOptions]);

  const handleZoomIn = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 1.2);
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 0.8);
    }
  }, []);

  const handleReset = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoom(1);
      graphRef.current.centerAt(0, 0, 1000);
    }
  }, []);

  const nodeColor = useCallback((node: GraphNode) => {
    return node.color;
  }, []);

  const nodeSize = useCallback((node: GraphNode) => {
    return node.size * graphSettings.nodeSize;
  }, [graphSettings.nodeSize]);

  const linkColor = useCallback((link: GraphLink) => {
    const colors = {
      calls: '#8b5cf6',
      imports: '#06b6d4', 
      inherits: '#ef4444',
      uses: '#10b981'
    };
    return colors[link.type] || '#64748b';
  }, []);

  const linkWidth = useCallback((link: GraphLink) => {
    return link.value * graphSettings.linkWidth;
  }, [graphSettings.linkWidth]);

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-xl font-semibold">{title}</CardTitle>
            <Badge variant="outline" className="text-xs">
              {data.nodes.length} nodes, {data.links.length} edges
            </Badge>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Graph Controls */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomIn}
              className="h-8 w-8 p-0"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomOut}
              className="h-8 w-8 p-0"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="h-8 w-8 p-0"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>

            {/* Export Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" disabled={isExporting}>
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleExport(ExportFormat.PNG)}>
                  <FileImage className="h-4 w-4 mr-2" />
                  PNG Image
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport(ExportFormat.JPEG)}>
                  <FileImage className="h-4 w-4 mr-2" />
                  JPEG Image
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport(ExportFormat.PDF)}>
                  <FileType className="h-4 w-4 mr-2" />
                  PDF Document
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
                  <DialogTrigger asChild>
                    <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                      <Settings className="h-4 w-4 mr-2" />
                      Export Settings...
                    </DropdownMenuItem>
                  </DialogTrigger>
                </Dialog>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div 
          ref={containerRef}
          className="relative border rounded-lg overflow-hidden bg-background"
        >
          <ForceGraph2D
            ref={graphRef}
            graphData={data}
            width={width}
            height={height}
            backgroundColor="#0f0f23"
            nodeColor={nodeColor}
            nodeVal={nodeSize}
            nodeLabel="name"
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              if (!graphSettings.showLabels || globalScale < 0.5) return;
              
              const label = node.name;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              ctx.textAlign = 'center';
              ctx.textBaseline = 'top';
              ctx.fillStyle = '#ffffff';
              
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);
              
              ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
              ctx.fillRect(
                node.x - bckgDimensions[0] / 2,
                node.y + nodeSize(node) + 2,
                bckgDimensions[0],
                bckgDimensions[1]
              );
              
              ctx.fillStyle = '#ffffff';
              ctx.fillText(label, node.x, node.y + nodeSize(node) + 4);
            }}
            linkColor={linkColor}
            linkWidth={linkWidth}
            linkOpacity={graphSettings.linkOpacity}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            enableNodeDrag={true}
            enablePanInteraction={true}
            enableZoomInteraction={true}
            cooldownTicks={graphSettings.enablePhysics ? 100 : 0}
            onEngineStop={() => graphRef.current?.zoom(0.8)}
          />
        </div>
      </CardContent>

      {/* Export Settings Dialog */}
      <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Export Settings</DialogTitle>
            <DialogDescription>
              Configure the export options for your graph visualization.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="filename" className="text-right">
                Filename
              </Label>
              <Input
                id="filename"
                value={exportOptions.filename}
                onChange={(e) => setExportOptions(prev => ({ ...prev, filename: e.target.value }))}
                className="col-span-3"
              />
            </div>
            
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="scale" className="text-right">
                Scale
              </Label>
              <div className="col-span-3">
                <Slider
                  value={[exportOptions.scale || 2]}
                  onValueChange={(value) => setExportOptions(prev => ({ ...prev, scale: value[0] }))}
                  max={4}
                  min={1}
                  step={0.5}
                  className="w-full"
                />
                <div className="text-xs text-muted-foreground mt-1">
                  {exportOptions.scale}x ({(width * (exportOptions.scale || 2))} × {(height * (exportOptions.scale || 2))} px)
                </div>
              </div>
            </div>

            {exportOptions.format === ExportFormat.JPEG && (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="quality" className="text-right">
                  Quality
                </Label>
                <div className="col-span-3">
                  <Slider
                    value={[exportOptions.quality || 0.9]}
                    onValueChange={(value) => setExportOptions(prev => ({ ...prev, quality: value[0] }))}
                    max={1}
                    min={0.1}
                    step={0.1}
                    className="w-full"
                  />
                  <div className="text-xs text-muted-foreground mt-1">
                    {Math.round((exportOptions.quality || 0.9) * 100)}%
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="showLabels" className="text-right">
                Show Labels
              </Label>
              <Switch
                id="showLabels"
                checked={graphSettings.showLabels}
                onCheckedChange={(checked) => setGraphSettings(prev => ({ ...prev, showLabels: checked }))}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setExportDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => handleExport()} disabled={isExporting}>
              {isExporting ? "Exporting..." : "Export"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default GraphVisualization;