import { Injectable } from '@angular/core';
import { LeafletMouseEvent, Map } from 'leaflet';
import { LayerOption } from './layer-builder.service';
import { ColorbarConfigResponse } from '../../core/climatemap.service';

export interface RasterColor {
  r: number;
  g: number;
  b: number;
  a: number;
}

@Injectable({
  providedIn: 'root',
})
export class RasterColorExtractorService {
  private readonly tileRegex = /\/(\d+)\/(\d+)\/(\d+)\.png/;
  private canvasCache: HTMLCanvasElement | null = null;
  private contextCache: CanvasRenderingContext2D | null = null;
  private cachedTileImages: HTMLImageElement[] | null = null;
  private cachedMapContainer: HTMLElement | null = null;
  private lastQueryTime = 0;
  private readonly TILE_QUERY_CACHE_MS = 100;

  extractColorFromRasterLayer(
    event: LeafletMouseEvent | { latlng: { lat: number; lng: number } },
    map: Map,
    rasterLayer: any,
    selectedOption: LayerOption | undefined,
    monthSelected: number,
  ): RasterColor | null {
    if (!map || !rasterLayer || !selectedOption?.rasterUrl) {
      return null;
    }

    const zoom = map.getZoom();
    const lat = event.latlng.lat;
    const lng = event.latlng.lng;

    // Convert lat/lng to tile coordinates
    const tileSize = 256;
    const scale = Math.pow(2, zoom);
    const worldX = (lng + 180) / 360;
    const latRad = (lat * Math.PI) / 180;
    const worldY =
      (1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2;

    const tileX = Math.floor(worldX * scale);
    const tileY = Math.floor(worldY * scale);

    // Calculate pixel position within the tile
    const pixelX = Math.floor((worldX * scale - tileX) * tileSize);
    const pixelY = Math.floor((worldY * scale - tileY) * tileSize);

    // Cache tile images query to avoid frequent DOM queries
    const now = Date.now();
    const mapContainer = map.getContainer();
    if (
      !this.cachedTileImages ||
      this.cachedMapContainer !== mapContainer ||
      now - this.lastQueryTime > this.TILE_QUERY_CACHE_MS
    ) {
      const tileNodeList = mapContainer.querySelectorAll(
        'img.leaflet-tile-loaded',
      ) as NodeListOf<HTMLImageElement>;
      this.cachedTileImages = Array.from(tileNodeList);
      this.cachedMapContainer = mapContainer;
      this.lastQueryTime = now;
    }

    const tileImages = this.cachedTileImages;
    const rasterUrl = selectedOption.rasterUrl;
    const monthPath = `_${monthSelected}/`;

    // Iterate over cached tile images array
    for (const img of tileImages) {
      const imgSrc = img.src;

      // Early exit: check URL contains before regex matching
      if (!imgSrc.includes(rasterUrl) || !imgSrc.includes(monthPath)) {
        continue;
      }

      const tileMatch = imgSrc.match(this.tileRegex);
      if (!tileMatch) {
        continue;
      }

      const imgZ = parseInt(tileMatch[1], 10);
      const imgX = parseInt(tileMatch[2], 10);
      const imgY = parseInt(tileMatch[3], 10);

      if (imgZ === zoom && imgX === tileX && imgY === tileY) {
        return this.getPixelColorFromImage(img, pixelX, pixelY);
      }
    }

    return null;
  }

  private getPixelColorFromImage(
    img: HTMLImageElement,
    x: number,
    y: number,
  ): RasterColor | null {
    try {
      const imgWidth = img.width || img.naturalWidth;
      const imgHeight = img.height || img.naturalHeight;

      if (!this.canvasCache || !this.contextCache) {
        this.canvasCache = document.createElement('canvas');
        this.contextCache = this.canvasCache.getContext('2d', {
          willReadFrequently: true,
        });
        if (!this.contextCache) {
          return null;
        }
      }

      const canvas = this.canvasCache;
      const ctx = this.contextCache;

      // Only resize canvas if image dimensions changed
      if (canvas.width !== imgWidth || canvas.height !== imgHeight) {
        canvas.width = imgWidth;
        canvas.height = imgHeight;
      }

      ctx.drawImage(img, 0, 0);

      // Ensure coordinates are within bounds
      const clampedX = Math.max(0, Math.min(x, imgWidth - 1));
      const clampedY = Math.max(0, Math.min(y, imgHeight - 1));

      const imageData = ctx.getImageData(clampedX, clampedY, 1, 1);
      const pixel = imageData.data;

      return {
        r: pixel[0],
        g: pixel[1],
        b: pixel[2],
        a: pixel[3] / 255,
      };
    } catch (error) {
      console.warn(
        'Failed to extract pixel color (CORS or other issue):',
        error,
      );
      return null;
    }
  }

  getValueFromColor(
    color: RasterColor,
    colorbarConfig: ColorbarConfigResponse,
  ): number | null {
    if (!colorbarConfig || !colorbarConfig.colors || !colorbarConfig.levels) {
      return null;
    }

    const { colors, levels, log_scale } = colorbarConfig;
    const numColors = colors.length;

    if (numColors === 0 || numColors !== levels.length) {
      return null;
    }

    // Normalize the input color to 0-1 range (colors in config are already normalized)
    const normalizedColor = {
      r: color.r / 255,
      g: color.g / 255,
      b: color.b / 255,
    };

    // Find the closest matching color in the colorbar
    let minDistance = Infinity;
    let closestIndex = 0;

    for (let i = 0; i < numColors; i++) {
      const configColor = colors[i];
      const distance = this.calculateColorDistance(
        normalizedColor,
        configColor,
      );

      if (distance < minDistance) {
        minDistance = distance;
        closestIndex = i;
      }
    }

    // If exact match (or very close), return the corresponding level
    if (minDistance < 0.001) {
      return levels[closestIndex];
    }

    // Determine which adjacent color to interpolate with
    let neighborIndex: number;
    let neighborDistance: number;

    if (closestIndex === 0) {
      // At the start, use the next color
      neighborIndex = 1;
      neighborDistance = this.calculateColorDistance(
        normalizedColor,
        colors[1],
      );
    } else if (closestIndex === numColors - 1) {
      // At the end, use the previous color
      neighborIndex = numColors - 2;
      neighborDistance = this.calculateColorDistance(
        normalizedColor,
        colors[numColors - 2],
      );
    } else {
      // Check both neighbors and use the closer one
      const prevDistance = this.calculateColorDistance(
        normalizedColor,
        colors[closestIndex - 1],
      );
      const nextDistance = this.calculateColorDistance(
        normalizedColor,
        colors[closestIndex + 1],
      );

      if (prevDistance < nextDistance) {
        neighborIndex = closestIndex - 1;
        neighborDistance = prevDistance;
      } else {
        neighborIndex = closestIndex + 1;
        neighborDistance = nextDistance;
      }
    }

    // Interpolate between the closest color and its neighbor
    const closestLevel = levels[closestIndex];
    const neighborLevel = levels[neighborIndex];

    // Calculate weights based on inverse distance
    const totalDistance = minDistance + neighborDistance;
    if (totalDistance === 0) {
      return closestLevel;
    }

    const weight1 = neighborDistance / totalDistance;
    const weight2 = minDistance / totalDistance;

    // Interpolate the level value
    let interpolatedValue: number;
    if (log_scale) {
      // For log scale, interpolate in log space
      const log1 = Math.log10(Math.max(closestLevel, 1e-10));
      const log2 = Math.log10(Math.max(neighborLevel, 1e-10));
      const interpolatedLog = weight1 * log1 + weight2 * log2;
      interpolatedValue = Math.pow(10, interpolatedLog);
    } else {
      // Linear interpolation
      interpolatedValue = weight1 * closestLevel + weight2 * neighborLevel;
    }

    return interpolatedValue;
  }

  private calculateColorDistance(
    color1: { r: number; g: number; b: number },
    color2: number[],
  ): number {
    // Calculate Euclidean distance in RGB space (alpha ignored)
    const dr = color1.r - color2[0];
    const dg = color1.g - color2[1];
    const db = color1.b - color2[2];

    return Math.sqrt(dr * dr + dg * dg + db * db);
  }
}
