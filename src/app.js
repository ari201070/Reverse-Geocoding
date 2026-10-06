/* src/app.js - Visor Leaflet del lote Italia 02-12 Oct 2023 (Fase C).
 * Capa 1: 1254 puntos de fotos (Popup: archivo + ImageDescription).
 * Capa 2: 24 poligonos H3 res 9 como mascara visual.
 * Solo lectura: no altera propiedades de la BD ni del GeoJSON.
 */
/* global L */
(function () {
  'use strict';

  var GEOJSON_URL = '../data/italy_2023_oct02_12.geojson';
  var ROME_VIEW = [41.9028, 12.4964];
  var ZOOM = 13;

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function initMap() {
    var map = L.map('map').setView(ROME_VIEW, ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    fetch(GEOJSON_URL)
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        res.json().then(function (fc) {
          renderLayers(map, fc.features || []);
        }).catch(function (e) { showError(e); });
      })
      .catch(function (e) { showError(e); });
  }

  function renderLayers(map, features) {
    var points = features.filter(function (f) {
      return f.geometry && f.geometry.type === 'Point';
    });
    var hexes = features.filter(function (f) {
      return f.geometry && f.geometry.type === 'Polygon';
    });

    var photoLayer = L.geoJSON(points, {
      pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
          radius: 4, color: '#d33', weight: 1, fillOpacity: 0.8
        });
      },
      onEachFeature: function (feature, layer) {
        var p = feature.properties || {};
        var mapsUrl = 'https://www.openstreetmap.org/?mlat=' +
          encodeURIComponent(feature.geometry.coordinates[1]) +
          '&mlon=' + encodeURIComponent(feature.geometry.coordinates[0]) +
          '#map=16/' + encodeURIComponent(feature.geometry.coordinates[1]) +
          '/' + encodeURIComponent(feature.geometry.coordinates[0]);
        layer.bindPopup(
          '<b>' + esc(p.filename) + '</b><br>' +
          esc(p.place || p.ImageDescription || '') + '<br>' +
          '<a href="' + mapsUrl + '" target="_blank" rel="noopener">Ver en OpenStreetMap</a>'
        );
      }
    });

    var h3Layer = L.geoJSON(hexes, {
      style: function () {
        return { fillColor: '#3388ff', weight: 1, fillOpacity: 0.2, color: '#3388ff' };
      },
      onEachFeature: function (feature, layer) {
        var p = feature.properties || {};
        layer.bindPopup(
          'Celda H3: <b>' + esc(p.h3_index) + '</b><br>' +
          'Fotos: ' + esc(p.photo_count)
        );
      }
    });

    photoLayer.addTo(map);
    h3Layer.addTo(map);

    L.control.layers(
      { 'Fotos (1254)': photoLayer, 'Hexagonos H3 (24)': h3Layer },
      null,
      { collapsed: false }
    ).addTo(map);

    var counter = document.getElementById('counts');
    if (counter) {
      counter.textContent = points.length + ' fotos · ' + hexes.length + ' celdas H3';
    }
  }

  function showError(e) {
    var el = document.getElementById('counts');
    if (el) el.textContent = 'Error cargando GeoJSON: ' + e.message;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMap);
  } else {
    initMap();
  }
})();
