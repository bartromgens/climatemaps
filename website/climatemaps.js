(function () {
   'use strict';
}());

// http://stackoverflow.com/a/4234006
$.ajaxSetup({
  beforeSend: function(xhr) {
    if (xhr.overrideMimeType)
    {
      xhr.overrideMimeType('application/json');
    }
  }
});

function getSelectedType() {
  return document.getElementById('select-type').value;
}

var dataDir = 'data/';
var firstTooltipShown = false;

var climateMap = (function() {
  var lon = 0.0;
  var lat = 10.0;

  var map = new ol.Map({
    target: 'map',
    interactions: ol.interaction.defaults({keyboard:false}),  // disable because this moves the map when using the arrow keys to change the slider
  });

  var view = new ol.View({
    center: [0, 0],
    zoom: 3,
    projection: 'EPSG:3857'
  });

  view.setCenter(ol.proj.fromLonLat([lon, lat]));
  map.setView(view);

  var osmSource = new ol.source.OSM('OpenCycleMap');
  // osmSource.setUrl("https://a.tile.thunderforest.com/transport/{z}/{x}/{y}.png?apikey=");  // needs an api key, get one at thunderforest.com
  osmSource.setUrl('http://a.tile.openstreetmap.org/{z}/{x}/{y}.png');
  //osmSource.setUrl('https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png');
  //osmSource.setUrl('http://a.tile.stamen.com/toner/{z}/{x}/{y}.png');

  var osmLayer = new ol.layer.Tile({source: osmSource});
  map.addLayer(osmLayer);
  map.addControl(new ol.control.FullScreen());
  //map.addControl(new ol.control.ZoomSlider());

  return map;
})();


var contourPlot = (function() {
  var plotTypesMonthsLayers = {};
  var plotTypesMonthsImages = {};

  function hideAllContours() {
    var type;
    var month;
    for (type in plotTypesMonthsLayers) {
      for (month in plotTypesMonthsLayers[type]) {
        plotTypesMonthsLayers[type][month].setVisible(false);
      }
    }

    for (type in plotTypesMonthsImages) {
      for (month in plotTypesMonthsImages[type]) {
        plotTypesMonthsImages[type][month].setVisible(false);
      }
    }
  }

  function lineStyleFunction(feature, resolution) {
    var scaleForPixelDensity = 1.0; //dpi_x/96.0;
    var lineWidth = feature.get('stroke-width') * scaleForPixelDensity * Math.pow(climateMap.getView().getZoom()/2.0, 1.3);
    var lineStyle = new ol.style.Style({
      stroke: new ol.style.Stroke({
        color: feature.get('stroke'),
        width: lineWidth,
        opacity: 0.0 //feature.get('opacity')
        //            width: climateMap.getView().getZoom(),
      })
    });
    return lineStyle;
  }

  function createContoursLayer(dataType, monthNr) {
    var contourLayer = new ol.layer.VectorTile({
      source: new ol.source.VectorTile({
        url: dataDir + dataType + '/' + monthNr + '/tiles/{z}/{x}/{y}.geojson',
        format: new ol.format.GeoJSON(),
        projection: 'EPSG:3857',
        tileGrid: ol.tilegrid.createXYZ({
          maxZoom: 5,
          minZoom: 1,
          tileSize: [256, 256]
        }),
      }),
      style: lineStyleFunction
    });

    contourLayer.setZIndex(99);
    climateMap.addLayer(contourLayer);
    return contourLayer;
  }

  function getImageOpacity() {
    var zoomedOut = 0.7;
    var zoomLevelToStart = 5;
    var zoom = climateMap.getView().getZoom();
    if (zoom < zoomLevelToStart) {
      return zoomedOut;
    }
    return zoomedOut - (climateMap.getView().getZoom()-zoomLevelToStart) / 5.0;
  }

  function createImageLayer(dataType, monthNr) {
    //    var extent = ol.extent.applyTransform([-180, -85, 180, 85], ol.proj.getTransform('EPSG:4326', 'EPSG:3857'));
    //    console.log(extent);
    return new ol.layer.Tile({
      source: new ol.source.XYZ({
        url: dataDir + dataType + '/' + monthNr + '/maptiles/{z}/{x}/{-y}.png',
        projection: 'EPSG:3857',
        wrapX: false,
        tileGrid: ol.tilegrid.createXYZ({
          maxZoom: 5,
          minZoom: 1,
          tileSize: [256, 256]
        }),
      }),
      opacity: getImageOpacity()
    });
  }

  // increase contour line width when zooming
  climateMap.getView().on('change:resolution', function(evt) {
    for (var type in plotTypesMonthsLayers) {
      for (var month in plotTypesMonthsLayers[type]) {
        plotTypesMonthsLayers[type][month].setStyle(lineStyleFunction);
      }
    }
  });

  return Object.freeze({
    showOrCreateContour: function(monthNr) {
      hideAllContours();
      var selectedType = getSelectedType();
      if ( !this.plotExists(selectedType, monthNr) ) {
        this.addContours(selectedType, monthNr);
      }
      else {
        var monthImage = plotTypesMonthsImages[selectedType][monthNr];
        var monthLayer = plotTypesMonthsLayers[selectedType][monthNr];
        monthImage.setVisible(true);
        monthLayer.setVisible(true);
      }
    },
    addContours: function(dataType, monthNr) {
      var contourLayer = createContoursLayer(dataType, monthNr);
      if ( !(dataType in plotTypesMonthsLayers)) {
        plotTypesMonthsLayers[dataType] = {};
        plotTypesMonthsImages[dataType] = {};
      }
      var imageLayer = createImageLayer(dataType, monthNr);
      climateMap.addLayer(imageLayer);
      plotTypesMonthsImages[dataType][monthNr] = imageLayer;
      plotTypesMonthsLayers[dataType][monthNr] = contourLayer;
    },
    plotExists: function(typeName, monthNr) {
      return typeName in plotTypesMonthsLayers && plotTypesMonthsLayers[typeName].hasOwnProperty(monthNr);
    },
    updateOnZoom: function() {
      for (var type in plotTypesMonthsImages) {
        for (var month in plotTypesMonthsImages[type]) {
          plotTypesMonthsImages[type][month].setOpacity( getImageOpacity() );
        }
      }
    }
  });
})();

var colorbarLegend = (function() {
  return Object.freeze({
    update: function(dataType, monthNr) {
      var colorBarImage = document.getElementById('colorbar-legend-container');
      var imageUrl = dataDir + dataType + '/' + monthNr + '_colorbar.png';
      colorBarImage.style.backgroundImage = 'url(' + imageUrl + ')';
    }
  });
})();

var slider = (function() {
  var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan'];

  function slide(event, ui) {
    var monthNr = ui.value + 1;
    if (monthNr == 13) {
      $('#month-slider').slider('value', 0);
      monthNr = 1;
    }

    contourPlot.showOrCreateContour(monthNr);
    colorbarLegend.update(getSelectedType(), monthNr);
  }

  function update() {
    var monthNr = $('#month-slider').slider('value') + 1;
    if (monthNr == 13) {
      $('#month-slider').slider('value', 0);
      monthNr = 1;
    }

    contourPlot.showOrCreateContour(monthNr);
    colorbarLegend.update(getSelectedType(), monthNr);
  }

  function init() {
    $('#month-slider').slider({
      orientation: 'horizontal',
      range: 'min',
      min: 0,
      max: 12,
      value: 0,
      slide: slide,
      change: update
    })
    .slider('pips', {
      rest: 'label',
      labels: months
    });
    //    .slider('float');
  }

  return Object.freeze({
    update: update,
    init: init
  });
})();


var animationID = 0;

$(document).ready( function(){
  $('#info').hide();

  slider.init();

  function toggleAnimate() {
    function playAnimation() {
      var monthNr = $('#month-slider').slider('value');
      $('#month-slider').slider('value', monthNr+1);
    }

    var playButton = document.getElementById('animate-button');
    var selectedType = getSelectedType();
    if (playButton.innerHTML == 'Animate') {
      for (var i = 1; i < 13; ++i) {
        if ( !contourPlot.plotExists(selectedType, i) ) {
          contourPlot.addContours(selectedType, i);
        }
      }
      playButton.innerHTML = 'Stop';
      animationID = window.setInterval(playAnimation, 800);
    }
    else {
      window.clearInterval(animationID);
      playButton.innerHTML = 'Animate';
    }
  }

  document.getElementById('animate-button').onclick = toggleAnimate;

  document.getElementById('select-type').onchange = function() {
    var selection = getSelectedType();
    slider.update();
  };

  climateMap.on('moveend', function() {
    contourPlot.updateOnZoom();
  });

  climateMap.on('pointermove', function(evt) {
    var info = $('#info');

    function displayFeatureInfo(pixel) {
      info.css({
        left: (pixel[0] + 10) + 'px',
        top: (pixel[1] - 50) + 'px',
      });

      var feature = climateMap.forEachFeatureAtPixel(pixel, function(feature) {
        return feature;
      });

      if (feature) {
        var title = feature.get('title');
        if (title) {
          firstTooltipShown = true;
          info.text(title);
          info.show();
        } else if (!firstTooltipShown) {
          info.text('Tip: hover over lines to show their value.');
          info.show();
        } else {
          info.hide();
        }
      } else {
        info.hide();
      }
    }

    if (evt.dragging) {
      info.hide();
      return;
    }
    displayFeatureInfo(climateMap.getEventPixel(evt.originalEvent));
  });
});

window.onload = function() {
  var initialDataType = 'precipitation';
  var initialMonth = 1;

  function selectDataType(valueToSelect) {
    var element = document.getElementById('select-type');
    element.value = valueToSelect;
  }

  function setSliderValue(monthNr) {
    if (monthNr >= 13) {
      $('#month-slider').slider('value', 0);
    } else {
      $('#month-slider').slider('value', monthNr-1);
    }
  }

  selectDataType(initialDataType);
  setSliderValue(initialMonth);
  //    addContours(initialDataType, initialMonth);  // initial contour of January
};
