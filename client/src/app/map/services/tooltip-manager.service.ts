import { Injectable } from '@angular/core';
import { CircleMarker, Map, Tooltip } from 'leaflet';

@Injectable({
  providedIn: 'root',
})
export class TooltipManagerService {
  private hoverTooltips = new WeakMap<Map, Tooltip>();
  private clickTooltips = new WeakMap<Map, Tooltip>();
  private clickMarkers = new WeakMap<Map, CircleMarker>();

  private createTooltip(
    content: string,
    latlng: any,
    map: Map,
    permanent: boolean,
  ): Tooltip {
    const tooltip = new Tooltip({
      content: content,
      className: 'contour-hover-tooltip',
      direction: 'top',
      offset: [0, -4],
      permanent: permanent,
    });

    tooltip.setLatLng(latlng);
    tooltip.addTo(map);
    return tooltip;
  }

  createHoverTooltip(content: string, latlng: any, map: Map): void {
    this.removeHoverTooltip(map);

    const tooltip = this.createTooltip(content, latlng, map, false);
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

    const marker = new CircleMarker(latlng, {
      radius: 3,
      fillColor: '#000000',
      color: '#000000',
      weight: 1,
      opacity: 1,
      fillOpacity: 1,
    });
    marker.addTo(map);
    this.clickMarkers.set(map, marker);

    const tooltip = this.createTooltip(content, latlng, map, true);
    this.clickTooltips.set(map, tooltip);
  }

  removeClickTooltip(map: Map): void {
    const tooltip = this.clickTooltips.get(map);
    if (tooltip) {
      map.removeLayer(tooltip);
      this.clickTooltips.delete(map);
    }
    const marker = this.clickMarkers.get(map);
    if (marker) {
      map.removeLayer(marker);
      this.clickMarkers.delete(map);
    }
  }

  removeAllTooltips(map: Map): void {
    this.removeHoverTooltip(map);
    this.removeClickTooltip(map);
  }
}
