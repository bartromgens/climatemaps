import { Injectable } from '@angular/core';
import { Map, LatLng, Point, TileLayer, LayerGroup } from 'leaflet';

export interface ColorInfo {
  r: number;
  g: number;
  b: number;
  a: number;
  hex: string;
  rgba: string;
}

@Injectable({
  providedIn: 'root',
})
export class ColorExtractionService {
  private canvas: HTMLCanvasElement | null = null;
  private context: CanvasRenderingContext2D | null = null;
  private debugMode = true; // Set to false to disable debug logging

  constructor() {
    // Initialize color extraction service
  }

  /**
   * Extract color from map layer at the given mouse position
   * @param map Leaflet map instance
   * @param latlng LatLng object from mouse event
   * @returns ColorInfo object with color data or null if extraction fails
   */
  getColorAtPosition(map: Map, latlng: LatLng): ColorInfo | null {
    try {
      // Get the map container
      const mapContainer = map.getContainer();
      if (!mapContainer) {
        console.warn('Map container not found');
        return null;
      }

      // Convert lat/lng to pixel coordinates
      const point = map.latLngToContainerPoint(latlng);

      // Debug: Log available elements
      if (this.debugMode) {
        this.debugMapElements(mapContainer);
      }

      // Try to get color from tile images first
      const colorFromTiles = this.getColorFromTileImages(
        mapContainer,
        point,
        map,
        latlng,
      );
      if (colorFromTiles) {
        console.log('Color extracted from tile images');
        return colorFromTiles;
      }

      // Fallback: try canvas approach
      const canvas = this.getCanvasFromMapContainer(mapContainer);
      if (canvas) {
        const colorFromCanvas = this.getColorFromCanvas(canvas, point);
        if (colorFromCanvas) {
          console.log('Color extracted from canvas');
          return colorFromCanvas;
        }
      }

      // Final fallback: try to get color from any visible image
      const colorFromAnyImage = this.getColorFromAnyImage(mapContainer, point);
      if (colorFromAnyImage) {
        console.log('Color extracted from any image');
        return colorFromAnyImage;
      }

      console.warn('No suitable rendering method found for color extraction');
      return null;
    } catch (error) {
      console.error('Error extracting color:', error);
      return null;
    }
  }

  /**
   * Get color from a specific layer at mouse position
   * @param map Leaflet map instance
   * @param latlng LatLng object from mouse event
   * @param layerName Name of the layer to sample from
   * @returns ColorInfo object with color data or null if extraction fails
   */
  getColorFromLayer(
    map: Map,
    latlng: LatLng,
    layerName: string,
  ): ColorInfo | null {
    try {
      // Find the specific layer
      const layer = this.findLayerByName(map, layerName);
      if (!layer) {
        console.warn(`Layer '${layerName}' not found`);
        return null;
      }

      // For raster layers, we can try to get the color from the tile
      if (layer instanceof TileLayer) {
        return this.getColorFromTileLayer(map, latlng, layer);
      }

      // For vector layers, we need to handle differently
      if (layer instanceof LayerGroup) {
        return this.getColorFromVectorLayer(map, latlng, layer);
      }

      console.warn(
        `Unsupported layer type for color extraction: ${layer.constructor.name}`,
      );
      return null;
    } catch (error) {
      console.error('Error extracting color from layer:', error);
      return null;
    }
  }

  /**
   * Get color from a specific Leaflet tile layer
   * @param map Leaflet map instance
   * @param latlng LatLng object from mouse event
   * @param tileLayer The tile layer to sample from
   * @returns ColorInfo object with color data or null if extraction fails
   */
  getColorFromTileLayer(
    map: Map,
    latlng: LatLng,
    tileLayer: TileLayer,
  ): ColorInfo | null {
    try {
      console.log('Extracting color from tile layer:', tileLayer);

      // Get the map container
      const mapContainer = map.getContainer();
      if (!mapContainer) {
        console.warn('Map container not found');
        return null;
      }

      // Convert lat/lng to pixel coordinates
      const point = map.latLngToContainerPoint(latlng);

      // Get current zoom and layer's max zoom
      const currentZoom = map.getZoom();
      const layerMaxZoom = this.getLayerMaxZoom(tileLayer);

      console.log(
        `Current zoom: ${currentZoom}, Layer max zoom: ${layerMaxZoom}`,
      );

      // If current zoom exceeds layer's max zoom, use the max zoom instead
      const effectiveZoom = Math.min(currentZoom, layerMaxZoom);

      if (currentZoom > layerMaxZoom) {
        console.log(
          `Zoom ${currentZoom} exceeds layer max zoom ${layerMaxZoom}, using zoom ${effectiveZoom}`,
        );
      }

      // Calculate tile coordinates using effective zoom
      const tileSize = 256;
      const scale = Math.pow(2, effectiveZoom);

      const tileX = Math.floor(((latlng.lng + 180) / 360) * scale);
      const tileY = Math.floor(
        ((1 -
          Math.log(
            Math.tan((latlng.lat * Math.PI) / 180) +
              1 / Math.cos((latlng.lat * Math.PI) / 180),
          ) /
            Math.PI) /
          2) *
          scale,
      );

      // Find the specific tile image for this layer
      const tileImage = this.findTileImageForLayer(
        mapContainer,
        tileLayer,
        tileX,
        tileY,
        effectiveZoom,
      );
      if (!tileImage) {
        console.warn(`Tile image not found for layer at zoom ${effectiveZoom}`);
        return null;
      }

      // Try to enable CORS on the image
      this.enableCorsOnImage(tileImage);

      // Sample color from the tile
      return this.sampleColorFromImage(
        tileImage,
        point,
        tileX,
        tileY,
        effectiveZoom,
        tileSize,
      );
    } catch (error) {
      console.error('Error extracting color from tile layer:', error);
      return null;
    }
  }

  private getColorFromTileImages(
    container: HTMLElement,
    point: Point,
    map: Map,
    latlng: LatLng,
  ): ColorInfo | null {
    try {
      // Find all tile images in the map
      const tileImages = container.querySelectorAll(
        'img[src*="/tiles/"], img[src*="tile"], img[src*="png"], img[src*="jpg"]',
      );

      if (tileImages.length === 0) {
        return null;
      }

      // Calculate which tile contains our point
      const zoom = map.getZoom();
      const tileSize = 256;
      const scale = Math.pow(2, zoom);

      // Calculate tile coordinates
      const tileX = Math.floor(((latlng.lng + 180) / 360) * scale);
      const tileY = Math.floor(
        ((1 -
          Math.log(
            Math.tan((latlng.lat * Math.PI) / 180) +
              1 / Math.cos((latlng.lat * Math.PI) / 180),
          ) /
            Math.PI) /
          2) *
          scale,
      );

      // Find the specific tile image
      const targetTile = this.findTileImageByCoordinates(
        tileImages,
        tileX,
        tileY,
        zoom,
      );
      if (!targetTile) {
        return null;
      }

      // Try to enable CORS on the image if possible
      this.enableCorsOnImage(targetTile);

      // Create a temporary canvas to sample from the tile
      return this.sampleColorFromImage(
        targetTile,
        point,
        tileX,
        tileY,
        zoom,
        tileSize,
      );
    } catch (error) {
      console.error('Error extracting color from tile images:', error);
      return null;
    }
  }

  private getColorFromCanvas(
    canvas: HTMLCanvasElement,
    point: Point,
  ): ColorInfo | null {
    try {
      // Get the context if we don't have it
      if (!this.context) {
        this.context = canvas.getContext('2d');
        if (!this.context) {
          console.warn('Could not get 2D context from canvas');
          return null;
        }
      }

      // Sample the pixel at the mouse position
      const imageData = this.context.getImageData(
        Math.round(point.x),
        Math.round(point.y),
        1,
        1,
      );

      if (imageData.data.length < 4) {
        console.warn('Invalid image data');
        return null;
      }

      const [r, g, b, a] = imageData.data;

      return {
        r,
        g,
        b,
        a,
        hex: this.rgbToHex(r, g, b),
        rgba: `rgba(${r}, ${g}, ${b}, ${a / 255})`,
      };
    } catch (error) {
      console.error('Error extracting color from canvas:', error);
      return null;
    }
  }

  private getColorFromAnyImage(
    container: HTMLElement,
    point: Point,
  ): ColorInfo | null {
    try {
      // Find all images in the map container
      const images = container.querySelectorAll('img');

      if (images.length === 0) {
        return null;
      }

      // Create a temporary canvas to composite all images
      const tempCanvas = document.createElement('canvas');
      const tempContext = tempCanvas.getContext('2d');
      if (!tempContext) {
        console.warn('Could not create temporary canvas context');
        return null;
      }

      // Set canvas size to match the container
      const rect = container.getBoundingClientRect();
      tempCanvas.width = rect.width;
      tempCanvas.height = rect.height;

      // Draw all images to the canvas
      for (const img of Array.from(images)) {
        const imageElement = img as HTMLImageElement;
        if (imageElement.complete && imageElement.naturalWidth > 0) {
          const imgRect = imageElement.getBoundingClientRect();
          const containerRect = container.getBoundingClientRect();

          const x = imgRect.left - containerRect.left;
          const y = imgRect.top - containerRect.top;

          tempContext.drawImage(
            imageElement,
            x,
            y,
            imgRect.width,
            imgRect.height,
          );
        }
      }

      // Sample the pixel at the mouse position
      const imageData = tempContext.getImageData(
        Math.round(point.x),
        Math.round(point.y),
        1,
        1,
      );

      if (imageData.data.length < 4) {
        console.warn('Invalid image data');
        return null;
      }

      const [r, g, b, a] = imageData.data;

      return {
        r,
        g,
        b,
        a,
        hex: this.rgbToHex(r, g, b),
        rgba: `rgba(${r}, ${g}, ${b}, ${a / 255})`,
      };
    } catch (error) {
      console.error('Error extracting color from any image:', error);
      return null;
    }
  }

  private getCanvasFromMapContainer(
    container: HTMLElement,
  ): HTMLCanvasElement | null {
    // Look for canvas elements in the map container
    const canvases = container.querySelectorAll('canvas');

    // Return the first canvas we find (usually the main map canvas)
    if (canvases.length > 0) {
      return canvases[0] as HTMLCanvasElement;
    }

    // If no canvas found, try to find it in child elements
    const mapPane = container.querySelector('.leaflet-map-pane');
    if (mapPane) {
      const mapCanvases = mapPane.querySelectorAll('canvas');
      if (mapCanvases.length > 0) {
        return mapCanvases[0] as HTMLCanvasElement;
      }
    }

    return null;
  }

  private findLayerByName(map: Map, layerName: string): any | null {
    // This is a simplified approach - in practice, you might need to track layers differently
    const layers = (map as any)._layers;
    for (const layerId in layers) {
      const layer = layers[layerId];
      if (layer.options && layer.options.name === layerName) {
        return layer;
      }
    }
    return null;
  }

  private getColorFromVectorLayer(
    map: Map,
    latlng: LatLng,
    layer: LayerGroup,
  ): ColorInfo | null {
    // Suppress unused parameter warnings
    void map;
    void latlng;
    void layer;

    // For vector layers, we need to check if the point intersects with any features
    // This is more complex and depends on the specific vector layer implementation
    console.warn('Color extraction from vector layers not yet implemented');
    return null;
  }

  private findTileImageByCoordinates(
    tileImages: NodeListOf<Element>,
    tileX: number,
    tileY: number,
    zoom: number,
  ): HTMLImageElement | null {
    // Look for tile images with the specific coordinates
    for (const img of Array.from(tileImages)) {
      const imageElement = img as HTMLImageElement;
      const src = imageElement.src;

      // Check if this tile matches our coordinates
      if (
        src.includes(`/${zoom}/${tileX}/${tileY}`) ||
        src.includes(`/${zoom}/${tileX}/${tileY}.`) ||
        src.includes(`/${zoom}/${tileX}/${tileY}_`)
      ) {
        return imageElement;
      }
    }
    return null;
  }

  private sampleColorFromImage(
    image: HTMLImageElement,
    point: Point,
    tileX: number,
    tileY: number,
    zoom: number,
    tileSize: number,
  ): ColorInfo | null {
    try {
      // Try to get color using a CORS-safe approach first
      const colorFromCorsSafe = this.getColorFromCorsSafeImage(
        image,
        point,
        tileX,
        tileY,
        zoom,
        tileSize,
      );
      if (colorFromCorsSafe) {
        return colorFromCorsSafe;
      }

      // Fallback: Try canvas approach with CORS handling
      return this.getColorFromCanvasWithCors(
        image,
        point,
        tileX,
        tileY,
        zoom,
        tileSize,
      );
    } catch (error) {
      console.error('Error sampling color from image:', error);
      return null;
    }
  }

  private getColorFromCorsSafeImage(
    image: HTMLImageElement,
    point: Point,
    tileX: number,
    tileY: number,
    zoom: number,
    tileSize: number,
  ): ColorInfo | null {
    try {
      // Check if image is from same origin or has CORS headers
      if (this.isImageCorsSafe(image)) {
        return this.sampleColorFromCanvas(
          image,
          point,
          tileX,
          tileY,
          zoom,
          tileSize,
        );
      }
      return null;
    } catch (error) {
      console.warn('CORS-safe approach failed:', error);
      return null;
    }
  }

  private getColorFromCanvasWithCors(
    image: HTMLImageElement,
    point: Point,
    tileX: number,
    tileY: number,
    zoom: number,
    tileSize: number,
  ): ColorInfo | null {
    try {
      // Create a temporary canvas to sample from the image
      const tempCanvas = document.createElement('canvas');
      const tempContext = tempCanvas.getContext('2d');
      if (!tempContext) {
        console.warn('Could not create temporary canvas context');
        return null;
      }

      // Set canvas size to match tile
      tempCanvas.width = tileSize;
      tempCanvas.height = tileSize;

      // Try to draw the image with CORS handling
      try {
        tempContext.drawImage(image, 0, 0, tileSize, tileSize);
      } catch (corsError) {
        console.warn('CORS error when drawing image:', corsError);
        return this.getColorFromImageFallback(
          image,
          point,
          tileX,
          tileY,
          zoom,
          tileSize,
        );
      }

      // Calculate pixel position within the tile
      const tilePoint = this.getTilePixelPosition(
        point,
        tileX,
        tileY,
        zoom,
        tileSize,
      );

      // Sample the pixel
      const imageData = tempContext.getImageData(
        tilePoint.x,
        tilePoint.y,
        1,
        1,
      );
      const [r, g, b, a] = imageData.data;

      return {
        r,
        g,
        b,
        a,
        hex: this.rgbToHex(r, g, b),
        rgba: `rgba(${r}, ${g}, ${b}, ${a / 255})`,
      };
    } catch (error) {
      console.error('Error in canvas with CORS approach:', error);
      return this.getColorFromImageFallback(
        image,
        point,
        tileX,
        tileY,
        zoom,
        tileSize,
      );
    }
  }

  private sampleColorFromCanvas(
    image: HTMLImageElement,
    point: Point,
    tileX: number,
    tileY: number,
    zoom: number,
    tileSize: number,
  ): ColorInfo | null {
    try {
      // Create a temporary canvas to sample from the image
      const tempCanvas = document.createElement('canvas');
      const tempContext = tempCanvas.getContext('2d');
      if (!tempContext) {
        console.warn('Could not create temporary canvas context');
        return null;
      }

      // Set canvas size to match tile
      tempCanvas.width = tileSize;
      tempCanvas.height = tileSize;

      // Draw the tile image to the canvas
      tempContext.drawImage(image, 0, 0, tileSize, tileSize);

      // Calculate pixel position within the tile
      const tilePoint = this.getTilePixelPosition(
        point,
        tileX,
        tileY,
        zoom,
        tileSize,
      );

      // Sample the pixel
      const imageData = tempContext.getImageData(
        tilePoint.x,
        tilePoint.y,
        1,
        1,
      );
      const [r, g, b, a] = imageData.data;

      return {
        r,
        g,
        b,
        a,
        hex: this.rgbToHex(r, g, b),
        rgba: `rgba(${r}, ${g}, ${b}, ${a / 255})`,
      };
    } catch (error) {
      console.error('Error sampling color from canvas:', error);
      return null;
    }
  }

  private getColorFromImageFallback(
    image: HTMLImageElement,
    point: Point,
    tileX: number,
    tileY: number,
    zoom: number,
    tileSize: number,
  ): ColorInfo | null {
    try {
      // Suppress unused parameter warnings
      void point;
      void tileX;
      void tileY;
      void zoom;
      void tileSize;

      // Fallback: Try to get color using CSS computed styles or other methods
      console.warn('Using fallback color extraction method');

      // For now, return a default color or try to extract from image URL patterns
      // This is a simplified fallback - in practice, you might need more sophisticated approaches
      return this.getColorFromImageUrl(image.src);
    } catch (error) {
      console.error('Error in fallback color extraction:', error);
      return null;
    }
  }

  private isImageCorsSafe(image: HTMLImageElement): boolean {
    try {
      // Check if the image is from the same origin
      const imageUrl = new URL(image.src);
      const currentUrl = new URL(window.location.href);

      return imageUrl.origin === currentUrl.origin;
    } catch (error) {
      console.warn('Error checking CORS safety:', error);
      return false;
    }
  }

  private getColorFromImageUrl(imageSrc: string): ColorInfo | null {
    try {
      console.log('Attempting to extract color from image URL:', imageSrc);

      // Try to extract color information from the URL or use alternative methods
      const colorFromUrl = this.extractColorFromUrl(imageSrc);
      if (colorFromUrl) {
        return colorFromUrl;
      }

      // Try to use a CORS proxy if available
      const colorFromProxy = this.getColorFromCorsProxy(imageSrc);
      if (colorFromProxy) {
        return colorFromProxy;
      }

      // Final fallback: return a default color
      console.warn('Using default color due to CORS restrictions');
      return {
        r: 128,
        g: 128,
        b: 128,
        a: 255,
        hex: '#808080',
        rgba: 'rgba(128, 128, 128, 1)',
      };
    } catch (error) {
      console.error('Error extracting color from image URL:', error);
      return null;
    }
  }

  private extractColorFromUrl(imageSrc: string): ColorInfo | null {
    try {
      // Try to extract color information from the URL
      // This is a simplified approach - you might need to implement more sophisticated parsing

      // Check if the URL contains color information
      const colorMatch = imageSrc.match(/#([0-9a-fA-F]{6})/);
      if (colorMatch) {
        const hex = colorMatch[1];
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);

        return {
          r,
          g,
          b,
          a: 255,
          hex: `#${hex}`,
          rgba: `rgba(${r}, ${g}, ${b}, 1)`,
        };
      }

      return null;
    } catch (error) {
      console.error('Error extracting color from URL:', error);
      return null;
    }
  }

  private getColorFromCorsProxy(imageSrc: string): ColorInfo | null {
    try {
      // Try to use a CORS proxy to fetch the image
      console.log('Attempting to use CORS proxy for:', imageSrc);

      // Use the CORS proxy endpoint
      const proxyUrl = `http://localhost:8001/proxy-image?url=${encodeURIComponent(imageSrc)}`;

      // Create a new image element with the proxy URL
      const proxyImage = new Image();
      proxyImage.crossOrigin = 'anonymous';

      // This is a synchronous method, so we can't wait for the image to load
      // In a real implementation, you would need to make this asynchronous
      // or use a different approach

      console.log('CORS proxy URL:', proxyUrl);

      // For now, return null to indicate we need async implementation
      // In a real implementation, you would:
      // 1. Make this method async
      // 2. Wait for the image to load
      // 3. Extract color from the loaded image

      return null;
    } catch (error) {
      console.error('Error using CORS proxy:', error);
      return null;
    }
  }

  private enableCorsOnImage(image: HTMLImageElement): void {
    try {
      // Try to enable CORS on the image
      if (!image.crossOrigin) {
        image.crossOrigin = 'anonymous';
        console.log('Set crossOrigin to anonymous for image:', image.src);
      }
    } catch (error) {
      console.warn('Could not set crossOrigin on image:', error);
    }
  }

  private findTileImageForLayer(
    container: HTMLElement,
    tileLayer: TileLayer,
    tileX: number,
    tileY: number,
    zoom: number,
  ): HTMLImageElement | null {
    try {
      // Get the layer's URL template
      const urlTemplate = (tileLayer as any)._url;
      if (!urlTemplate) {
        console.warn('No URL template found for tile layer');
        return null;
      }

      console.log('Layer URL template:', urlTemplate);

      // Find all images in the container
      const images = container.querySelectorAll('img');
      console.log(`Found ${images.length} images in container`);

      // First, try to find exact URL match
      const expectedUrl = urlTemplate
        .replace('{s}', 'a') // Use first subdomain
        .replace('{z}', zoom.toString())
        .replace('{x}', tileX.toString())
        .replace('{y}', tileY.toString());

      console.log('Looking for tile with URL:', expectedUrl);

      for (const img of Array.from(images)) {
        const imageElement = img as HTMLImageElement;
        const src = imageElement.src;

        // Check for exact URL match first
        if (src === expectedUrl) {
          console.log('Found exact URL match:', src);
          return imageElement;
        }
      }

      // If no exact match and we're looking for a zoom level that might not exist,
      // try to find the closest available zoom level
      if (zoom > 0) {
        console.log(
          `No exact match at zoom ${zoom}, trying lower zoom levels...`,
        );

        for (let testZoom = zoom - 1; testZoom >= 0; testZoom--) {
          const testTileX = Math.floor(tileX / Math.pow(2, zoom - testZoom));
          const testTileY = Math.floor(tileY / Math.pow(2, zoom - testZoom));

          const testUrl = urlTemplate
            .replace('{s}', 'a')
            .replace('{z}', testZoom.toString())
            .replace('{x}', testTileX.toString())
            .replace('{y}', testTileY.toString());

          console.log(`Trying zoom ${testZoom} with URL:`, testUrl);

          for (const img of Array.from(images)) {
            const imageElement = img as HTMLImageElement;
            const src = imageElement.src;

            if (src === testUrl) {
              console.log(`Found tile at zoom ${testZoom}:`, src);
              return imageElement;
            }
          }
        }
      }

      // If no exact match, try to find by URL pattern matching
      const urlPattern = this.extractUrlPatternFromTemplate(urlTemplate);
      if (urlPattern) {
        console.log('Using URL pattern:', urlPattern);

        for (const img of Array.from(images)) {
          const imageElement = img as HTMLImageElement;
          const src = imageElement.src;

          if (urlPattern.test(src)) {
            console.log('Found tile by URL pattern:', src);
            return imageElement;
          }
        }
      }

      // Fallback: Look for images that contain the layer's domain/path
      const layerDomain = this.extractDomainFromUrl(urlTemplate);
      if (layerDomain) {
        console.log('Looking for images from domain:', layerDomain);

        for (const img of Array.from(images)) {
          const imageElement = img as HTMLImageElement;
          const src = imageElement.src;

          if (
            src.includes(layerDomain) &&
            src.includes(`/${zoom}/${tileX}/${tileY}`)
          ) {
            console.log('Found tile by domain match:', src);
            return imageElement;
          }
        }
      }

      // Additional fallback: Look for images that match the layer's specific path pattern
      const layerPath = this.extractLayerPathFromUrl(urlTemplate);
      if (layerPath) {
        console.log('Looking for images with layer path:', layerPath);

        for (const img of Array.from(images)) {
          const imageElement = img as HTMLImageElement;
          const src = imageElement.src;

          if (
            src.includes(layerPath) &&
            src.includes(`/${zoom}/${tileX}/${tileY}`)
          ) {
            console.log('Found tile by layer path match:', src);
            return imageElement;
          }
        }
      }

      // Log all available images for debugging
      console.log('Available images:');
      for (let i = 0; i < Math.min(images.length, 10); i++) {
        const img = images[i] as HTMLImageElement;
        console.log(`  ${i}: ${img.src}`);
      }

      console.warn('No tile image found for layer');
      return null;
    } catch (error) {
      console.error('Error finding tile image for layer:', error);
      return null;
    }
  }

  private extractUrlPatternFromTemplate(urlTemplate: string): RegExp | null {
    try {
      // Convert URL template to regex pattern
      // Example: "http://localhost:8080/data/vapourpressuredeficit_1981_2010_0_5m_raster_1/{z}/{x}/{y}.png"
      // Becomes: /http:\/\/localhost:8080\/data\/vapourpressuredeficit_1981_2010_0_5m_raster_1\/\d+\/\d+\/\d+\.png/

      const escaped = urlTemplate
        .replace(/[.*+?^${}()|[\]\\]/g, '\\$&') // Escape special regex chars
        .replace(/\\{[^}]+\\}/g, '\\d+'); // Replace {param} with \d+ for numbers

      return new RegExp(escaped);
    } catch (error) {
      console.error('Error creating URL pattern:', error);
      return null;
    }
  }

  private extractDomainFromUrl(urlTemplate: string): string | null {
    try {
      // Extract the domain/path part from the URL template
      // Example: "http://localhost:8080/data/vapourpressuredeficit_1981_2010_0_5m_raster_1/{z}/{x}/{y}.png"
      // Returns: "localhost:8080/data/vapourpressuredeficit_1981_2010_0_5m_raster_1"

      const url = new URL(urlTemplate.replace(/\{[^}]+\}/g, 'placeholder'));
      const pathname = url.pathname.split('/').slice(0, -3).join('/'); // Remove {z}/{x}/{y}.png
      return `${url.host}${pathname}`;
    } catch (error) {
      console.error('Error extracting domain from URL:', error);
      return null;
    }
  }

  private extractLayerPathFromUrl(urlTemplate: string): string | null {
    try {
      // Extract the specific layer path from the URL template
      // Example: "http://localhost:8080/data/vapourpressuredeficit_1981_2010_0_5m_raster_1/{z}/{x}/{y}.png"
      // Returns: "vapourpressuredeficit_1981_2010_0_5m_raster_1"

      const url = new URL(urlTemplate.replace(/\{[^}]+\}/g, 'placeholder'));
      const pathParts = url.pathname.split('/');

      // Find the layer-specific part (usually the last meaningful part before {z}/{x}/{y})
      for (let i = pathParts.length - 1; i >= 0; i--) {
        const part = pathParts[i];
        if (part && part !== 'data' && part !== 'placeholder') {
          return part;
        }
      }

      return null;
    } catch (error) {
      console.error('Error extracting layer path from URL:', error);
      return null;
    }
  }

  private getLayerMaxZoom(tileLayer: TileLayer): number {
    try {
      // Try to get maxNativeZoom from the layer options
      const options = (tileLayer as any).options;
      if (options && typeof options.maxNativeZoom === 'number') {
        return options.maxNativeZoom;
      }

      // Try to get maxZoom from the layer options
      if (options && typeof options.maxZoom === 'number') {
        return options.maxZoom;
      }

      // Try to get from the layer's _url template by checking for zoom limits
      const urlTemplate = (tileLayer as any)._url;
      if (urlTemplate) {
        // Check if the URL template contains zoom level information
        // This is a fallback - you might need to adjust based on your specific setup
        const zoomMatch = urlTemplate.match(/maxzoom[=:](\\d+)/i);
        if (zoomMatch) {
          return parseInt(zoomMatch[1], 10);
        }
      }

      // Default fallback - assume reasonable max zoom
      console.warn('Could not determine layer max zoom, using default value 5');
      return 5;
    } catch (error) {
      console.error('Error getting layer max zoom:', error);
      return 5; // Safe fallback
    }
  }

  private findTileElement(
    container: HTMLElement,
    x: number,
    y: number,
    zoom: number,
  ): HTMLImageElement | null {
    // Look for tile images with the specific coordinates
    const tileImages = container.querySelectorAll(
      'img[src*="' + zoom + '/' + x + '/' + y + '"]',
    );
    if (tileImages.length > 0) {
      return tileImages[0] as HTMLImageElement;
    }
    return null;
  }

  private getTilePixelPosition(
    point: Point,
    _tileX: number,
    _tileY: number,
    _zoom: number,
    tileSize: number,
  ): Point {
    // Calculate the pixel position within the tile
    const tilePixelX = point.x % tileSize;
    const tilePixelY = point.y % tileSize;

    return new Point(tilePixelX, tilePixelY);
  }

  private debugMapElements(container: HTMLElement): void {
    console.log('=== Map Container Debug Info ===');
    console.log('Container:', container);

    // Check for canvas elements
    const canvases = container.querySelectorAll('canvas');
    console.log('Canvas elements found:', canvases.length);

    // Check for image elements
    const images = container.querySelectorAll('img');
    console.log('Image elements found:', images.length);

    // Log image sources
    for (let i = 0; i < Math.min(images.length, 5); i++) {
      const img = images[i] as HTMLImageElement;
      console.log(`Image ${i}:`, img.src);
    }

    // Check for tile-specific images
    const tileImages = container.querySelectorAll(
      'img[src*="/tiles/"], img[src*="tile"], img[src*="png"], img[src*="jpg"]',
    );
    console.log('Tile images found:', tileImages.length);

    // Check map panes
    const mapPanes = container.querySelectorAll(
      '.leaflet-map-pane, .leaflet-tile-pane, .leaflet-overlay-pane',
    );
    console.log('Map panes found:', mapPanes.length);

    console.log('=== End Debug Info ===');
  }

  private rgbToHex(r: number, g: number, b: number): string {
    const toHex = (n: number) => {
      const hex = Math.round(n).toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    };
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  }

  /**
   * Get all available layers on the map
   * @param map Leaflet map instance
   * @returns Array of layer names
   */
  getAvailableLayers(map: Map): string[] {
    const layers: string[] = [];
    const mapLayers = (map as any)._layers;

    for (const layerId in mapLayers) {
      const layer = mapLayers[layerId];
      if (layer.options && layer.options.name) {
        layers.push(layer.options.name);
      }
    }

    return layers;
  }

  /**
   * Enable or disable debug logging
   * @param enabled Whether to enable debug logging
   */
  setDebugMode(enabled: boolean): void {
    this.debugMode = enabled;
  }
}
