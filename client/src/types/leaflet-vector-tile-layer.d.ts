declare module 'leaflet-vector-tile-layer' {
  import { Layer } from 'leaflet';
  function vectorTileLayer(url: string, options?: any): Layer;
  export default vectorTileLayer;
}
