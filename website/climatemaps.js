
// http://stackoverflow.com/a/4234006
$.ajaxSetup({beforeSend: function(xhr) {
    if (xhr.overrideMimeType)
    {
      xhr.overrideMimeType("application/json");
    }
}
});

var dataDir = "data/";

var map = new ol.Map({
    target: 'map',
    interactions: ol.interaction.defaults({keyboard:false}),  // disable because this moves the map when using the arrow keys to change the slider
});

var view = new ol.View( {center: [0, 0], zoom: 3, projection: 'EPSG:3857'} );
map.setView(view);

var osmSource = new ol.source.OSM("OpenCycleMap");
osmSource.setUrl("http://a.tile.opencyclemap.org/transport/{z}/{x}/{y}.png");
//osmSource.setUrl("http://a.tile.openstreetmap.org/{z}/{x}/{y}.png");
//osmSource.setUrl("https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png");
//osmSource.setUrl("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png");

var osmLayer = new ol.layer.Tile({source: osmSource});

map.addLayer(osmLayer);

var lon = 0.0;
var lat = 10.0;
view.setCenter(ol.proj.fromLonLat([lon, lat]));

var plotTypesMonthsLayers = {};
var plotTypesMonthsImages = {};


//
//var imageLayer = createImageLayer('precipitation', 1);
//
//map.addLayer(imageLayer);

function createImageLayer(dataType, monthNr) {
//    var extent = ol.extent.applyTransform([-180, -85, 180, 85], ol.proj.getTransform("EPSG:4326", "EPSG:3857"));
//    console.log(extent);
    return new ol.layer.Tile({
        source: new ol.source.XYZ({
            url: dataDir + dataType + '/' + monthNr + '/maptiles/{z}/{x}/{-y}.png',
            projection: "EPSG:3857",
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


function addContours(dataType, monthNr)
{
    var contourLayer = createContoursLayer(dataType, monthNr);
    if ( !(dataType in plotTypesMonthsLayers)) {
        plotTypesMonthsLayers[dataType] = {};
        plotTypesMonthsImages[dataType] = {};
    }
    var imageLayer = createImageLayer(dataType, monthNr);
    map.addLayer(imageLayer);
    plotTypesMonthsImages[dataType][monthNr] = imageLayer;
    plotTypesMonthsLayers[dataType][monthNr] = contourLayer;
}


function getImageOpacity() {
    var zoomedOut = 0.7;
    var zoomLevelToStart = 5;
    var zoom = view.getZoom();
    if (zoom < zoomLevelToStart) {
        return zoomedOut;
    }
    return zoomedOut - (view.getZoom()-zoomLevelToStart) / 5.0;
}


var lineStyleFunction = function(feature, resolution) {
    var scaleForPixelDensity = dpi_x/96.0;
    var lineWidth = feature.get('stroke-width') * scaleForPixelDensity * Math.pow(map.getView().getZoom()/2.0, 1.3)
    var lineStyle = new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: feature.get('stroke'),
            width: lineWidth,
            opacity: 0.0 //feature.get('opacity')
//            width: map.getView().getZoom(),
        })
    });
    return lineStyle
};

function createContoursLayer(dataType, monthNr) {
    console.log('create new contour layers');
    console.log(dataDir + dataType + '/' + monthNr + '/tiles/{z}/{x}/{y}.geojson')

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
    map.addLayer(contourLayer);
    return contourLayer;
}

// increase contour line width when zooming
map.getView().on('change:resolution', function(evt) {
    for (var type in plotTypesMonthsLayers) {
        for (var month in plotTypesMonthsLayers[type]) {
            plotTypesMonthsLayers[type][month].setStyle(lineStyleFunction);
        }
    }
});


map.addControl(new ol.control.FullScreen());
map.addControl(new ol.control.ZoomSlider());

// Tooltip

var info = $('#info');
var firstTooltipShown = false;

var displayFeatureInfo = function(pixel) {
    info.css({
        left: (pixel[0] + 10) + 'px',
        top: (pixel[1] - 50) + 'px',
    });

    var feature = map.forEachFeatureAtPixel(pixel, function(feature) {
        return feature;
     });

    if (feature) {
        var title = feature.get('title');
        if (title) {
            firstTooltipShown = true;
            info.text(title);
            info.show();
        } else if (!firstTooltipShown) {
            info.text("Tip: hover over lines to show their value.");
            info.show();
        } else {
            info.hide();
        }
    } else {
        info.hide();
    }
};


map.on('pointermove', function(evt) {
    if (evt.dragging) {
        info.hide();
        return;
    }
    displayFeatureInfo(map.getEventPixel(evt.originalEvent));
});


var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan"];


$(function() {
    $("#month-slider").slider({
      orientation: "horizontal",
      range: "min",
      min: 0,
      max: 12,
      value: 0,
      slide: sliderChanged,
      change: sliderChanged
    })
    .slider("pips", {
        rest: "label",
        labels: months
    });
//    .slider("float");
});


var hideAllContours = function() {
    console.log('hide all contours');
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
};


var showOrCreateContour = function(monthNr) {
    console.log("showOrCreateContour");
    hideAllContours();
    var selectedType = getSelectedType();
    if ( !plotExists(selectedType, monthNr) ) {
        addContours(selectedType, monthNr);
    }
    else {
        var monthLayer = plotTypesMonthsLayers[selectedType][monthNr];
        var monthImage = plotTypesMonthsImages[selectedType][monthNr];
        monthImage.setVisible(true);
        monthLayer.setVisible(true);
    }
};

var setSliderValue = function(monthNr) {
    console.log('set slider value')
    var slider = $("#month-slider");
    if (monthNr >= 13) {
        slider.slider("value", 0);
//    } else if (getSliderValue() != monthNr-1) {
    } else {
        slider.slider("value", monthNr-1);
    };
};


var getSliderValue = function() {
    var slider = $("#month-slider");
    return slider.slider("value");
};


var sliderChanged = function() {
    var slider = $("#month-slider");
    var monthNr = getSliderValue() + 1;
    if (monthNr == 13) {
        slider.slider("value", 0);
        monthNr = 1;
    }
    console.log("slider changed to: " + monthNr);

    showOrCreateContour(monthNr);
    updateColorBarLegend(getSelectedType(), monthNr);
};


var updateColorBarLegend = function(dataType, monthNr) {
    var colorBarImage = document.getElementById('colorbar-image');
    var imageUrl = dataDir + "/" + dataType + "/" + monthNr + "_colorbar.svg";
    colorBarImage.setAttribute("src", imageUrl);
};


var intervalID = 0;

var toggleAnimation = function() {
    var playButton = document.getElementById('animate-button');
    var selectedType = getSelectedType();
    if (playButton.innerHTML == "Animate") {
        for (var i = 1; i < 13; ++i) {
            if ( !plotExists(selectedType, i) ) {
                addContours(selectedType, i);
            }
        }
        playButton.innerHTML = "Stop";
        intervalID = window.setInterval(playAnimation, 500);
    }
    else {
        window.clearInterval(intervalID);
        playButton.innerHTML = "Animate";
    }
};


var playAnimation = function() {
    var slider = $("#month-slider");
    var monthNr = slider.slider("value");
    slider.slider("value", monthNr+1);
};


document.getElementById("animate-button").onclick = toggleAnimation;


var selectDataType = function selectDataType(valueToSelect)
{
    var element = document.getElementById('select-type');
    element.value = valueToSelect;
}

var getSelectedType = function() {
    return document.getElementById("select-type").value;
};


var typeChanged = function() {
    var selection = getSelectedType();
    sliderChanged();
};


document.getElementById("select-type").onchange = typeChanged;

var plotExists = function(typeName, monthNr) {
    return typeName in plotTypesMonthsLayers && plotTypesMonthsLayers[typeName].hasOwnProperty(monthNr);
};


map.on("moveend", function() {
    // change image layer opacacity depending on zoom
    for (var type in plotTypesMonthsImages) {
        for (var month in plotTypesMonthsImages[type]) {
            plotTypesMonthsImages[type][month].setOpacity( getImageOpacity() );
        }
    }
});


var initialDataType = 'precipitation';
var initialMonth = 1;


var onLoad = function() {
    selectDataType(initialDataType);
    typeChanged();
    setSliderValue(initialMonth);
//    addContours(initialDataType, initialMonth);  // initial contour of January
};

window.onload = onLoad;