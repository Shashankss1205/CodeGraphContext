import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Download, FileImage, FileType, Settings } from 'lucide-react';
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
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { exportElement, ExportFormat, ExportOptions, getOptimalExportSettings } from '@/utils/exportUtils';
import { toast } from '@/hooks/use-toast';

interface ExportButtonProps {
  targetElementRef: React.RefObject<HTMLElement>;
  filename?: string;
  className?: string;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'sm' | 'default' | 'lg';
}

const ExportButton: React.FC<ExportButtonProps> = ({
  targetElementRef,
  filename = 'graph-export',
  className = '',
  variant = 'outline',
  size = 'sm'
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: ExportFormat.PNG,
    filename,
    quality: 0.9,
    scale: 2,
    backgroundColor: '#0f0f23'
  });

  const handleExport = async (format?: ExportFormat) => {
    if (!targetElementRef.current) {
      toast({
        title: "Export Failed",
        description: "Target element not found",
        variant: "destructive",
      });
      return;
    }

    setIsExporting(true);
    
    try {
      const finalOptions = {
        ...exportOptions,
        ...(format && { format }),
        ...getOptimalExportSettings(targetElementRef.current, format || exportOptions.format),
      };

      await exportElement(targetElementRef.current, finalOptions);
      
      toast({
        title: "Export Successful",
        description: `File exported as ${(format || exportOptions.format).toUpperCase()}`,
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
  };

  const formatIcons = {
    [ExportFormat.PNG]: FileImage,
    [ExportFormat.JPEG]: FileImage,
    [ExportFormat.PDF]: FileType,
    [ExportFormat.SVG]: FileType,
  };

  const formatLabels = {
    [ExportFormat.PNG]: 'PNG Image',
    [ExportFormat.JPEG]: 'JPEG Image', 
    [ExportFormat.PDF]: 'PDF Document',
    [ExportFormat.SVG]: 'SVG Vector',
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant={variant} size={size} disabled={isExporting} className={className}>
            <Download className="h-4 w-4 mr-2" />
            {isExporting ? 'Exporting...' : 'Export'}
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

      {/* Export Settings Dialog */}
      <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Export Settings</DialogTitle>
            <DialogDescription>
              Configure the export options for your visualization.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="format" className="text-right">
                Format
              </Label>
              <div className="col-span-3">
                <Select
                  value={exportOptions.format}
                  onValueChange={(value) => setExportOptions(prev => ({ ...prev, format: value as ExportFormat }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(ExportFormat).map((format) => {
                      const Icon = formatIcons[format];
                      return (
                        <SelectItem key={format} value={format}>
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4" />
                            {formatLabels[format]}
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="filename" className="text-right">
                Filename
              </Label>
              <Input
                id="filename"
                value={exportOptions.filename}
                onChange={(e) => setExportOptions(prev => ({ ...prev, filename: e.target.value }))}
                className="col-span-3"
                placeholder="Enter filename without extension"
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
                <div className="text-xs text-muted-foreground mt-1 flex items-center justify-between">
                  <span>{exportOptions.scale}x resolution</span>
                  <Badge variant="outline" className="text-xs">
                    Higher = Better Quality
                  </Badge>
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
                    {Math.round((exportOptions.quality || 0.9) * 100)}% quality
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="backgroundColor" className="text-right">
                Background
              </Label>
              <div className="col-span-3">
                <Select
                  value={exportOptions.backgroundColor}
                  onValueChange={(value) => setExportOptions(prev => ({ ...prev, backgroundColor: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="#0f0f23">Dark (Default)</SelectItem>
                    <SelectItem value="#ffffff">White</SelectItem>
                    <SelectItem value="#000000">Black</SelectItem>
                    <SelectItem value="transparent">Transparent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
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
    </>
  );
};

export default ExportButton;