# climatemaps
Global monthly climate data visualised on an interactive map with [OpenLayers 3](https://github.com/openlayers/ol3).

## Demo
**http://climatemaps.romgens.com**

## Data
The climate grid data, 30 year averages, is taken from http://www.ipcc-data.org/obs/get_30yr_means.html.

## Dependencies

##### GDAL
GDAL is needed for the gdal2tiles.py script that creates map-tiles from a single images (matplotlib plot).

Install dependencies,
```bash
conda install -c conda-forge gdal==3.8.3
```

##### Tippecanoe
**WARNING**: tippecanoe 1.19.1 is the latest version that produces valid GeoJSON due to issue https://github.com/mapbox/tippecanoe/issues/652

```bash
sudo apt install libsqlite3-dev
git clone https://github.com/mapbox/tippecanoe.git
cd tippecanoe
git checkout tags/1.19.1
make -j
make install
```

## Create contours
Run:
```bash
python ./bin/create_contour.py
```
