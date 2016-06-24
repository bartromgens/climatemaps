# climatemaps
Global monthly climate data visualised on an interactive map with [OpenLayers 3](https://github.com/openlayers/ol3).

#### Demo
**http://climatemaps.romgens.com**

#### Data
The climate grid data, 30 year averages, is taken from http://www.ipcc-data.org/obs/get_30yr_means.html.

#### Dependencies

##### Basemap
Matplotlib-basemap has no pypi package and thus does not install via pip.
For install instructions see https://github.com/matplotlib/basemap. 

##### GDAL
GDAL 2.1 is needed for the gdal2tiles.py script that creates map-tiles from a single images (matplotlib plot).

Installation instructions for **Ubuntu 16.04**:  
Install dependencies,
```
$ sudo apt-get build-dep gdal
```
Build and install gdal-2.1.0 and the Python bindings,
```
$ wget http://download.osgeo.org/gdal/2.1.0/gdal-2.1.0.tar.gz
$ tar -xvf gdal-2.1.0.tar.gz
$ cd gdal-2.1.0/
$ ./configure --prefix=/usr/
$ make
$ sudo make install
$ cd swig/python/
$ sudo python setup.py install
```

##### Tippecanoe
...
