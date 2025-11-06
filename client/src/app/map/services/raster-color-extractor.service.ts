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

    const zoom = map.getZoom();
    const containerPoint = map.latLngToContainerPoint(event.latlng);

    // Convert lat/lng to tile coordinates
    const tileSize = 256;
    const scale = Math.pow(2, zoom);
    const worldX = (event.latlng.lng + 180) / 360;
    const worldY =
      (1 -
        Math.log(
          Math.tan((event.latlng.lat * Math.PI) / 180) +
            1 / Math.cos((event.latlng.lat * Math.PI) / 180),
        ) /
          Math.PI) /
      2;

    const tileX = Math.floor(worldX * scale);
    const tileY = Math.floor(worldY * scale);

    // Calculate pixel position within the tile
    const pixelX = Math.floor((worldX * scale - tileX) * tileSize);
    const pixelY = Math.floor((worldY * scale - tileY) * tileSize);

    // Find the tile image element in the DOM
    const mapContainer = map.getContainer();
    const tileImages = mapContainer.querySelectorAll(
      'img.leaflet-tile-loaded',
    ) as NodeListOf<HTMLImageElement>;

    // First try to find by matching tile coordinates from URL
    for (const img of Array.from(tileImages)) {
      const imgSrc = img.src;
      if (
        imgSrc.includes(selectedOption?.rasterUrl || '') &&
        imgSrc.includes(`_${monthSelected}/`)
      ) {
        const tileMatch = imgSrc.match(/\/(\d+)\/(\d+)\/(\d+)\.png/);
        if (tileMatch) {
          const imgZ = parseInt(tileMatch[1], 10);
          const imgX = parseInt(tileMatch[2], 10);
          const imgY = parseInt(tileMatch[3], 10);

          if (imgZ === zoom && imgX === tileX && imgY === tileY) {
            return this.getPixelColorFromImage(img, pixelX, pixelY);
          }
        }
      }
    }

    // Fallback: find tile by checking if container point is within tile bounds
    for (const img of Array.from(tileImages)) {
      const imgSrc = img.src;
      if (
        imgSrc.includes(selectedOption?.rasterUrl || '') &&
        imgSrc.includes(`_${monthSelected}/`)
      ) {
        const rect = img.getBoundingClientRect();
        const mapRect = mapContainer.getBoundingClientRect();
        const imgLeft = rect.left - mapRect.left;
        const imgTop = rect.top - mapRect.top;

        if (
          containerPoint.x >= imgLeft &&
          containerPoint.x < imgLeft + rect.width &&
          containerPoint.y >= imgTop &&
          containerPoint.y < imgTop + rect.height
        ) {
          const localX = Math.floor(
            ((containerPoint.x - imgLeft) / rect.width) * tileSize,
          );
          const localY = Math.floor(
            ((containerPoint.y - imgTop) / rect.height) * tileSize,
          );
          return this.getPixelColorFromImage(img, localX, localY);
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
      const canvas = document.createElement('canvas');
      canvas.width = img.width || img.naturalWidth;
      canvas.height = img.height || img.naturalHeight;
      const ctx = canvas.getContext('2d');

      if (!ctx) {
        return null;
      }

      ctx.drawImage(img, 0, 0);

      // Ensure coordinates are within bounds
      const clampedX = Math.max(0, Math.min(x, canvas.width - 1));
      const clampedY = Math.max(0, Math.min(y, canvas.height - 1));

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
