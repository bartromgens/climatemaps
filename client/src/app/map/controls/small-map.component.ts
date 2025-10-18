import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { LeafletModule } from '@bluehalo/ngx-leaflet';
import { control, latLng, Layer, Map, tileLayer } from 'leaflet';
import 'leaflet.vectorgrid';
import { Subject, takeUntil } from 'rxjs';

import { MapSyncService, MapViewState } from '../services/map-sync.service';
import { LayerOption } from '../services/layer-builder.service';
import { TooltipManagerService } from '../services/tooltip-manager.service';
import { VectorLayerTooltipService } from '../services/vector-layer-tooltip.service';

@Component({
  selector: 'app-small-map',
  standalone: true,
  imports: [CommonModule, LeafletModule],
  template: `
    <div class="small-map-container">
      <div class="map-label" *ngIf="label">{{ label }}</div>
      <div
        class="map-wrapper"
        leaflet
        [leafletOptions]="options"
        (leafletMapReady)="onMapReady($event)"
        (leafletMapMoveEnd)="onMove()"
        (leafletMapZoomEnd)="onZoom()"
      ></div>
    </div>
  `,
  styles: [
    `
      .small-map-container {
        position: relative;
        width: 100%;
        height: 100%;
        border: 2px solid white;
        box-sizing: border-box;
      }

      .map-label {
        position: absolute;
        top: 8px;
        left: 8px;
        background: rgba(255, 255, 255, 0.9);
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 12px;
        z-index: 1000;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
      }

      .map-wrapper {
        width: 100%;
        height: 100%;
      }
    `,
  ],
})
export class SmallMapComponent implements OnInit, OnDestroy, OnChanges {
  @Input() month: number | undefined;
  @Input() customLabel: string | undefined;
  @Input() selectedOption: LayerOption | undefined;
  @Input() showZoomControl = false;

  private map: Map | null = null;
  private rasterLayer: Layer | null = null;
  private vectorLayer: Layer | null = null;
  private destroy$ = new Subject<void>();
  private isUpdatingFromSync = false;

  private baseLayer = tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      maxZoom: 20,
      attribution: '...',
    },
  );

  options: any;

  get label(): string {
    return this.customLabel || '';
  }

  constructor(
    private mapSyncService: MapSyncService,
    private tooltipManager: TooltipManagerService,
    private vectorLayerTooltip: VectorLayerTooltipService,
  ) {
    const initialState = this.mapSyncService.getInitialViewState();
    this.options = {
      layers: [this.baseLayer],
      zoom: initialState.zoom,
      center: latLng(initialState.center.lat, initialState.center.lng),
      zoomControl: false,
    };
  }

  ngOnInit(): void {
    this.mapSyncService.viewState$
      .pipe(takeUntil(this.destroy$))
      .subscribe((state) => {
        this.syncViewState(state);
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['selectedOption'] && !changes['selectedOption'].firstChange) {
      this.updateLayers();
    }
  }

  onMapReady(map: Map): void {
    this.map = map;
    if (this.showZoomControl) {
      control.zoom({ position: 'bottomleft' }).addTo(map);
    }
    this.updateLayers();
  }

  onMove(): void {
    if (!this.isUpdatingFromSync && this.map) {
      const center = this.map.getCenter();
      const zoom = this.map.getZoom();
      this.mapSyncService.updateViewState({
        center: { lat: center.lat, lng: center.lng },
        zoom,
      });
    }
  }

  onZoom(): void {
    if (!this.isUpdatingFromSync && this.map) {
      const center = this.map.getCenter();
      const zoom = this.map.getZoom();
      this.mapSyncService.updateViewState({
        center: { lat: center.lat, lng: center.lng },
        zoom,
      });
    }
  }

  private syncViewState(state: MapViewState): void {
    if (!this.map) {
      return;
    }

    this.isUpdatingFromSync = true;
    this.map.setView([state.center.lat, state.center.lng], state.zoom, {
      animate: false,
    });

    setTimeout(() => {
      this.isUpdatingFromSync = false;
    }, 100);
  }

  private updateLayers(): void {
    this.removeCurrentLayers();

    if (this.selectedOption && this.map && this.month !== undefined) {
      this.rasterLayer = tileLayer(
        `${this.selectedOption.rasterUrl}_${this.month}/{z}/{x}/{y}.png`,
        {
          minZoom: 0,
          maxNativeZoom: this.selectedOption.rasterMaxZoom,
          maxZoom: 12,
          tileSize: 256,
          opacity: 0.8,
        },
      );

      this.vectorLayer = (window as any).L.vectorGrid.protobuf(
        `${this.selectedOption.vectorUrl}_${this.month}/{z}/{x}/{y}.pbf`,
        {
          vectorTileLayerStyles: {
            contours: (properties: any) => ({
              color: properties.stroke,
              weight: 1.5,
              opacity: 0.8,
            }),
          },
          interactive: true,
          maxNativeZoom: this.selectedOption.vectorMaxZoom,
          maxZoom: 18,
        },
      );

      this.vectorLayer?.on('mouseover', (e: any) => {
        this.onVectorLayerHover(e);
      });

      this.vectorLayer?.on('mouseout', () => {
        this.onVectorLayerMouseOut();
      });

      if (this.rasterLayer) {
        this.map.addLayer(this.rasterLayer);
      }
      if (this.vectorLayer) {
        this.map.addLayer(this.vectorLayer);
      }

      setTimeout(() => {
        this.map?.invalidateSize();
      }, 0);
    }
  }

  private removeCurrentLayers(): void {
    if (this.rasterLayer && this.map) {
      this.map.removeLayer(this.rasterLayer);
      this.rasterLayer = null;
    }
    if (this.vectorLayer && this.map) {
      this.map.removeLayer(this.vectorLayer);
      this.vectorLayer = null;
    }
    if (this.map) {
      this.tooltipManager.removeAllTooltips(this.map);
    }
  }

  private onVectorLayerHover(e: any): void {
    if (!this.map) {
      return;
    }

    const variableType = this.selectedOption?.metadata?.variableType || '';
    const unit = this.selectedOption?.climateMap?.variable?.unit || '';

    this.vectorLayerTooltip.handleVectorLayerHover(
      e,
      this.map,
      variableType,
      unit,
    );
  }

  private onVectorLayerMouseOut(): void {
    if (this.map) {
      this.vectorLayerTooltip.handleVectorLayerMouseOut(this.map);
    }
  }
}
