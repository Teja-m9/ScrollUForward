import React, { forwardRef, useImperativeHandle, useMemo, useRef, useState, useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import { WebView } from 'react-native-webview';

/*
  NotebookWorldMap
  ────────────────
  Real-world 3D map rendered with MapLibre GL JS + OpenFreeMap vector tiles
  (OSM data, no API key, no rate limits). Building footprints are extruded
  by their real heights and the camera is pitched so the view matches the
  isometric reference image. A paper/ink CSS filter over the canvas plus a
  ruled-paper overlay fold the whole thing into the notebook aesthetic.

  Props:
    me          { lat, lng, name }
    others      [{ user_id, display_name, username, latitude, longitude, km }]
    routeTo     { lat, lng }
    onReady     () => void
    style       style for the outer container

  Imperative methods (via ref):
    ref.current.recenter(lat, lng, zoom?)
*/
const NotebookWorldMap = forwardRef(function NotebookWorldMap(
  { me, others = [], routeTo, onReady, style },
  ref
) {
  const webRef = useRef(null);
  const [ready, setReady] = useState(false);
  const lastPayloadRef = useRef(null);

  // HTML is built ONCE. Marker/route updates happen via injectJavaScript.
  const html = useMemo(() => buildHtml(), []);

  // Push updates whenever props change AND map is ready. If the map isn't ready yet
  // we cache the payload and flush it the moment the 'ready' event arrives —
  // that's the fix for "my location never shows up".
  useEffect(() => {
    const payload = { me, others, routeTo };
    lastPayloadRef.current = payload;
    if (ready && webRef.current) {
      const js = `window.__updateMap && window.__updateMap(${JSON.stringify(payload)}); true;`;
      webRef.current.injectJavaScript(js);
    }
  }, [me, others, routeTo, ready]);

  useImperativeHandle(ref, () => ({
    recenter: (lat, lng, zoom = 17) => {
      webRef.current?.injectJavaScript(
        `window.__recenter && window.__recenter(${lat}, ${lng}, ${zoom}); true;`
      );
    },
  }));

  const handleMessage = (e) => {
    const data = e?.nativeEvent?.data;
    if (data === 'ready') {
      setReady(true);
      // Flush any cached payload immediately so the pin appears on first paint.
      if (lastPayloadRef.current && webRef.current) {
        const js = `window.__updateMap(${JSON.stringify(lastPayloadRef.current)}); true;`;
        webRef.current.injectJavaScript(js);
      }
      onReady?.();
    }
  };

  return (
    <View style={[StyleSheet.absoluteFill, style]}>
      <WebView
        ref={webRef}
        originWhitelist={['*']}
        source={{ html }}
        style={{ flex: 1, backgroundColor: '#FDF6E3' }}
        javaScriptEnabled
        domStorageEnabled
        setSupportMultipleWindows={false}
        // NB: do NOT use androidLayerType="hardware" — it hoists the WebView
        // onto an OS layer that paints OVER our React Native overlays
        // (header, trending bottom sheet). Default compositing is correct.
        mixedContentMode="always"
        allowFileAccess
        onMessage={handleMessage}
      />
    </View>
  );
});

export default NotebookWorldMap;

function buildHtml() {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<style>
  * { box-sizing: border-box; }
  html, body, #map {
    margin: 0; padding: 0; width: 100%; height: 100%;
    background: #FDF6E3;
    overflow: hidden;
  }
  body {
    font-family: Georgia, 'Times New Roman', serif;
    color: #2C1810;
  }

  /* ── Subtle paper warmth — keeps the colour vivid ── */
  #map .maplibregl-canvas {
    filter:
      saturate(1.18)
      contrast(1.08)
      brightness(1.02);
  }

  /* ── Ruled paper overlay (lighter so colour shows through) ── */
  #paperOverlay {
    position: absolute; inset: 0; pointer-events: none; z-index: 400;
    background-image:
      repeating-linear-gradient(
        to bottom,
        transparent 0px,
        transparent 27px,
        rgba(90,150,210,0.07) 27px,
        rgba(90,150,210,0.07) 28px
      );
    mix-blend-mode: multiply;
    opacity: 0.8;
  }
  #marginLine {
    position: absolute; top: 0; bottom: 0; left: 44px;
    width: 1.5px; background: rgba(200,55,55,0.18);
    pointer-events: none; z-index: 401;
  }
  /* Warm cream vignette to feel like aged paper edges */
  #paperWash {
    position: absolute; inset: 0; pointer-events: none; z-index: 399;
    background: radial-gradient(ellipse at center,
      rgba(253,246,227,0.0) 50%,
      rgba(253,246,227,0.20) 100%);
  }

  /* ── Hide MapLibre UI chrome ── */
  .maplibregl-ctrl-attrib,
  .maplibregl-ctrl-logo,
  .maplibregl-ctrl-top-right,
  .maplibregl-ctrl-top-left,
  .maplibregl-ctrl-bottom-left,
  .maplibregl-ctrl-bottom-right { display: none !important; }

  /* ── Notebook pin ── */
  .nb-pin {
    display: flex; flex-direction: column; align-items: center;
    pointer-events: auto;
    transform-origin: center bottom;
  }
  .nb-pin-bubble {
    width: 46px; height: 46px; border-radius: 23px;
    border: 2.5px solid #2C1810;
    background: #FFFCF2;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 2px 2px 0 #2C1810;
    animation: nbBob 2.6s ease-in-out infinite;
    position: relative;
  }
  @keyframes nbBob {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-4px); }
  }
  .nb-pin-avatar {
    width: 34px; height: 34px; border-radius: 17px;
    border: 1.5px solid #2C1810;
    color: #fff; font-weight: 900; font-size: 14px;
    display: flex; align-items: center; justify-content: center;
    text-transform: uppercase;
    font-family: Georgia, serif;
  }
  .nb-pin-tail {
    width: 0; height: 0;
    border-left: 7px solid transparent;
    border-right: 7px solid transparent;
    border-top: 10px solid #2C1810;
    margin-top: -2px;
    filter: drop-shadow(1px 1px 0 #2C1810);
  }
  .nb-pin-label {
    margin-top: 4px; padding: 3px 8px;
    border-radius: 4px; border: 1.5px solid #2C1810;
    font-size: 10px; font-weight: 900; color: #2C1810;
    letter-spacing: 0.6px;
    max-width: 180px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    box-shadow: 1px 1px 0 #2C1810;
    background: #FFF7ED;
    font-family: Georgia, serif;
  }
  .nb-pin.me .nb-pin-bubble::after {
    content: '';
    position: absolute;
    top: -2px; left: -2px; right: -2px; bottom: -2px;
    border-radius: 50%;
    border: 2px solid #2563EB;
    animation: nbPulse 2s ease-out infinite;
  }
  @keyframes nbPulse {
    0%   { transform: scale(1);   opacity: 0.7; }
    100% { transform: scale(2.3); opacity: 0; }
  }
</style>
</head>
<body>
  <div id="map"></div>
  <div id="paperWash"></div>
  <div id="paperOverlay"></div>
  <div id="marginLine"></div>

<script>
(function () {
  // ── Notebook colour palette (richer, notebook-illustration vibe) ─
  const INK       = '#2C1810';
  const PAPER     = '#FDF6E3';
  const WATER     = '#7DD3FC';    // vivid sketch-blue river/sea
  const WATER_LIP = '#38BDF8';    // darker water edge
  const PARK      = '#BBF7D0';    // bright mint for parks
  const FOREST    = '#86EFAC';    // deeper green for forests
  const SAND      = '#FEF3C7';    // beach/sand
  const ROAD_MOT  = '#FB923C';    // motorway — warm orange
  const ROAD_TRK  = '#FDBA74';    // trunk — lighter orange
  const ROAD_PRI  = '#FDE047';    // primary — yellow
  const ROAD_SEC  = '#FEF9C3';    // secondary — pale yellow
  const ROAD_MIN  = '#FFFCF2';    // local street — near-white cream
  const ROAD_CSG  = INK;          // casing

  const map = new maplibregl.Map({
    container: 'map',
    style: 'https://tiles.openfreemap.org/styles/liberty',
    center: [0, 20],
    zoom: 2,
    pitch: 40,        // gentler angle → less overlap between towers
    bearing: -12,
    attributionControl: false,
    maxPitch: 65,
    renderWorldCopies: true,
    fadeDuration: 100,
    antialias: true,
  });

  // Directional sun so 3D buildings get realistic shading
  map.on('styledata', () => {
    try {
      map.setLight({
        anchor: 'viewport',
        color: '#FFF7E6',
        intensity: 0.55,
        position: [1.15, 210, 28], // [radial distance, azimuth, polar]
      });
    } catch {}
  });

  // Friendlier interaction
  map.touchZoomRotate.enable();
  map.dragRotate.enable();

  const PIN_COLORS = ['#DC2626','#059669','#EC4899','#EA580C','#7C3AED','#0891B2','#CA8A04'];

  const markers = {};         // user_id → maplibregl.Marker
  let myMarker = null;
  let flownToSelf = false;

  function buildPinElement(color, letter, label, isMe) {
    const wrap = document.createElement('div');
    wrap.className = isMe ? 'nb-pin me' : 'nb-pin';
    const safe = (s) => String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    wrap.innerHTML = \`
      <div class="nb-pin-bubble">
        <div class="nb-pin-avatar" style="background:\${color}">\${safe(letter)}</div>
      </div>
      <div class="nb-pin-tail"></div>
      \${label ? \`<div class="nb-pin-label">\${safe(label)}</div>\` : ''}
    \`;
    return wrap;
  }

  function fmtKm(km) {
    return km < 1 ? Math.round(km * 1000) + ' m' : km.toFixed(1) + ' km';
  }

  // ── Recolour the vector style to rich notebook palette on load ──
  map.on('load', () => {
    try {
      const style = map.getStyle();
      const layers = style.layers || [];

      // Classify road layers by hierarchy keywords in the layer id
      const pickRoadColor = (id) => {
        const s = id.toLowerCase();
        if (/motorway|trunk|freeway|expressway/.test(s)) return ROAD_MOT;
        if (/primary/.test(s))   return ROAD_PRI;
        if (/secondary/.test(s)) return ROAD_SEC;
        if (/tertiary/.test(s))  return ROAD_SEC;
        if (/service|residential|minor|living|path|track|pedestrian|footway|cycleway/.test(s)) return ROAD_MIN;
        return ROAD_SEC;
      };

      layers.forEach(layer => {
        const id = layer.id;
        const lower = id.toLowerCase();

        // Background → paper cream
        if (layer.type === 'background') {
          try { map.setPaintProperty(id, 'background-color', PAPER); } catch {}
        }

        // Water variants
        if (/water|ocean|sea|river|lake|stream|pond|reservoir/.test(lower) && layer.type === 'fill') {
          try {
            map.setPaintProperty(id, 'fill-color', WATER);
            map.setPaintProperty(id, 'fill-outline-color', WATER_LIP);
          } catch {}
        }
        if (/water|river|stream/.test(lower) && layer.type === 'line') {
          try {
            map.setPaintProperty(id, 'line-color', WATER_LIP);
            map.setPaintProperty(id, 'line-width', 1);
          } catch {}
        }

        // Sand / beach
        if (/sand|beach/.test(lower) && layer.type === 'fill') {
          try { map.setPaintProperty(id, 'fill-color', SAND); } catch {}
        }

        // Forests vs parks (deeper green vs bright mint)
        if (/forest|wood/.test(lower) && layer.type === 'fill') {
          try { map.setPaintProperty(id, 'fill-color', FOREST); } catch {}
        } else if (/park|grass|meadow|landuse|landcover|garden|golf|cemetery/.test(lower) && layer.type === 'fill') {
          try { map.setPaintProperty(id, 'fill-color', PARK); } catch {}
        }

        // Road casings → ink outline (thicker)
        if ((/casing|outline/.test(lower)) && layer.type === 'line') {
          try {
            map.setPaintProperty(id, 'line-color', ROAD_CSG);
          } catch {}
        }
        // Road fills → hierarchy colour
        else if (/road|street|highway|motorway|trunk|primary|secondary|tertiary|service|residential|path|transportation/.test(lower)
                 && layer.type === 'line' && !/tunnel|bridge_outline|casing|outline|rail/.test(lower)) {
          try { map.setPaintProperty(id, 'line-color', pickRoadColor(id)); } catch {}
        }

        // Rail → dashed ink
        if (/rail|railway/.test(lower) && layer.type === 'line') {
          try {
            map.setPaintProperty(id, 'line-color', INK);
            map.setPaintProperty(id, 'line-dasharray', [3, 2]);
          } catch {}
        }

        // Labels → dark ink with cream halo
        if (layer.type === 'symbol') {
          try {
            map.setPaintProperty(id, 'text-color', INK);
            map.setPaintProperty(id, 'text-halo-color', '#FFFCF2');
            map.setPaintProperty(id, 'text-halo-width', 1.6);
          } catch {}
        }

        // Buildings — rich colour variety based on height, with a pseudo-random
        // warm/cool split so the city doesn't look monochrome.
        if (/building/.test(lower)) {
          if (layer.type === 'fill-extrusion') {
            try {
              // Match() mixes two palettes based on last digit of osm id — gives variety
              map.setPaintProperty(id, 'fill-extrusion-color', [
                'case',
                ['==', ['%', ['to-number', ['coalesce', ['id'], 0]], 3], 0],
                [
                  // Palette A — warm
                  'interpolate', ['linear'],
                  ['coalesce', ['get', 'render_height'], ['get', 'height'], 5],
                  0,   '#FCD9B6',
                  8,   '#FBBF8A',
                  18,  '#F97316',
                  30,  '#DC2626',
                  50,  '#B91C1C',
                  100, '#7C2D12'
                ],
                ['==', ['%', ['to-number', ['coalesce', ['id'], 0]], 3], 1],
                [
                  // Palette B — cool
                  'interpolate', ['linear'],
                  ['coalesce', ['get', 'render_height'], ['get', 'height'], 5],
                  0,   '#DBEAFE',
                  8,   '#93C5FD',
                  18,  '#60A5FA',
                  30,  '#3B82F6',
                  50,  '#2563EB',
                  100, '#1E3A8A'
                ],
                [
                  // Palette C — pink/purple
                  'interpolate', ['linear'],
                  ['coalesce', ['get', 'render_height'], ['get', 'height'], 5],
                  0,   '#FCE7F3',
                  8,   '#FBCFE8',
                  18,  '#F472B6',
                  30,  '#EC4899',
                  50,  '#DB2777',
                  100, '#9D174D'
                ]
              ]);
              map.setPaintProperty(id, 'fill-extrusion-opacity', 0.95);
              map.setPaintProperty(id, 'fill-extrusion-vertical-gradient', true);
              // Heights scaled down 40% so towers don't overlap their neighbours visually
              map.setPaintProperty(id, 'fill-extrusion-height', [
                '*',
                ['coalesce', ['get', 'render_height'], ['get', 'height'], 5],
                0.6,
              ]);
              map.setPaintProperty(id, 'fill-extrusion-base',
                ['coalesce', ['get', 'render_min_height'], ['get', 'min_height'], 0]);
            } catch {}
          } else if (layer.type === 'fill') {
            try {
              map.setPaintProperty(id, 'fill-color', '#FFE5C2');
              map.setPaintProperty(id, 'fill-outline-color', INK);
            } catch {}
          }
        }
      });

      // Thicker ink outline over 3D buildings — separates neighbours visually
      if (map.getSource('openmaptiles') && !map.getLayer('nb-building-outline')) {
        map.addLayer({
          id: 'nb-building-outline',
          type: 'line',
          source: 'openmaptiles',
          'source-layer': 'building',
          minzoom: 14,
          paint: {
            'line-color': INK,
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              14, 0.5,
              16, 1.2,
              18, 2.0,
            ],
            'line-opacity': 0.85,
          }
        });
      }

      // Live building-name labels — real OSM names, pulled from the vector tiles
      if (map.getSource('openmaptiles') && !map.getLayer('nb-building-name')) {
        map.addLayer({
          id: 'nb-building-name',
          type: 'symbol',
          source: 'openmaptiles',
          'source-layer': 'building',
          minzoom: 16.5,
          filter: ['has', 'name'],
          layout: {
            'text-field': ['get', 'name'],
            'text-size': ['interpolate', ['linear'], ['zoom'], 16, 10, 19, 13],
            'text-font': ['Noto Sans Regular'],
            'text-max-width': 8,
            'text-anchor': 'center',
            'text-allow-overlap': false,
            'text-padding': 4,
          },
          paint: {
            'text-color': INK,
            'text-halo-color': '#FFFCF2',
            'text-halo-width': 1.6,
          }
        });
      }

      // POI / landmark labels — encourage them to show (shops, parks, landmarks)
      layers.forEach(layer => {
        const id = layer.id;
        if (/poi|place/.test(id.toLowerCase()) && layer.type === 'symbol') {
          try {
            map.setLayoutProperty(id, 'visibility', 'visible');
            map.setPaintProperty(id, 'text-color', INK);
            map.setPaintProperty(id, 'text-halo-color', '#FFFCF2');
            map.setPaintProperty(id, 'text-halo-width', 1.6);
          } catch {}
        }
      });
    } catch (e) {
      console && console.warn && console.warn('recolor failed', e);
    }

    // Signal RN that we're ready to accept markers/route
    if (window.ReactNativeWebView) {
      window.ReactNativeWebView.postMessage('ready');
    }
  });

  // ── External update API ──────────────────────────────────────
  window.__updateMap = function (payload) {
    const { me, others, routeTo } = payload || {};

    // My marker
    if (me && typeof me.lat === 'number' && typeof me.lng === 'number') {
      const letter = (me.name || 'Y').charAt(0).toUpperCase();
      if (!myMarker) {
        const el = buildPinElement('#2563EB', letter, 'YOU', true);
        myMarker = new maplibregl.Marker({ element: el, anchor: 'bottom' })
          .setLngLat([me.lng, me.lat])
          .addTo(map);
      } else {
        myMarker.setLngLat([me.lng, me.lat]);
      }
      // Fly to self the FIRST time we get a fix
      if (!flownToSelf) {
        flownToSelf = true;
        map.flyTo({
          center: [me.lng, me.lat],
          zoom: 17,
          pitch: 40,
          bearing: -12,
          duration: 1400,
          essential: true,
        });
      }
    }

    // Friend markers — diff by user_id
    const nextIds = new Set((others || []).map(u => u.user_id));
    Object.keys(markers).forEach(k => {
      if (!nextIds.has(k)) { markers[k].remove(); delete markers[k]; }
    });
    (others || []).forEach((u, i) => {
      if (typeof u.latitude !== 'number' || typeof u.longitude !== 'number') return;
      const color = PIN_COLORS[i % PIN_COLORS.length];
      const letter = (u.display_name || u.username || '?').charAt(0).toUpperCase();
      const km = (typeof u.km === 'number') ? ' · ' + fmtKm(u.km) : '';
      const label = (u.display_name || u.username || 'user') + km;
      if (markers[u.user_id]) {
        markers[u.user_id].setLngLat([u.longitude, u.latitude]);
      } else {
        const el = buildPinElement(color, letter, label, false);
        markers[u.user_id] = new maplibregl.Marker({ element: el, anchor: 'bottom' })
          .setLngLat([u.longitude, u.latitude])
          .addTo(map);
      }
    });

    // Route line
    try { if (map.getLayer('nb-route'))  map.removeLayer('nb-route');  } catch {}
    try { if (map.getSource('nb-route')) map.removeSource('nb-route'); } catch {}
    if (me && routeTo && typeof me.lat === 'number' && typeof routeTo.lat === 'number') {
      map.addSource('nb-route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: [[me.lng, me.lat], [routeTo.lng, routeTo.lat]] }
        }
      });
      map.addLayer({
        id: 'nb-route',
        type: 'line',
        source: 'nb-route',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': '#EC4899',
          'line-width': 6,
          'line-opacity': 0.92,
          'line-dasharray': [2, 1.4],
        }
      });
    }
  };

  window.__recenter = function (lat, lng, zoom) {
    if (lat == null || lng == null) return;
    map.flyTo({
      center: [lng, lat],
      zoom: zoom || 17,
      pitch: 52,
      bearing: -17,
      duration: 1000,
      essential: true,
    });
  };
})();
</script>
</body>
</html>`;
}
