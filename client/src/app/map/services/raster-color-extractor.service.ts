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
  private canvasCache = new WeakMap<HTMLImageElement, HTMLCanvasElement>();
  private contextCache = new WeakMap<
    HTMLImageElement,
    CanvasRenderingContext2D
  >();

  extractColorFromRasterLayer(
    event: LeafletMouseEvent | { latlng: { lat: number; lng: number } },
    map: Map,
    rasterLayer: any,
    selectedOption: LayerOption | undefined,
    monthSelected: number,
  ): RasterColor | null {
    if (!map || !rasterLayer) {
      return null;
    }

    const mapZoom = map.getZoom();
    const effectiveZoom = Math.min(
      mapZoom,
      selectedOption?.rasterMaxZoom ?? mapZoom,
    );

    // Convert lat/lng to tile coordinates using effective zoom (actual tile zoom level)
    const tileSize = 256;
    const scale = Math.pow(2, effectiveZoom);
    const latRad = (event.latlng.lat * Math.PI) / 180;
    const worldX = (event.latlng.lng + 180) / 360;
    const worldY =
      (1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2;

    const tileX = Math.floor(worldX * scale);
    const tileY = Math.floor(worldY * scale);

    // Calculate pixel position within the tile
    // Note: tile images are always 256x256 pixels regardless of display zoom
    const pixelX = Math.floor((worldX * scale - tileX) * tileSize);
    const pixelY = Math.floor((worldY * scale - tileY) * tileSize);

    // Find the tile image element in the DOM - query once
    const mapContainer = map.getContainer();
    const tileImages = Array.from(
      mapContainer.querySelectorAll('img.leaflet-tile-loaded'),
    ) as HTMLImageElement[];

    if (tileImages.length === 0) {
      return null;
    }

    // Pre-compute filter strings to avoid repeated string operations
    const rasterUrl = selectedOption?.rasterUrl || '';
    const monthPattern = `_${monthSelected}/`;
    const urlPattern = /\/(\d+)\/(\d+)\/(\d+)\.png/;

    // Pre-filter and convert to array once
    const filteredImages: HTMLImageElement[] = [];
    for (const img of tileImages) {
      const imgSrc = img.src;
      if (imgSrc.includes(rasterUrl) && imgSrc.includes(monthPattern)) {
        filteredImages.push(img);
      }
    }

    if (filteredImages.length === 0) {
      return null;
    }

    // Find tile by matching tile coordinates from URL
    for (const img of filteredImages) {
      const tileMatch = img.src.match(urlPattern);
      if (tileMatch) {
        const imgZ = parseInt(tileMatch[1], 10);
        if (imgZ === effectiveZoom) {
          const imgX = parseInt(tileMatch[2], 10);
          const imgY = parseInt(tileMatch[3], 10);
          if (imgX === tileX && imgY === tileY) {
            return this.getPixelColorFromImage(img, pixelX, pixelY);
          }
        }
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
      const width = img.width || img.naturalWidth;
      const height = img.height || img.naturalHeight;

      if (width === 0 || height === 0) {
        return null;
      }

      let canvas = this.canvasCache.get(img);
      let ctx = this.contextCache.get(img);

      if (!canvas || !ctx) {
        canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const newCtx = canvas.getContext('2d', { willReadFrequently: true });

        if (!newCtx) {
          return null;
        }

        ctx = newCtx;
        this.canvasCache.set(img, canvas);
        this.contextCache.set(img, ctx);
      }

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      ctx.drawImage(img, 0, 0);

      const clampedX = x < 0 ? 0 : x >= width ? width - 1 : x;
      const clampedY = y < 0 ? 0 : y >= height ? height - 1 : y;

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

    const normalizedColor = {
      r: color.r / 255,
      g: color.g / 255,
      b: color.b / 255,
    };

    let minSquaredDistance = Infinity;
    let closestIndex = 0;

    for (let i = 0; i < numColors; i++) {
      const configColor = colors[i];
      const squaredDistance = this.calculateSquaredColorDistance(
        normalizedColor,
        configColor,
      );

      if (squaredDistance < minSquaredDistance) {
        minSquaredDistance = squaredDistance;
        closestIndex = i;
      }
    }

    const minDistance = Math.sqrt(minSquaredDistance);

    if (minDistance < 0.001) {
      return levels[closestIndex];
    }

    let neighborIndex: number;
    let neighborDistance: number;

    if (closestIndex === 0) {
      neighborIndex = 1;
      neighborDistance = this.calculateColorDistance(
        normalizedColor,
        colors[1],
      );
    } else if (closestIndex === numColors - 1) {
      neighborIndex = numColors - 2;
      neighborDistance = this.calculateColorDistance(
        normalizedColor,
        colors[numColors - 2],
      );
    } else {
      const prevSquaredDistance = this.calculateSquaredColorDistance(
        normalizedColor,
        colors[closestIndex - 1],
      );
      const nextSquaredDistance = this.calculateSquaredColorDistance(
        normalizedColor,
        colors[closestIndex + 1],
      );

      if (prevSquaredDistance < nextSquaredDistance) {
        neighborIndex = closestIndex - 1;
        neighborDistance = Math.sqrt(prevSquaredDistance);
      } else {
        neighborIndex = closestIndex + 1;
        neighborDistance = Math.sqrt(nextSquaredDistance);
      }
    }

    const closestLevel = levels[closestIndex];
    const neighborLevel = levels[neighborIndex];

    const totalDistance = minDistance + neighborDistance;
    if (totalDistance === 0) {
      return closestLevel;
    }

    const weight1 = neighborDistance / totalDistance;
    const weight2 = minDistance / totalDistance;

    let interpolatedValue: number;
    if (log_scale) {
      const log1 = Math.log10(Math.max(closestLevel, 1e-10));
      const log2 = Math.log10(Math.max(neighborLevel, 1e-10));
      const interpolatedLog = weight1 * log1 + weight2 * log2;
      interpolatedValue = Math.pow(10, interpolatedLog);
    } else {
      interpolatedValue = weight1 * closestLevel + weight2 * neighborLevel;
    }

    return interpolatedValue;
  }

  private calculateSquaredColorDistance(
    color1: { r: number; g: number; b: number },
    color2: number[],
  ): number {
    const dr = color1.r - color2[0];
    const dg = color1.g - color2[1];
    const db = color1.b - color2[2];

    return dr * dr + dg * dg + db * db;
  }

  private calculateColorDistance(
    color1: { r: number; g: number; b: number },
    color2: number[],
  ): number {
    return Math.sqrt(this.calculateSquaredColorDistance(color1, color2));
  }
}
