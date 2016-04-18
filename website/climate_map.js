
// http://stackoverflow.com/a/4234006
$.ajaxSetup({beforeSend: function(xhr){
    if (xhr.overrideMimeType)
    {
      xhr.overrideMimeType("application/json");
    }
}
});

var dataDir = "./data/"

var map = new ol.Map({target: 'map'});
var view = new ol.View( {center: [0, 0], zoom: 3, projection: 'EPSG:3857'} );
map.setView(view);

var osmSource = new ol.source.OSM("OpenCycleMap");
//osmSource.setUrl("http://a.tile.opencyclemap.org/transport/{z}/{x}/{y}.png");
//osmSource.setUrl("http://a.tile.openstreetmap.org/{z}/{x}/{y}.png");
osmSource.setUrl("https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png");
//osmSource.setUrl("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png");

var osmLayer = new ol.layer.Tile({source: osmSource});

map.addLayer(osmLayer);

var lon = 360.0;
var lat = 0.0;
view.setCenter(ol.proj.fromLonLat([lon, lat]));

var contourMonthsLayers = {};

addContours(1);  // initial contourd of January


function addContours(monthNr)
{
    $.getJSON(dataDir + "contour_precipitation_" + monthNr + ".json", function(json) {
        var contours = json.contours;
        var contourLayers = createContoursLayer(contours, "Cloud coverage");
        contourMonthsLayers[monthNr] = contourLayers;
    });
}


function createContoursLayer(contours, name) {
    console.log('create new contour layers');
    console.log(contours.length + ' contours');
    var contourLayers = [];

    // each contour can have multiple (including zero) paths.
    for (var k = 0; k < contours.length; ++k)
    {
        var paths = contours[k].paths;
        for (var j = 0; j < paths.length; ++j)
        {
            var markers = [];
            for (var i = 0; i < paths[j].x.length; ++i)
            {
                var lon = paths[j].x[i]
                var lat = -paths[j].y[i]
                var lonLat = [lon, lat];
                markers.push(ol.proj.fromLonLat(lonLat));
            }

            var color = [paths[j].linecolor[0]*255, paths[j].linecolor[1]*255, paths[j].linecolor[2]*255, 0.8];
            var lineWidth = 4;
//            if ((k+1) % 6 == 0)
//            {
//                lineWidth = 8;
//            }

            var lineStyle = new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: color,
                    width: lineWidth
                })
            });

            var layerLines = new ol.layer.Vector({
                source: new ol.source.Vector({
                    features: [new ol.Feature({
                        geometry: new ol.geom.LineString(markers, 'XY'),
                        name: paths[j].label
                    })]
                }),
                style: lineStyle
            });

            contourLayers.push(layerLines);
            map.addLayer(layerLines);
        }
    }

    return contourLayers;
}


map.addControl(new ol.control.FullScreen());


// Tooltip

var info = $('#info');

var displayFeatureInfo = function(pixel) {
  info.css({
    left: (pixel[0] + 10) + 'px',
    top: (pixel[1] - 50) + 'px'
  });

  var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
    return feature;
  });

  if (feature) {
    info.text(feature.get('name'));
    info.show();
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


// Select features

//var select = new ol.interaction.Select({
//    condition: ol.events.condition.click
//});
//
//select.on('select', function(evt) {
//    for (var i = 0; i < contourLayers.length; ++i)
//    {
//        var removedLayer = map.removeLayer(contourLayers[i]);
//    }
//    contourLayers.length = 0;
//    addContours(1);
//});

//map.addInteraction(select);

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
    })
//    .slider("float");
});


var hideAllContours = function() {
    console.log('hide all contours');
    for (month in contourMonthsLayers) {
        for (var i = 0; i < contourMonthsLayers[month].length; ++i) {
            contourMonthsLayers[month][i].setVisible(false);
        };
    };
};


var showOrCreateContour = function(monthNr) {
    hideAllContours();
    if (!contourMonthsLayers.hasOwnProperty(monthNr)) {
        addContours(monthNr);
    }
    else {
        var monthLayers = contourMonthsLayers[monthNr];
        for (var i = 0; i < monthLayers.length; ++i) {
            monthLayers[i].setVisible(true);
        };
    };
};


var sliderChanged = function() {
    var monthNr = $("#month-slider").slider("value") + 1;
    if (monthNr == 13) {
        $("#month-slider").slider("value", 0);
        return;
    }
    console.log("slider changed to: " + monthNr);
    showOrCreateContour(monthNr);
};

var intervalID = 0;

var toggleAnimation = function() {
    playButton = document.getElementById('animate-button');
    if (playButton.innerHTML == "Animate") {
        for (var i = 1; i < 13; ++i) {
            if (!contourMonthsLayers.hasOwnProperty(i)) {
                addContours(i);
            };
        };
        playButton.innerHTML = "Stop";
        intervalID = window.setInterval(playAnimation, 500);
    }
    else {
        window.clearInterval(intervalID);
        playButton.innerHTML = "Animate";
    };
};

var stopAnimation = function() {
    window.clearInterval(intervalID);
};

var playAnimation = function() {
    var monthNr = $("#month-slider").slider("value");
    $("#month-slider").slider("value", monthNr+1);
};

document.getElementById('animate-button').onclick = toggleAnimation;

