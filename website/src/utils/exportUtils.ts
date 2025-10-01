import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

export enum ExportFormat {
  PNG = 'png',
  JPEG = 'jpeg',
  PDF = 'pdf',
  SVG = 'svg'
}

export interface ExportOptions {
  format: ExportFormat;
  filename?: string;
  quality?: number; // 0.1 to 1.0 for JPEG
  scale?: number; // Scale factor for resolution
  backgroundColor?: string;
}

/**
 * Exports an HTML element as an image or PDF
 * @param element - The HTML element to export
 * @param options - Export configuration options
 */
export const exportElement = async (
  element: HTMLElement,
  options: ExportOptions
): Promise<void> => {
  const {
    format,
    filename = `graph-export-${Date.now()}`,
    quality = 0.9,
    scale = 2,
    backgroundColor = '#0f0f23'
  } = options;

  try {
    // Configure html2canvas options
    const canvas = await html2canvas(element, {
      scale: scale,
      backgroundColor: backgroundColor,
      useCORS: true,
      allowTaint: true,
      logging: false,
      width: element.offsetWidth,
      height: element.offsetHeight,
    });

    switch (format) {
      case ExportFormat.PNG:
        downloadCanvas(canvas, `${filename}.png`, 'image/png');
        break;
      
      case ExportFormat.JPEG:
        downloadCanvas(canvas, `${filename}.jpg`, 'image/jpeg', quality);
        break;
      
      case ExportFormat.PDF:
        await exportToPDF(canvas, `${filename}.pdf`);
        break;
      
      case ExportFormat.SVG:
        // Note: SVG export would require a different approach since html2canvas generates a canvas
        // For now, we'll export as PNG and suggest using SVG-based graph libraries for true SVG export
        console.warn('SVG export not implemented - using PNG instead');
        downloadCanvas(canvas, `${filename}.png`, 'image/png');
        break;
      
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  } catch (error) {
    console.error('Export failed:', error);
    throw new Error(`Failed to export as ${format.toUpperCase()}: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

/**
 * Downloads a canvas as an image file
 */
const downloadCanvas = (
  canvas: HTMLCanvasElement,
  filename: string,
  mimeType: string,
  quality?: number
): void => {
  const link = document.createElement('a');
  link.download = filename;
  link.href = canvas.toDataURL(mimeType, quality);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Exports a canvas to PDF
 */
const exportToPDF = async (canvas: HTMLCanvasElement, filename: string): Promise<void> => {
  const imgData = canvas.toDataURL('image/png');
  
  // Calculate PDF dimensions based on canvas aspect ratio
  const imgWidth = canvas.width;
  const imgHeight = canvas.height;
  const aspectRatio = imgHeight / imgWidth;
  
  // Standard A4 size in mm
  const pdfWidth = 297; // A4 landscape width
  const pdfHeight = 210; // A4 landscape height
  
  // Calculate dimensions to fit the image in PDF while maintaining aspect ratio
  let finalWidth = pdfWidth - 20; // 10mm margin on each side
  let finalHeight = finalWidth * aspectRatio;
  
  // If height is too large, scale down based on height
  if (finalHeight > pdfHeight - 20) {
    finalHeight = pdfHeight - 20;
    finalWidth = finalHeight / aspectRatio;
  }
  
  const pdf = new jsPDF({
    orientation: finalWidth > finalHeight ? 'landscape' : 'portrait',
    unit: 'mm',
    format: 'a4'
  });
  
  // Center the image on the page
  const x = (pdfWidth - finalWidth) / 2;
  const y = (pdfHeight - finalHeight) / 2;
  
  pdf.addImage(imgData, 'PNG', x, y, finalWidth, finalHeight);
  pdf.save(filename);
};

/**
 * Gets the optimal export settings based on the element size and desired format
 */
export const getOptimalExportSettings = (
  element: HTMLElement,
  format: ExportFormat
): Partial<ExportOptions> => {
  const { offsetWidth, offsetHeight } = element;
  
  // Calculate optimal scale based on element size
  let scale = 2; // Default high-DPI scale
  
  if (offsetWidth * offsetHeight > 1000000) { // Very large elements
    scale = 1;
  } else if (offsetWidth * offsetHeight < 100000) { // Small elements
    scale = 3;
  }
  
  return {
    scale,
    quality: format === ExportFormat.JPEG ? 0.9 : undefined,
  };
};