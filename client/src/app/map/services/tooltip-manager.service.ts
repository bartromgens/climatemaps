import { Injectable } from '@angular/core';
import { Map, Tooltip } from 'leaflet';

@Injectable({
  providedIn: 'root',
})
export class TooltipManagerService {
  private hoverTooltips = new WeakMap<Map, Tooltip>();
  private clickTooltips = new WeakMap<Map, Tooltip>();

  createHoverTooltip(content: string, latlng: any, map: Map): void {
    this.removeHoverTooltip(map);

    const tooltip = new Tooltip({
      content: content,
      className: 'contour-hover-tooltip',
      direction: 'top',
      offset: [0, -10],
      opacity: 0.9,
    });

    tooltip.setLatLng(latlng);
    tooltip.addTo(map);
    this.hoverTooltips.set(map, tooltip);
  }

  removeHoverTooltip(map: Map): void {
    const tooltip = this.hoverTooltips.get(map);
    if (tooltip) {
      map.removeLayer(tooltip);
      this.hoverTooltips.delete(map);
    }
  }

  createPersistentTooltip(content: string, latlng: any, map: Map): void {
    this.removeClickTooltip(map);

    const tooltip = new Tooltip({
      content: content,
      className: 'contour-hover-tooltip',
      direction: 'top',
      offset: [0, -10],
      opacity: 0.9,
      permanent: true,
    });

    tooltip.setLatLng(latlng);
    tooltip.addTo(map);
    this.clickTooltips.set(map, tooltip);
  }

  removeClickTooltip(map: Map): void {
    const tooltip = this.clickTooltips.get(map);
    if (tooltip) {
      map.removeLayer(tooltip);
      this.clickTooltips.delete(map);
    }
  }

  removeAllTooltips(map: Map): void {
    this.removeHoverTooltip(map);
    this.removeClickTooltip(map);
  }
}
