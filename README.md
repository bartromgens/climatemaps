# climatemaps
Global monthly climate data visualised on an interactive map with [OpenLayers 3](https://github.com/openlayers/ol3).

## Demo
**http://climatemaps.romgens.com**

## Data

### Historic
- The climate grid data, 30 year averages, is taken from http://www.ipcc-data.org/obs/get_30yr_means.html.
- Historic 1970-2000 WorldClim data: https://www.worldclim.org/data/worldclim21.html

### Projections (predictions)
- Copernicus Climate Data Store - CMIP6 climate projections:
https://cds.climate.copernicus.eu/datasets/projections-cmip6?tab=download

#### Downscaled (increasing the spatial resolution)
- WorldClim: Downscaled CMIP5 and CMIP6 model outputs for 2021–2100: https://www.worldclim.org/data/cmip6/cmip6_clim5m.html
- NASA NEX-GDDP-CMIP6  (~25 km resolution): https://registry.opendata.aws/nex-gddp-cmip6/
- CHELSA (~1km resolution): https://chelsa-climate.org/

### Visualizations
- https://interactive-atlas.ipcc.ch/

## Development

### Dependencies

##### GDAL
GDAL is needed for the gdal2tiles.py script that creates map-tiles from a single image (matplotlib plot).

Install GDAL with conda to prevent the need to install a hugh number of system level dependencies:
```bash
conda install -c conda-forge gdal==3.11.0
```

##### Tippecanoe
**WARNING**: tippecanoe 1.19.1 is the latest version that produces valid GeoJSON due to issue https://github.com/mapbox/tippecanoe/issues/652

TODO: migrate to active fork https://github.com/felt/tippecanoe

```bash
sudo apt install libsqlite3-dev
git clone https://github.com/mapbox/tippecanoe.git
cd tippecanoe
git checkout tags/1.19.1
make -j
make install
```

#### tileserver-gl
```bash
npm install -g tileserver-gl
```

### Run

#### Create contour data
Run:
```bash
python scrips/create_contour.py
```
to create contour and raster mbtiles.

#### Create tileserver config
```bash
python scripts/create_tileserver_config.py
```
to generate the tileserver config.

#### Run the backend (FastAPI server)
```bash
uvicorn api.main:app --reload
```

#### Run the tileserver (tileserver-gl)
```bash
tileserver-gl --config tileserver_config.json --port 8080
```

#### Run the client (Angular)
In `./client` run:
```bash
ng serve
```

### Tests
Run:
```bash
pytest
```

## Deployment (to openclimatemap.org)

### Everything
Deploy client and backend:
```bash
bash scripts/deploy.sh
```

### Client
Deploy the client angular app:
```bash
bash scripts/deploy_client.sh
```

### API and TileServer
```bash
bash scripts/deploy_backend.sh
```

