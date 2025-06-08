import { Component, OnInit } from '@angular/core';
import { CommonModule, NgOptimizedImage, Location } from '@angular/common';
import { ActivatedRoute, ParamMap, RouterOutlet } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinner } from '@angular/material/progress-spinner';

import { LeafletModule } from '@bluehalo/ngx-leaflet';
import {
  Control,
  latLng, Layer,
  LeafletEvent,
  LeafletMouseEvent,
  Map,
  tileLayer
} from "leaflet";
import 'leaflet.vectorgrid';  // bring in the vectorgrid plugin

import { environment } from '../../environments/environment';
import { MonthSliderComponent } from "./month-slider.component";
import { YearSliderComponent } from "./year-slider.component";
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatSelectModule } from "@angular/material/select";
import { ClimateMapService } from "../core/climatemap.service";

interface LayerOption {
  name: string;
  rasterUrl: string;
  vectorUrl: string;
}


@Component({
  selector: 'app-map',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    NgOptimizedImage,
    LeafletModule,
    MatIconModule,
    MatSidenavModule,
    MatButtonModule,
    MatCardModule,
    MatProgressSpinner,
    MatFormFieldModule,
    MatSelectModule,
    MonthSliderComponent,
    YearSliderComponent,
  ],
  templateUrl: './map.component.html',
  styleUrl: './map.component.scss',
})
export class MapComponent implements OnInit {
  private readonly ZOOM_DEFAULT: number = 5;
  layerOptions: LayerOption[] = [];
  selectedOption!: LayerOption;

  Object = Object;
  private baseLayer = tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      maxZoom: 20,
      attribution: '...',
    },
  );
  options = {
    layers: [this.baseLayer],
    zoom: this.ZOOM_DEFAULT,
    center: latLng(52.1, 5.58),
  };
  sidebarOpened = false;
  debug = !environment.production;

  private map: Map | null = null;
  private readonly control: Control.Layers;
  private rasterLayer: Layer | null = null;
  private vectorLayer: Layer | null = null;

  constructor(
    private route: ActivatedRoute,
    private location: Location,
    private climatemapService: ClimateMapService
  ) {
    this.control = new Control.Layers(undefined, undefined, {
      collapsed: false,
    });
  }

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      if (params.has('lat') && params.has('lon') && params.has('zoom')) {
        this.updateLocationZoomFromURL(params);
      }
    });
    this.climatemapService.getClimateMapList().subscribe(climateMaps => {
      console.log(climateMaps);
      const layerOptions: LayerOption[] = [];
      for (const climateMap of climateMaps) {
        layerOptions.push({
          name: `${climateMap.variable.displayName} (${climateMap.variable.unit})`,
          rasterUrl: `${climateMap.tiles_url}_1_raster`,
          vectorUrl: `${climateMap.tiles_url}_1_vector`,
        });
      }
      this.layerOptions = layerOptions;
      this.selectedOption = layerOptions[0];
      this.initializeLayers();
    })
  }

  onLayerChange() {
    this.initializeLayers();
  }

  private initializeMap(): void {
    console.log('initializeMap');
    if (!this.map) {
      console.assert(false, 'map is not defined');
      return;
    }
    this.update();
    this.addControls();
  }

  private initializeLayers(): void {
    console.log('initializeLayers selectedOption', this.selectedOption);

    console.log('initializeLayers rasterLayer', this.rasterLayer);
    console.log('initializeLayers vectorLayer', this.vectorLayer);
    if (this.rasterLayer) {
      console.log('remove raster layer');
      this.map?.removeLayer(this.rasterLayer);
    }
    if (this.vectorLayer) {
      console.log('remove vector layer');
      this.map?.removeLayer(this.vectorLayer);
    }

    this.rasterLayer = tileLayer(
      `${this.selectedOption.rasterUrl}/{z}/{x}/{y}.png`,
      {
        // attribution: '&copy; My Raster Tiles',
        minZoom: 0,
        maxNativeZoom: 4,
        maxZoom: 12,
        tileSize: 256,
        opacity: 0.5
        // tms: true, // uncomment if your MBTiles uses TMS y‐axis
      }
    );

    this.vectorLayer = (window as any).L.vectorGrid.protobuf(
      `${this.selectedOption.vectorUrl}/{z}/{x}/{y}.pbf`,
      {
        vectorTileLayerStyles: {
          // the layer name "1geojson" must match what your tileserver outputs
          "1geojson": (properties: any, zoom: number) => ({
            color: properties.stroke,
            weight: 2,
            opacity: 1
          })
        },
        interactive: true,
        maxNativeZoom: 6,
        maxZoom: 18
      }
    );

    // configure map options
    if (this.rasterLayer) {
      this.map?.addLayer(this.rasterLayer);
    }
    if (this.vectorLayer) {
      this.map?.addLayer(this.vectorLayer);
    }
  }

  private addControls() {
    if (!this.map) {
      console.assert(false, 'map is not defined');
      return;
    }
    this.control.addTo(this.map);
    new Control.Scale().addTo(this.map);
  }

  private update(): void {
    console.log('update');
    if (!this.map) {
      console.assert(false, 'map is not defined');
      return;
    }
  }

  private updateLocationZoomFromURL(params: ParamMap) {
    const lat = Number(params.get('lat'));
    const lon = Number(params.get('lon'));
    const zoom = Number(params.get('zoom'));
    if (lat === null || lon === null || zoom === null) {
      return;
    }
    this.options.center = latLng(lat, lon);
    this.options.zoom = zoom;
    this.map?.setView([lat, lon], zoom);
  }

  onMapClick(event: LeafletMouseEvent): void {
    console.log('mapClick', event);
  }

  onMapReady(map: Map): void {
    this.map = map;
    this.initializeMap();
  }

  onMove(event: LeafletEvent): void {
    console.log('onMove', event);
    this.update();
    this.updateUrlWithLocationZoom();
  }

  onZoom(event: LeafletEvent): void {
    console.log('onZoom: level', this.map?.getZoom(), event);
    this.updateUrlWithLocationZoom();
  }

  private updateUrlWithLocationZoom(): void {
    if (!this.map) {
      return;
    }
    const center = this.map.getCenter();
    const zoom = this.map.getZoom();
    const url = new URL(window.location.href);
    url.searchParams.set('lat', center.lat.toFixed(6));
    url.searchParams.set('lon', center.lng.toFixed(6));
    url.searchParams.set('zoom', String(zoom));
    this.location.replaceState(url.pathname + url.search);
  }
}
