import { Injectable } from '@angular/core';
import { Map, Tooltip } from 'leaflet';

@Injectable({
  providedIn: 'root',
})
export class TooltipManagerService {
  private hoverTooltip: Tooltip | null = null;
  private clickTooltip: Tooltip | null = null;

  createHoverTooltip(content: string, latlng: any, map: Map): void {
    this.removeHoverTooltip(map);

    this.hoverTooltip = new Tooltip({
      content: content,
      className: 'contour-hover-tooltip',
      direction: 'top',
      offset: [0, -10],
      opacity: 0.9,
    });

    this.hoverTooltip.setLatLng(latlng);
    this.hoverTooltip.addTo(map);
  }

  removeHoverTooltip(map: Map): void {
    if (this.hoverTooltip) {
      map.removeLayer(this.hoverTooltip);
      this.hoverTooltip = null;
    }
  }

  createPersistentTooltip(content: string, latlng: any, map: Map): void {
    this.removeClickTooltip(map);

    this.clickTooltip = new Tooltip({
      content: content,
      className: 'contour-hover-tooltip',
      direction: 'top',
      offset: [0, -10],
      opacity: 0.9,
      permanent: true,
    });

    this.clickTooltip.setLatLng(latlng);
    this.clickTooltip.addTo(map);
  }

  removeClickTooltip(map: Map): void {
    if (this.clickTooltip) {
      map.removeLayer(this.clickTooltip);
      this.clickTooltip = null;
    }
  }

  removeAllTooltips(map: Map): void {
    this.removeHoverTooltip(map);
    this.removeClickTooltip(map);
  }
}
