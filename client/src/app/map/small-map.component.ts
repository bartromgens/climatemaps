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
import { latLng, Layer, LeafletEvent, Map, tileLayer } from 'leaflet';
import 'leaflet.vectorgrid';
import { Subject, takeUntil } from 'rxjs';

import { MapSyncService, MapViewState } from './services/map-sync.service';
import { LayerOption } from './services/layer-builder.service';

@Component({
  selector: 'app-small-map',
  standalone: true,
  imports: [CommonModule, LeafletModule],
  template: `
    <div class="small-map-container">
      <div class="month-label">{{ monthName }}</div>
      <div
        class="map-wrapper"
        leaflet
        [leafletOptions]="options"
        (leafletMapReady)="onMapReady($event)"
        (leafletMapMoveEnd)="onMove($event)"
        (leafletMapZoomEnd)="onZoom($event)"
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

      .month-label {
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
  @Input() month!: number;
  @Input() selectedOption: LayerOption | undefined;

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

  options = {
    layers: [this.baseLayer],
    zoom: 5,
    center: latLng(52.1, 5.58),
    zoomControl: false,
  };

  get monthName(): string {
    const monthNames = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];
    return monthNames[this.month - 1] || '';
  }

  constructor(private mapSyncService: MapSyncService) {}

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
    this.updateLayers();
  }

  onMove(event: LeafletEvent): void {
    if (!this.isUpdatingFromSync && this.map) {
      const center = this.map.getCenter();
      const zoom = this.map.getZoom();
      this.mapSyncService.updateViewState({
        center: { lat: center.lat, lng: center.lng },
        zoom,
      });
    }
  }

  onZoom(event: LeafletEvent): void {
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

    if (this.selectedOption && this.map) {
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
          interactive: false,
          maxNativeZoom: this.selectedOption.vectorMaxZoom,
          maxZoom: 18,
        },
      );

      if (this.rasterLayer) {
        this.map.addLayer(this.rasterLayer);
      }
      if (this.vectorLayer) {
        this.map.addLayer(this.vectorLayer);
      }
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
  }
}
