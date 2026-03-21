// Cliente: maneja UI, EXIF, mapa y llama al endpoint /api/find-poi (serverless)
// Migrado de Leaflet a Google Maps JS API y modernizado con Advanced Markers

let translations = {};
let currentLanguage = localStorage.getItem("language") || "es";

async function initI18n() {
  try {
    const response = await fetch(`/locales/${currentLanguage}.json`);
    translations = await response.json();
    applyTranslations();
  } catch (error) {
    console.error("Error loading translations:", error);
  }
}

function t(key) {
  return translations[key] || key;
}

function applyTranslations() {
  document.querySelectorAll("[data-t]").forEach(el => {
    const key = el.getAttribute("data-t");
    if (el.tagName === "INPUT" && el.getAttribute("placeholder")) {
      el.placeholder = t(key);
    } else {
      el.textContent = t(key);
    }
  });
  document.documentElement.lang = currentLanguage;
  document.documentElement.dir = currentLanguage === "he" ? "rtl" : "ltr";
}

const GLOBAL_MEMORY_KEY = "rg_global_poi_memory_v1";

function getGlobalMemory() {
  try {
    return JSON.parse(localStorage.getItem(GLOBAL_MEMORY_KEY) || "{}");
  } catch (e) { return {}; }
}

function saveToGlobalMemory(lat, lng, poi) {
  if (!lat || !lng || !poi || isGenericName(poi)) return;
  const memory = getGlobalMemory();
  // Geohash aproximado (4 decimales = ~11 metros de precisión)
  const key = `${lat.toFixed(4)},${lng.toFixed(4)}`;
  memory[key] = {
    poi: poi,
    ts: Date.now()
  };
  localStorage.setItem(GLOBAL_MEMORY_KEY, JSON.stringify(memory));
}

function findInGlobalMemory(lat, lng) {
  if (!lat || !lng) return null;
  const memory = getGlobalMemory();
  const key = `${lat.toFixed(4)},${lng.toFixed(4)}`;
  return memory[key] ? memory[key].poi : null;
}

let _gMapsPromise = null;

async function loadGoogleMapsApi() {
  if (window.google && window.google.maps && window.google.maps.importLibrary) {
    return Promise.resolve();
  }
  if (_gMapsPromise) return _gMapsPromise;

  _gMapsPromise = (async () => {
    try {
      const configRes = await fetch('/api/config');
      const config = await configRes.json();
      const apiKey = config.googleMapsApiKey || config.GOOGLE_MAPS_API_KEY;
      
      if (!apiKey) {
        throw new Error("Google Maps API Key not found in config");
      }

      return new Promise((resolve, reject) => {
        // Idempotent loader stub
        (g=>{var h,a,k,p="The Google Maps JavaScript API",c="google",l="importLibrary",q="__ib__",m=document,b=window;b=b[c]||(b[c]={});var d=b.maps||(b.maps={}),r=new Set,e=new URLSearchParams,u=()=>h||(h=new Promise(async(f,n)=>{await (a=m.createElement("script"));e.set("libraries",[...r]+"");for(k in g)e.set(k.replace(/[A-Z]/g,t=>"_"+t[0].toLowerCase()),g[k]);e.set("callback",c+".maps."+q);a.src=`https://maps.${c}apis.com/maps/api/js?`+e;d[q]=f;a.onerror=()=>h=n(Error(p+" could not load."));a.nonce=m.querySelector("script[nonce]")?.nonce||"";m.head.append(a)}));d[l]?(console.log(p+" already loading..."),r.add(g.libraries)):d[l]=(f,...n)=>r.add(f)&&u().then(()=>d[l](f,...n))})({
          key: apiKey,
          v: "weekly"
        });
        
        const check = setInterval(() => {
          if (window.google && window.google.maps && window.google.maps.importLibrary) {
            clearInterval(check);
            resolve();
          }
        }, 100);
        setTimeout(() => { clearInterval(check); reject(new Error("Timeout loading Google Maps")); }, 10000);
      });
    } catch (err) {
      _gMapsPromise = null; 
      console.error("Error loading Google Maps API:", err);
      throw err;
    }
  })();

  return _gMapsPromise;
}

// Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('SW Registered', reg))
      .catch(err => console.error('SW Registration failed', err));
  });
}

const el = {
  consent: document.getElementById("consent"),
  anonymize: document.getElementById("anonymize"),
  radiusRange: document.getElementById("radiusRange"),
  radiusValue: document.getElementById("radiusValue"),
  mapDiv: document.getElementById("map"),
  photosList: document.getElementById("photosList"),
  albumGallery: document.getElementById("albumGallery"),
  placeDetails: document.getElementById("placeDetails"),
  selectedInfo: document.getElementById("selectedInfo"),
  placesList: document.getElementById("placesList"),
  // Batch Modal Elements
  batchModal: document.getElementById("batchModal"),
  importBatchBtn: document.getElementById("importBatchBtn"),
  closeBatchBtn: document.getElementById("closeBatchBtn"),
  cancelBatchBtn: document.getElementById("cancelBatchBtn"),
  dropZone: document.getElementById("dropZone"),
  batchFileInput: document.getElementById("batchFileInput"),
  batchPreview: document.getElementById("batchPreview"),
  saveBatchBtn: document.getElementById("saveBatchBtn"),
  commonDesc: document.getElementById("commonDesc"),
  imagesInput: document.getElementById("imagesInput"),
  usePicarta: document.getElementById("usePicarta"),
  langSelector: document.getElementById("langSelector"),
};

let batchFiles = []; // To store current batch files and their metadata
let map, photoMarker, radiusCircle;
let albumMarkers = []; // v4.6: For multiple album markers
let AdvancedMarkerElement;
let currentSelected = null;

// --- Batch Modal Logic ---

el.importBatchBtn.addEventListener("click", () => {
  el.batchModal.style.display = "block";
});

el.closeBatchBtn.addEventListener("click", () => closeModal());
el.cancelBatchBtn.addEventListener("click", () => closeModal());

window.addEventListener("click", (e) => {
  if (e.target === el.batchModal) closeModal();
});

function closeModal() {
  el.batchModal.style.display = "none";
  batchFiles = [];
  el.batchPreview.innerHTML = "";
  el.saveBatchBtn.disabled = true;
  el.commonDesc.value = "";
}

el.dropZone.addEventListener("click", () => el.batchFileInput.click());
el.dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  el.dropZone.classList.add("dragover");
});
el.dropZone.addEventListener("dragleave", () => el.dropZone.classList.remove("dragover"));
el.dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  el.dropZone.classList.remove("dragover");
  processBatchFiles(e.dataTransfer.files);
});
el.batchFileInput.addEventListener("change", (e) => processBatchFiles(e.target.files));

async function processBatchFiles(files) {
  if (!files.length) return;
  el.saveBatchBtn.disabled = false;
  const fileArray = Array.from(files);
  const items = [];

  // --- Phase 0: Immediate UI Skeleton ---
  for (const file of fileArray) {
    const isImage = file.type.startsWith("image/");
    const id = `${file.name}-${file.size}-${file.lastModified}`;
    const batchItem = {
      file, id, title: file.name, lat: null, lng: null, date: 0, poi: null, consensus: false, visionLabels: [], isImage
    };

    const itemEl = document.createElement("div");
    itemEl.className = "batch-item";
    itemEl.innerHTML = `
      <img src="${isImage ? URL.createObjectURL(file) : 'https://img.icons8.com/color/96/000000/video.png'}" />
      <div class="batch-item-fields">
        <input type="text" class="batch-title" value="${file.name}" placeholder="${t('app_title')}..." />
        <input type="text" class="batch-date" placeholder="${isImage ? t('status_analyzing') : 'Formato no soportado'}..." />
        <div class="batch-coords small" style="opacity:0.6; font-size:0.7rem">${isImage ? t('status_searching_poi') : 'Sube solo imágenes'}...</div>
      </div>
      <div class="batch-item-fields">
        <div style="display:flex; gap:5px">
          <input type="text" class="batch-poi" placeholder="Lugar (POI)..." style="flex:1" ${!isImage ? 'disabled' : ''} />
          <button class="btn btn-search" title="Buscar de nuevo" ${!isImage ? 'disabled' : ''}>🔍</button>
        </div>
        <div class="consensus-area"></div>
        <div class="status-msg small" style="color:var(--accent); font-size:0.7rem"></div>
        <div class="vision-tags small" style="color:#94a3b8; font-size:0.7rem; font-style:italic"></div>
      </div>
    `;
    el.batchPreview.appendChild(itemEl);

    const itm = { 
      ...batchItem, 
      el: itemEl,
      poiInput: itemEl.querySelector(".batch-poi"),
      statusMsg: itemEl.querySelector(".status-msg"),
      coordsDiv: itemEl.querySelector(".batch-coords"),
      visionDiv: itemEl.querySelector(".vision-tags")
    };
    
    // Search manual bind
    itemEl.querySelector(".btn-search").onclick = () => performSearch(itm, itm.poiInput, itm.statusMsg);
    
    // Individual manual change bind
    itm.poiInput.addEventListener("input", () => {
       itm.poi = itm.poiInput.value.trim();
       applyConsensus();
    });

    items.push(itm);
    batchFiles.push(itm);
  }

  // --- Phase 1: EXIF Extraction & Global Memory Check ---
  await Promise.all(items.map(async (itm) => {
    if (!itm.isImage) return; 
    try {
      itm.statusMsg.textContent = t("status_analyzing");
      const fullMeta = await window.exifr.parse(itm.file, { gps: true, exif: true, xmp: true, iptc: true });
      const coords = extractGpsCascading(fullMeta);
      
      const d = fullMeta?.DateTimeOriginal || fullMeta?.DateTime || fullMeta?.CreateDate || itm.file.lastModified;
      itm.date = d instanceof Date ? d.getTime() : (typeof d === 'number' ? d : new Date(d).getTime() || itm.file.lastModified);
      
      const dateStr = new Date(itm.date).toLocaleString();
      itm.el.querySelector(".batch-date").value = dateStr;

      if (coords) {
        itm.lat = coords.lat;
        itm.lng = coords.lng;
        itm.coordsDiv.textContent = `${itm.lat.toFixed(6)}, ${itm.lng.toFixed(6)}`;
        
        const rememberedPoi = findInGlobalMemory(itm.lat, itm.lng);
        if (rememberedPoi) {
           itm.poi = rememberedPoi;
           itm.poiInput.value = rememberedPoi;
           itm.statusMsg.textContent = "✓ Memoria Local";
        }
      }
    } catch (e) {
      console.warn("EXIF failed", e);
      itm.date = itm.file.lastModified;
      itm.el.querySelector(".batch-date").value = new Date(itm.date).toLocaleString();
    }
  }));

  // --- Phase 2: Vision AI (Throttled) ---
  const pendingItems = items.filter(itm => itm.isImage); // Analyze all for landmarks/ocr
  
  const chunk = (arr, size) => Array.from({ length: Math.ceil(arr.length / size) }, (v, i) => arr.slice(i * size, i * size + size));
  const itemChunks = chunk(pendingItems, 2);

  for (const batch of itemChunks) {
    await Promise.all(batch.map(async (itm) => {
      try {
        const withTimeout = (promise, ms) => Promise.race([
          promise,
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), ms))
        ]);

        itm.statusMsg.textContent = "👁️ Analizando imagen...";
        
        // Try Cloud Vision
        let visionData = null;
        try {
           visionData = await withTimeout(analyzeImage(itm.file), 10000);
        } catch(e) { console.warn("Cloud vision timeout", itm.id); }

        if (visionData) {
            itm.visionLabels = [...new Set(visionData.labels || [])];
            itm.visionLandmarks = [...new Set(visionData.landmarks || [])];
            itm.visionTexts = visionData.texts || [];
            
            const primaryTag = itm.visionLandmarks[0] || itm.visionTexts[0] || itm.visionLabels[0] || "";
            if (primaryTag) {
              itm.visionDiv.textContent = "🔍 " + t("vision_detected") + ": " + primaryTag;
              if (!itm.poi) {
                 itm.poiInput.value = primaryTag;
                 itm.poi = primaryTag;
              }
            }
        }
      } catch (err) {
        console.warn("Vision failed for item", itm.id, err);
      }
    }));
  }

  // --- Phase 3: Spatio-Temporal Consensus (Zero-Lag) ---
  applyConsensus();
  
  // --- Phase 4: Backend Consenso & Orchestration ---
  items.forEach(itm => { if (itm.isImage) itm.statusMsg.textContent = '🧩 Resolviendo lote...'; });
  
  try {
    const puzzleData = await fetch('/api/resolve-puzzle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        photos: items.map(p => ({
          id: p.id,
          lat: p.lat,
          lng: p.lng,
          timestamp: p.date,
          visionLabels: (p.visionLabels || []).map(l => ({ name: l, isLandmark: (p.visionLandmarks || []).includes(l) })),
          ocrText: p.visionTexts ? p.visionTexts.join(' ') : ''
        }))
      })
    });
    
    if (puzzleData.ok) {
      const puzzleResults = await puzzleData.json();
      console.log('[Puzzle] Batch results:', puzzleResults);
      
      // Apply collective intelligence to each batch item
      items.forEach(itm => {
        const result = puzzleResults.results?.find(r => r.photoId === itm.id);
        if (!result) return;

        if (result.name) {
          itm.poi = result.name;
          itm.poiInput.value = result.name;
        }

        // --- Evidence Badges ---
        const badges = [];
        if (result.evidence === 'ANCHOR_PHOTO')  badges.push({ cls: 'badge-gps',       icon: '⚓', label: 'Ancla' });
        else if (result.evidence === 'GPS')      badges.push({ cls: 'badge-gps',       icon: '📍', label: 'GPS' });
        else if (result.evidence === 'TIME_PROXIMITY') badges.push({ cls: 'badge-inherited', icon: '⚡', label: 'Heredado' });

        if (result.source === 'SPATIAL_MEMORY') badges.push({ cls: 'badge-memory', icon: '🧠', label: 'Memoria' });
        if (itm.visionLandmarks?.length)        badges.push({ cls: 'badge-vision', icon: '👁', label: 'Hito' });
        if (itm.visionTexts?.length)            badges.push({ cls: 'badge-ocr',    icon: '🔤', label: 'OCR' });

        const evidenceArea = itm.el.querySelector('.consensus-area');
        if (evidenceArea) {
          evidenceArea.innerHTML = `<div class="evidence-badges">${
            badges.map(b => `<span class="badge ${b.cls}">${b.icon} ${b.label}</span>`).join('')
          }</div>`;
        }

        // Status message & anchor styling
        itm.statusMsg.textContent = `✓ ${result.evidence === 'ANCHOR_PHOTO' ? '⚓ Ancla del lote' : result.evidence || 'Listo'}`;
        if (result.isAnchor) itm.el.classList.add('anchor-photo');
      });
    }
  } catch (e) {
    console.warn('[Puzzle] Backend failed, using local consensus only:', e.message);
    // Legacy path: performSearch is already done in Phase 3, consensus is applied
  }
}

function showManualGeoFallback(itm) {
  itm.coordsDiv.innerHTML = `${t('status_found_geocoder').split('(')[0]} <button class="btn-mini btn-manual-geo" title="${t('btn_manual_geo')}">📍</button>`;
  itm.statusMsg.textContent = t("status_no_coords");
  itm.coordsDiv.querySelector(".btn-manual-geo").onclick = () => {
    alert(t("manual_geo_alert"));
    window.pendingManualGeo = { 
      batchItem: itm, 
      itemEl: itm.el, 
      coordsDiv: itm.coordsDiv, 
      statusMsg: itm.statusMsg, 
      poiInput: itm.poiInput, 
      file: itm.file 
    };
    el.batchModal.style.display = "none";
  };
}

async function performSearch(batchItem, poiInput, statusMsg) {
  if (!batchItem.lat || !batchItem.lng) return;
  
  const radius = Math.max(parseInt(el.radiusRange.value) || 20, 500);
  
  // Intelligence: Combine Vision clues (filtered for noise)
  const lmarks = batchItem.visionLandmarks || [];
  const texts = (batchItem.visionTexts || []).filter(t => !isGenericName(t));
  const labels = batchItem.visionLabels || [];
  
  // Neighbor Intelligence (v2.2): Borrow keywords from highly similar neighbors
  const neighbors = batchFiles.filter(bf => {
    if (bf.id === batchItem.id) return false;
    if (!bf.lat || !bf.lng) return false;
    const d = calculateDistance(batchItem.lat, batchItem.lng, bf.lat, bf.lng);
    const tDiff = Math.abs((batchItem.date || 0) - (bf.date || 0));
    return (d < 100 && tDiff < (5 * 60 * 1000)); 
  });

  const neighborLmarks = neighbors.flatMap(n => n.visionLandmarks || []);
  const neighborTexts = neighbors.flatMap(n => n.visionTexts || []).filter(t => !isGenericName(t));

  const keywords = [...new Set([...lmarks, ...texts, ...neighborLmarks, ...neighborTexts, ...labels])].slice(0, 10).join(" ");
  
  // 1. Try Backend
  try {
    const poiData = await findPoiBackend(batchItem.lat, batchItem.lng, radius, keywords);
    if (poiData && poiData.place) {
      batchItem.poi = poiData.place.name || poiData.place.formatted_address;
      poiInput.value = batchItem.poi;
      statusMsg.textContent = t("status_found_backend");
      applyConsensus();
      return;
    }
  } catch (e) {
    console.warn("Backend search skipped/failed", e);
  }

  // 2. Fallback: Google Places Service (Nearby Search)
  if (window.google && window.google.maps && window.google.maps.places) {
    statusMsg.textContent = t("status_searching_local");
    
    try {
      // Create a temporary div for the PlacesService
      const service = new google.maps.places.PlacesService(el.mapDiv);
      const request = {
        location: { lat: batchItem.lat, lng: batchItem.lng },
        radius: radius,
        type: keywords ? undefined : 'tourist_attraction',
        keyword: keywords || undefined
      };
      console.log("Searching POI near:", request.location, "with radius:", radius);

      service.nearbySearch(request, (results, status) => {
        try {
          if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length > 0) {
            // Filtrar nombres genéricos y priorizar por tipo + cercanía
            const validResults = results.filter(r => !isGenericName(r.name));
            const pool = validResults.length > 0 ? validResults : results;

            const best = pool.sort((a, b) => {
              const distA = calculateDistance(batchItem.lat, batchItem.lng, a.geometry.location.lat(), a.geometry.location.lng());
              const distB = calculateDistance(batchItem.lat, batchItem.lng, b.geometry.location.lat(), b.geometry.location.lng());
              
              const score = (r) => {
                let s = 0;
                if (r.types.includes('tourist_attraction')) s += 100;
                if (r.types.includes('museum')) s += 95;
                if (r.types.includes('park')) s += 90;
                if (r.types.includes('establishment')) s += 50;
                return s;
              };
              // Priorizar score pero penalizar distancia (distancia en metros / 10)
              return (score(b) - distB/10) - (score(a) - distA/10);
            })[0];

            batchItem.poi = best.name;
            poiInput.value = best.name;
            statusMsg.textContent = t("status_found_google");
            applyConsensus();
          } else {
            useGeocoderFallback(batchItem, poiInput, statusMsg);
          }
        } catch (err) {
          console.warn("Places search callback error:", err);
          useGeocoderFallback(batchItem, poiInput, statusMsg);
        }
      });
    } catch (err) {
      console.warn("Places search invocation error:", err);
      useGeocoderFallback(batchItem, poiInput, statusMsg);
    }
  } else {
    useGeocoderFallback(batchItem, poiInput, statusMsg);
  }
}

function useGeocoderFallback(batchItem, poiInput, statusMsg) {
  if (!window.google || !window.google.maps) {
    statusMsg.textContent = "Error: Google API.";
    return;
  }
  statusMsg.textContent = t("status_searching_local") + " (Geocoder)...";
  const geocoder = new google.maps.Geocoder();
  geocoder.geocode({ location: { lat: batchItem.lat, lng: batchItem.lng } }, (results, status) => {
    if (status === "OK" && results && results.length > 0) {
      // Priorizar POIs específicos
      const poiResult = results.find(r => 
        r.types.includes('point_of_interest') || 
        r.types.includes('establishment') || 
        r.types.includes('premise') ||
        r.types.includes('tourist_attraction')
      );
      
      const best = poiResult || results[0];
      let name = best.formatted_address.split(',')[0];

      // Si el geocoder solo devuelve una calle y NO es un POI claro,
      // ya lo habremos intentado en performSearch, así que lo aceptamos como el mejor esfuerzo.
      batchItem.poi = name;
      poiInput.value = name;
      statusMsg.textContent = t("status_found_geocoder");
      applyConsensus();
    } else {
      statusMsg.textContent = t("status_no_coords");
    }
  });
}

// --- Consensus Logic ---
// (consolidated helper used below)

// --- Consensus Logic (Master Pattern: Spatio-Temporal Clustering) ---
// --- Consensus Logic (Master Pattern: Spatio-Temporal Clustering v5.0) ---
import { renderPuzzleSummary } from './components/PuzzleSummary.js';

function applyConsensus() {
  // RULE: 30-minute window for the batch cluster
  const clusters = clusterPhotosByContext(batchFiles, 30 * 60 * 1000);
  
  clusters.forEach(cluster => {
    if (cluster.length > 1) { 
      // 1. Identify ANCHOR and calculate Confidence
      const { anchor, confidence } = analyzeClusterIntelligence(cluster);
      
      // 2. Inheritance (RULE: 15-minute window from Anchor)
      const bestLat = anchor.lat;
      const bestLng = anchor.lng;
      const bestPoi = (anchor.poi && !isGenericName(anchor.poi)) ? anchor.poi : getMostCommonCaption(cluster).winner;

      cluster.forEach(p => {
        const timeDiff = Math.abs((p.date || 0) - (anchor.date || 0));
        
        // Mark Roles
        p.role = (p.id === anchor.id) ? 'ANCHOR_VISUAL' : null;

        // Inherit Location (15 min rule)
        if ((!p.lat || !p.lng) && bestLat && bestLng && timeDiff <= 15 * 60 * 1000) {
           p.lat = bestLat;
           p.lng = bestLng;
           p.source = 'consensus';
           p.isConsensus = true;
           if (p.coordsDiv) p.coordsDiv.innerHTML = `<span style="color:var(--accent-success)">⚡ ${p.lat.toFixed(4)}, ${p.lng.toFixed(4)} (Heredado)</span>`;
           if (p.statusMsg) p.statusMsg.textContent = "⚡ GPS Heredado";
        }

        // Inherit POI Name if empty or generic
        if (bestPoi && (!p.poi || isGenericName(p.poi) || p.consensus)) {
           p.poi = bestPoi;
           p.consensus = true;
           if (p.poiInput) p.poiInput.value = bestPoi;
           
           const ca = p.el.querySelector(".consensus-area");
           if (ca) ca.innerHTML = `<span class="consensus-badge">${t('consensus_badge')}</span>`;
        }

        // --- Evidence Badges ---
        updateEvidenceBadges(p);
      });

      // 3. Render Puzzle UI
      const container = document.getElementById("consensus-summary-area") || (() => {
          const div = document.createElement("div");
          div.id = "consensus-summary-area";
          el.batchPreview.prepend(div);
          return div;
      })();

      renderPuzzleSummary(container, {
          consensus_result: {
             place_name: bestPoi || "Buscando...",
             confidence_score: confidence,
             match_reason: `Consenso de ${cluster.length} fotos (Ventana: 30min)`
          },
          images: cluster.map(p => ({
             id: p.title,
             url: URL.createObjectURL(p.file),
             role: p.role,
             exif: { has_gps: !!(p.lat && p.lng) },
             vision_analysis: {
                landmark: p.visionLandmarks && p.visionLandmarks.length > 0,
                ocr_text: p.visionTexts && p.visionTexts.length > 0
             },
             source_text: p.poi
          }))
      });

      // 4. Human-In-The-Loop: Trigger if confidence is low
      if (confidence < 0.75) {
         const sm = cluster.find(p => p.statusMsg);
         if (sm) sm.statusMsg.innerHTML = `<span style="color:var(--danger)">⚠️ Baja confianza. Verifica el lugar.</span>`;
      }
    }
  });
}

function analyzeClusterIntelligence(cluster) {
   let maxScore = -1;
   let anchor = cluster[0];
   
   cluster.forEach(p => {
      let score = 0;
      if (p.lat && p.lng) score += 50; // GPS is strong
      if (p.visionLandmarks?.length) score += 40; // Recognizable landmark
      if (p.visionTexts?.length) score += 20; // OCR data
      if (p.poi && !isGenericName(p.poi)) score += 10;
      
      if (score > maxScore) {
         maxScore = score;
         anchor = p;
      }
   });

   const confidence = Math.min(maxScore / 100, 1); 
   return { anchor, confidence };
}

function updateEvidenceBadges(p) {
  const badges = [];
  if (p.role === 'ANCHOR_VISUAL') badges.push({ cls: 'badge-gps', icon: '⚓', label: 'Ancla' });
  else if (p.source === 'consensus') badges.push({ cls: 'badge-inherited', icon: '⚡', label: 'Heredado' });
  else if (p.lat && p.lng) badges.push({ cls: 'badge-gps', icon: '📍', label: 'GPS' });

  if (p.visionLandmarks?.length) badges.push({ cls: 'badge-vision', icon: '👁', label: 'Hito' });
  if (p.visionTexts?.length) badges.push({ cls: 'badge-ocr', icon: '🔤', label: 'OCR' });
  if (p.source === 'spatial_memory') badges.push({ cls: 'badge-memory', icon: '🧠', label: 'Memoria' });

  const evidenceArea = p.el.querySelector('.consensus-area');
  if (evidenceArea) {
    evidenceArea.innerHTML = `<div class="evidence-badges">${
      badges.map(b => `<span class="badge ${b.cls}">${b.icon} ${b.label}</span>`).join('')
    }</div>`;
  }
}

function clusterPhotosByContext(photos, windowSize = 30 * 60 * 1000) {
  const clusters = [];
  const processed = new Set();

  for (const photo of photos) {
    if (processed.has(photo)) continue;
    const cluster = [photo];
    processed.add(photo);
    
    const pTime = photo.date || 0;

    for (const other of photos) {
      if (processed.has(other)) continue;
      
      const oTime = other.date || 0;
      const timeDiff = Math.abs(pTime - oTime);
      
      if (timeDiff < windowSize) {
        cluster.push(other);
        processed.add(other);
      }
    }
    clusters.push(cluster);
  }
  return clusters;
}

function getMostCommonCaption(photos) {
  const scores = new Map();
  photos.forEach(p => {
    if (p.poi && p.poi.trim().length > 0) {
      const name = p.poi.trim();
      const l = name.toLowerCase();
      // Scoring (v5.0 - NotebookLM Alignment): 
      let points = 1;
      const isGeneric = isGenericName(name);
      
      // Sanitización para evitar errores con apóstrofos (Regla NotebookLM)
      const sanitizedName = sanitizeLocationName(name);
      
      if (!isGeneric) points += 50; 
      
      const isLandmarkString = /jardin|jardín|parque|museo|monumento|plaza|palacio|recoleta|tigre|plazoleta|estación|terminal/i.test(l);
      if (isLandmarkString) points += 120; // Plus para hitos/parques
      
      // Prioridad absoluta a nombres que NO son calles
      if (/^calle|avenida|av\.|pje|pasaje/i.test(l)) points -= 40;

      // AI Signal boost (Pistas de Visión)
      if (p.visionLandmarks && p.visionLandmarks.includes(name)) points += 200;
      else if (p.visionLandmarks && p.visionLandmarks.length > 0) points += 20;

      // Penalización fuerte si contiene patrones de fecha/hora (v2.5)
      if (/(\d{2}[\.\/:]\d{2})/.test(name) || /(\d{4})/.test(name)) points -= 80;
      
      if (name === name.toUpperCase() && name.length > 5 && !isGeneric) points += 10; 
      
      scores.set(name, (scores.get(name) || 0) + points);
    }
  });
  
  let maxScore = 0, best = null;
  scores.forEach((score, name) => {
    if (score > maxScore) {
      maxScore = score;
      best = name;
    }
  });
  return { winner: best, scores };
}

/**
 * Sanitiza nombres de ubicaciones para evitar errores (como el bug de apóstrofos).
 */
function sanitizeLocationName(name) {
  if (!name) return "";
  // Escapa apóstrofos simples para seguridad (Regla NotebookLM)
  return name.replace(/'/g, "''");
}

async function findPoiBackend(lat, lng, radius = 500, keywords = "") {
  try {
    const res = await fetch(`/api/find-poi`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ latitude: lat, longitude: lng, radius, keywords })
    });
    
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await res.json();
    } else {
      throw new Error("Formato no válido (servidor estático)");
    }
  } catch (e) {
    console.warn("Backend failover:", e.message);
    // FALLBACK 2: OpenCage (if key exists)
    const ocResult = await reverseGeocodeOpenCage(lat, lng);
    if (ocResult) return ocResult;

    throw e;
  }
}

// --- Ollama Local Intelligence Functions (v3.2) ---

async function refinePoiWithOllama(names) {
  if (!names || names.length === 0) return null;
  
  const prompt = `Dada esta lista de nombres de lugares detectados en una ubicación de Buenos Aires (Argentina), identifica el PUNTO DE INTERÉS (POI) real más probable. Ignora ruidos, marcas de agua, o textos de fecha/hora. 
Nombres detectados: ${names.join(", ")}
Responde ÚNICAMENTE en JSON con este formato: {"poi": "Nombre del lugar", "reason": "breve explicación"}`;

  try {
    const res = await fetch('/api/ollama', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        model: 'phi3', 
        prompt: prompt 
      })
    });
    
    if (!res.ok) return null;
    const data = await res.json();
    const result = JSON.parse(data.response);
    return result.poi && !isGenericName(result.poi) ? result.poi : null;
  } catch (e) {
    console.warn("Ollama refinement failed:", e);
    return null;
  }
}

async function analyzeImageWithOllama(file) {
  // Convertir file a base64
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64 = reader.result.split(',')[1];
      try {
        const res = await fetch('/api/ollama', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: 'moondream',
            prompt: "Describe this image in 3-5 keywords, focus on landmarks if visible.",
            images: [base64]
          })
        });

        if (!res.ok) return resolve(null);
        const data = await res.json();
        const keywords = data.response.split(',').map(k => k.trim());
        resolve({
          labels: keywords,
          landmarks: [] 
        });
      } catch (e) {
        console.warn("Ollama Vision failed:", e);
        resolve(null);
      }
    };
    reader.readAsDataURL(file);
  });
}
el.saveBatchBtn.addEventListener("click", () => {
  const commonStr = el.commonDesc.value.trim();
  batchFiles.forEach(bf => {
    const titleVal = bf.el.querySelector(".batch-title").value || bf.title;
    const poiVal = bf.el.querySelector(".batch-poi").value;
    const dateVal = bf.el.querySelector(".batch-date").value;
    const finalCaption = poiVal || commonStr || titleVal;
    
    // Create actual item in main list
    createPhotoItem(bf.file, finalCaption, bf.lat, bf.lng, dateVal);
    
    // Save to localStorage
    const saved = JSON.parse(localStorage.getItem("rg_saved_captions_v1") || "{}");
    const saveId = `${bf.file.name}-${bf.file.size}-${bf.file.lastModified}`;
    saved[saveId] = { 
      caption: finalCaption, 
      ts: Date.now(),
      lat: bf.lat,
      lng: bf.lng,
      date: bf.date
    };
    localStorage.setItem("rg_saved_captions_v1", JSON.stringify(saved));

    // v4.0: Alimentar Memoria Global con el éxito actual
    if (bf.lat && bf.lng && poiVal) {
      saveToGlobalMemory(bf.lat, bf.lng, poiVal);
    }
  });
  updateAlbumGallery();
  closeModal();
});

async function initMap() {
  await loadGoogleMapsApi();
  const defaultPos = { lat: -34.6037, lng: -58.3816 };
  if (map) return; // Prevent double init
  
  if (!el.mapDiv) {
    console.error("Map div not found!");
    return;
  }
  
  // Clean start
  if (!el.mapDiv.innerHTML) {
     el.mapDiv.innerHTML = `<div style="color:white; padding:20px;">${t('loading_map')}</div>`;
  }

  try {
    // Correctly load libraries using the dynamic import
    // @ts-ignore
    const { Map } = await google.maps.importLibrary("maps");
    console.log("Map library imported");
    // @ts-ignore
    ({ AdvancedMarkerElement } = await google.maps.importLibrary("marker"));
    // @ts-ignore
    const { Place } = await google.maps.importLibrary("places"); // Pre-load places

    // Clear loading message before creating map
    el.mapDiv.innerHTML = '';

    map = new Map(el.mapDiv, {
      center: defaultPos,
      zoom: 12,
      mapTypeId: "roadmap",
      mapId: "DEMO_MAP_ID", // Required for AdvancedMarkerElement
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      disableDefaultUI: true,
      zoomControl: true,
    });
    
    console.log("Map instance created (Modern)", map);
    
    // Force a resize calculation
    setTimeout(() => {
        // @ts-ignore
        if (google.maps.event) google.maps.event.trigger(map, "resize");
        map.setCenter(defaultPos);
    }, 500);

    map.addListener("click", async (e) => {
      const lat = e.latLng.lat();
      const lng = e.latLng.lng();


      // Case: Manual geocoding from Batch Modal
      if (window.pendingManualGeo) {
        const { batchItem, itemEl, coordsDiv, statusMsg, poiInput } = window.pendingManualGeo;
        batchItem.lat = lat;
        batchItem.lng = lng;
        coordsDiv.textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        el.batchModal.style.display = "flex"; // Re-show modal
        
        statusMsg.textContent = "Buscando POI...";
        await performSearch(batchItem, poiInput, statusMsg);
        
        window.pendingManualGeo = null;
        return;
      }

      if (!currentSelected) {
        alert(t("select_photo_first"));
        return;
      }
      updateMarkerAndCircle(lat, lng);
      await handleFindPoi(lat, lng, currentSelected.itemEl);
    });
  } catch (error) {
    console.error("Error initializing map:", error);
    if (el.mapDiv) el.mapDiv.innerHTML = `<div style="color:white; padding:20px;">${t('map_error')}</div>`;
  }
}

function updateMarkerAndCircle(lat, lng) {
  if (!map) return;
  const pos = { lat: Number(lat), lng: Number(lng) };

  if (!photoMarker) {
    photoMarker = new google.maps.marker.AdvancedMarkerElement({
      position: pos,
      map: map,
      title: "Foto"
    });
  } else {
    photoMarker.position = pos;
  }

  const radius = Number(el.radiusRange.value) || 20;
  if (!radiusCircle) {
    radiusCircle = new google.maps.Circle({
      strokeColor: "#3388ff",
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillColor: "#3388ff",
      fillOpacity: 0.2,
      map: map,
      center: pos,
      radius: radius,
    });
  } else {
    // @ts-ignore
    radiusCircle.setCenter(pos);
    radiusCircle.setRadius(radius);
  }

  map.setZoom(16);
  map.panTo(pos);
  // Force redraw
  google.maps.event.trigger(map, "resize");
}

let searchTimeout;
el.radiusRange.addEventListener("input", () => {
  el.radiusValue.textContent = el.radiusRange.value;
  if (radiusCircle && currentSelected && currentSelected.lat) {
    radiusCircle.setRadius(Number(el.radiusRange.value));
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      await handleFindPoi(
        currentSelected.lat,
        currentSelected.lng,
        currentSelected.itemEl
      );
    }, 400); // Debounce de 400ms
  }
});

function roundCoords(lat, lng, decimals = 4) {
  const f = Math.pow(10, decimals);
  return [Math.round(lat * f) / f, Math.round(lng * f) / f];
}

async function createPhotoItem(file, preCaption = null, preLat = null, preLng = null, preDate = null) {
  const id = `${file.name}_${file.size}_${file.lastModified}`;
  const imgUrl = URL.createObjectURL(file);
  const img = document.createElement("img");
  img.src = imgUrl;
  img.className = "photoThumb";
  img.alt = file.name;

  const item = document.createElement("div");
  item.className = "photoItem";
  item.dataset.id = id;

  const deleteBtn = document.createElement("button");
  deleteBtn.className = "delete-btn";
  deleteBtn.textContent = "×";
  deleteBtn.innerHTML = "&times;";
  deleteBtn.onclick = (e) => {
    e.stopPropagation();
    if (currentSelected && currentSelected.id === id) {
      if (photoMarker) photoMarker.map = null;
      if (radiusCircle) radiusCircle.setMap(null);
      photoMarker = null;
      radiusCircle = null;
      currentSelected = null;
      el.selectedInfo.textContent = t("select_photo_msg");
      el.placesList.innerHTML = "";
    }
    item.remove();
  };

  const meta = document.createElement("div");
  meta.className = "photoMeta";

  const title = document.createElement("div");
  title.className = "title";
  title.textContent = preCaption || file.name;

  const metaRow = document.createElement("div");
  metaRow.className = "metaRow";

  const rowButtons = document.createElement("div");
  rowButtons.className = "rowButtons";

  const useBtn = document.createElement("button");
  useBtn.className = "btn primary";
  useBtn.textContent = t("btn_use_location");
  useBtn.disabled = true;

  const manualBtn = document.createElement("button");
  manualBtn.className = "btn";
  manualBtn.textContent = t("btn_manual_geo");

  const saveBtn = document.createElement("button");
  saveBtn.className = "btn primary";
  saveBtn.textContent = t("btn_save_suggested");

  // Check if already saved in localStorage
  const savedData = JSON.parse(localStorage.getItem("rg_saved_captions_v1") || "{}");
  if (savedData[id]) {
    saveBtn.textContent = "✅ " + t("badge_saved");
    saveBtn.style.opacity = "0.7";
    item.dataset.selectedCaption = savedData[id].caption;
    title.textContent = savedData[id].caption;
    
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.style.background = "#10b981";
    badge.style.position = "absolute";
    badge.style.top = "8px";
    badge.style.left = "8px";
    badge.textContent = t("badge_saved");
    item.appendChild(badge);
  }

  rowButtons.appendChild(useBtn);
  rowButtons.appendChild(manualBtn);
  rowButtons.appendChild(saveBtn);
  meta.appendChild(title);
  meta.appendChild(metaRow);
  meta.appendChild(rowButtons);
  item.appendChild(deleteBtn);
  item.appendChild(img);
  item.appendChild(meta);
  el.photosList.prepend(item);

  let lat = preLat, lng = preLng, dateTaken = preDate;

  if (lat && lng) {
    metaRow.textContent = `Coordenadas: ${lat.toFixed(6)}, ${lng.toFixed(6)}${
      dateTaken ? " · " + dateTaken : ""
    }`;
    useBtn.disabled = false;
  } else {
    // Extraer EXIF si no se proveyó
    try {
      // @ts-ignore
      const fullMeta = await window.exifr.parse(file, { gps: true, exif: true, xmp: true, iptc: true });
      const coords = extractGpsCascading(fullMeta);
      if (coords) {
        lat = coords.lat;
        lng = coords.lng;
        dateTaken = fullMeta.DateTimeOriginal || fullMeta.DateTime || "";
        metaRow.textContent = `Coordenadas: ${lat.toFixed(6)}, ${lng.toFixed(6)}${
          dateTaken ? " · " + dateTaken : ""
        }`;
        useBtn.disabled = false;
      } else {
        metaRow.textContent = "No se encontraron coordenadas (EXIF/XMP/IPTC).";
      }
    } catch (e) {
      console.warn("exifr error", e);
      metaRow.textContent = "Error al leer metadatos.";
    }
  }

  // Analizar imagen con Vision AI si tiene coordenadas
  if (lat && lng) {
    analyzeImage(file).then(visionData => {
      if (visionData) {
        const { labels, landmarks, texts } = visionData;
        item.dataset.visionLabels = labels.join(',');
        item.dataset.visionLandmarks = landmarks.join(',');
        item.dataset.visionTexts = texts.join(',');

        const primaryTag = landmarks[0] || texts[0] || labels[0];
        if (primaryTag) {
          const labelsTag = document.createElement("div");
          labelsTag.className = "small";
          labelsTag.style.color = "var(--accent)";
          labelsTag.innerHTML = `🔍 <strong>${primaryTag}</strong>`;
          meta.insertBefore(labelsTag, title);
        }
      }
    }).catch(e => { console.warn("Vision API skipped", e); });
  }

  useBtn.addEventListener("click", async () => {
    if (!lat || !lng) return;
    currentSelected = { id, lat, lng, itemEl: item };
    updateMarkerAndCircle(lat, lng);
    await handleFindPoi(lat, lng, item);
    highlightSelectedPhoto(item);
  });

  manualBtn.addEventListener("click", () => {
    currentSelected = { id, lat: null, lng: null, itemEl: item };
    alert(t("manual_geo_alert"));
    highlightSelectedPhoto(item);
  });

  saveBtn.addEventListener("click", () => {
    const caption = item.dataset.selectedCaption;
    if (!caption) {
      alert(t("select_photo_first"));
      return;
    }
    const saved = JSON.parse(localStorage.getItem("rg_saved_captions_v1") || "{}");
    saved[id] = { caption, ts: Date.now() };
    localStorage.setItem("rg_saved_captions_v1", JSON.stringify(saved));
    
    saveBtn.textContent = "✅ " + t("badge_saved");
    saveBtn.style.opacity = "0.7";
    
    // Feedback visual en la foto
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.style.background = "#10b981";
    badge.style.position = "absolute";
    badge.style.top = "8px";
    badge.style.left = "8px";
    badge.textContent = t("badge_saved");
    item.appendChild(badge);
  });
}

function highlightSelectedPhoto(itemEl) {
  document.querySelectorAll(".photoItem").forEach((i) => (i.style.boxShadow = "none"));
  if (itemEl) itemEl.style.boxShadow = "0 0 0 2px var(--accent)";
}

async function analyzeImage(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64 = reader.result.split(',')[1];
      try {
        const res = await fetch("/api/analyze-image", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_base64: base64 }),
        });
        if (!res.ok) throw new Error(`Server returned ${res.status}`);
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
           const data = await res.json();
           resolve({
              labels: data.labels || [],
              landmarks: data.landmarks || [],
              texts: data.texts || []
            });
         } else {
            resolve({ labels: [], landmarks: [], texts: [] });
         }
      } catch (e) {
        console.warn("Vision AI skipped:", e.message);
        resolve({ labels: [], landmarks: [], texts: [] });
      }
    };
    reader.readAsDataURL(file);
  });
}

async function handleFindPoi(lat, lng, itemEl) {
  el.selectedInfo.textContent = t("status_searching_poi");
  el.placesList.innerHTML = "";

  const anonymize = el.anonymize.checked;
  const [rlat, rlng] = anonymize ? roundCoords(lat, lng, 4) : [lat, lng];
  
  // Extract all vision context
  const lmarks = (itemEl.dataset.visionLandmarks || "").split(",").filter(v => v);
  const texts = (itemEl.dataset.visionTexts || "").split(",").filter(v => v.length > 3);
  const labels = (itemEl.dataset.visionLabels || "").split(",").filter(v => v);
  
  const keywords = [...lmarks, ...texts, ...labels].slice(0, 10).join(" ") || null;

  const payload = {
    latitude: lat,
    longitude: lng,
    radius: Number(el.radiusRange.value) || 20,
    keywords: keywords,
  };

  try {
    const res = await fetch("/api/find-poi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    
    let data;
    if (res.ok) {
       data = await res.json();
    } else {
       console.warn("Backend 404/Error, falling back to local Places search.");
       // Optional: Add visual indicator of fallback
       if (itemEl && !itemEl.querySelector('.fallback-badge')) {
          const badge = document.createElement('span');
          badge.className = 'badge';
          badge.style.backgroundColor = 'var(--text-muted)';
          badge.style.marginLeft = '8px';
          badge.textContent = 'OFFLINE MODE';
          const title = itemEl.querySelector('.title');
          if (title) title.appendChild(badge);
       }
    }

    if (data && data.place) {
      renderPoiResult(data, itemEl);
    } else {
      // Fallback a Places Local
      handlePlacesLocalFallback(lat, lng, itemEl, keywords);
    }
  } catch (err) {
    console.warn("Backend exception, falling back to local Places search:", err.message);
    handlePlacesLocalFallback(lat, lng, itemEl, keywords);
  }
}

async function handlePlacesLocalFallback(lat, lng, itemEl, keywords) {
  if (!window.google || !window.google.maps || !window.google.maps.places || !window.google.maps.places.Place) {
    el.selectedInfo.textContent = "Error: Buscador local de Google (v4) no disponible.";
    return;
  }

  el.selectedInfo.textContent = t("status_searching_local");
  const radius = Math.max(Number(el.radiusRange.value) || 20, 500); 
  
  try {
    // Modern Search (v4)
    const { Place } = await google.maps.importLibrary("places");
    const request = {
      locationRestriction: {
        center: { lat, lng },
        radius: radius
      },
      fields: ['displayName', 'formattedAddress', 'location', 'types', 'plusCode']
    };

    const { places } = await Place.searchNearby(request);

    if (places && places.length > 0) {
      // Logic: Rank by specificity and keyword match
      const ranked = places.map(p => ({
        name: p.displayName, // displayName is already the string or handles toString in v4
        formatted_address: p.formattedAddress,
        geometry: { location: { lat: p.location.lat(), lng: p.location.lng() } },
        types: p.types || [],
        plus_code: p.plusCode
      })).sort((a, b) => {
        const score = (r) => {
          let s = 0;
          const n = r.name.toLowerCase();
          
          if (keywords) {
             const keys = keywords.toLowerCase().split(' ').filter(k => k.length > 3);
             keys.forEach(k => { if (n.includes(k)) s += 100; });
          }

          if (!isGenericName(r.name)) s += 50;
          if (r.types.includes('tourist_attraction')) s += 20;
          if (r.types.includes('amusement_park')) s += 40;
          return s;
        };
        return score(b) - score(a);
      });

      const best = ranked[0];
      renderPoiResult({ source: 'local_fallback_v4', place: best, plus_code: best.plus_code }, itemEl);
    } else {
      el.selectedInfo.textContent = t("status_no_coords");
    }
  } catch (e) {
    console.error("Local search fail:", e);
    // Silent fallback to basic geocode if needed or just show error
    el.selectedInfo.textContent = "Error en el buscador local moderno.";
  }
}

function renderPoiResult(data, itemEl) {
    const p = data.place;
    const plusCode = data.plus_code ? (data.plus_code.global_code || data.plus_code) : null;
    
    const item = document.createElement("div");
    item.className = "placeItem";
    const info = document.createElement("div");
    info.className = "placeInfo";
    const name = document.createElement("div");
    name.className = "placeName";
    name.textContent = p.name || p.formatted_address || t("status_no_coords");
    
    const metaInfo = document.createElement("div");
    metaInfo.className = "placeTypes";
    metaInfo.innerHTML = `
      <span class="badge">${data.source || ""}</span> 
      · ${data.distanceMeters ? data.distanceMeters + 'm' : 'área'} 
      ${plusCode ? `· <span class="plus-code">${plusCode}</span>` : ""}
      <br><small style="opacity:0.7">${p.types ? p.types.join(", ") : ""}</small>
    `;
    
    const actions = document.createElement("div");
    actions.className = "rowButtons";
    actions.style.marginTop = "8px";
    
    const svBtn = document.createElement("button");
    svBtn.className = "btn";
    svBtn.innerHTML = "📍 Street View";
    svBtn.onclick = () => {
      const loc = p.geometry.location;
      window.open(`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${loc.lat},${loc.lng}`, '_blank');
    };
    
    const dirBtn = document.createElement("button");
    dirBtn.className = "btn primary";
    dirBtn.innerHTML = "🚗 Cómo llegar";
    dirBtn.onclick = () => {
      const loc = p.geometry.location;
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}`, '_blank');
    };

    actions.appendChild(svBtn);
    actions.appendChild(dirBtn);
    info.appendChild(name);
    info.appendChild(metaInfo);
    info.appendChild(actions);
    item.appendChild(info);
    el.placesList.appendChild(item);

    // Actualizar item de la foto
    itemEl.dataset.selectedCaption = p.name || p.formatted_address;
    if (plusCode) {
      const pcLabel = itemEl.querySelector('.plusCodeLabel') || document.createElement('div');
      pcLabel.className = 'plusCodeLabel small';
      pcLabel.style.color = 'var(--accent)';
      pcLabel.textContent = `📍 ${plusCode}`;
      if (!pcLabel.parentNode) itemEl.querySelector('.photoMeta').insertBefore(pcLabel, itemEl.querySelector('.rowButtons'));
    }
    el.selectedInfo.textContent = t("pane_details") + ":";
}

// Inicializar al cargar
window.onload = async () => {
  await initI18n(); // Load translations first
  el.langSelector.value = currentLanguage;
  el.langSelector.addEventListener("change", (e) => setLanguage(e.target.value));

  await initMap();
  updateAlbumGallery(); // v4.6: Populate albums on start
  el.radiusValue.textContent = el.radiusRange.value;
  el.imagesInput.addEventListener("change", async (ev) => {
    const files = Array.from(ev.target.files || []);
    for (const file of files) await createPhotoItem(file);
  });
};
/**
 * Intenta extraer GPS de múltiples fuentes (EXIF, XMP, IPTC)
 */
function extractGpsCascading(meta) {
  if (!meta) return null;
  // 1. EXIF Estándar
  if (meta.latitude && meta.longitude) {
    return { lat: meta.latitude, lng: meta.longitude };
  }
  // 2. XMP
  if (meta.GPSLatitude && meta.GPSLongitude) {
    return { lat: meta.GPSLatitude, lng: meta.GPSLongitude };
  }
  // 3. IPTC (a veces como strings en arrays o tags específicos)
  // exifr ya suele aplanar mucho, pero chequeamos fallback manual si fuera necesario
  return null;
}

/**
 * Placeholder para OpenCage Geocoding
 * Requiere OPENCAGE_API_KEY en el environment
 */
async function reverseGeocodeOpenCage(lat, lng) {
  const apiKey = import.meta.env.VITE_OPENCAGE_API_KEY;
  if (!apiKey) return null;
  
  try {
    const url = `https://api.opencagedata.com/geocode/v1/json?q=${lat}+${lng}&key=${apiKey}&language=es&no_annotations=1`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      const best = data.results[0];
      return {
        name: best.formatted,
        geometry: { location: { lat, lng } },
        types: ['point_of_interest'] // genérico
      };
    }
  } catch (e) {
    console.warn("OpenCage error", e);
  }
  return null;
}

/**
 * Picarta AI Integration (Visual Geolocation via Backend Proxy)
 */
async function localizeWithPicarta(file) {
  if (!el.usePicarta.checked) return null;

  console.log("Attempting Picarta AI localization via Proxy...");
  
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = async () => {
      try {
        const base64 = reader.result.split(',')[1];
        const res = await fetch("/api/picarta", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_base64: base64 })
        });

        if (res.ok) {
          const data = await res.json();
          console.log("Picarta Proxy Response:", data);
          
          if (data && data.lat && data.lng) {
            resolve(data);
            return;
          }
        } else {
          const errData = await res.json();
          console.warn("Picarta Proxy Error:", errData);
        }
      } catch (e) {
        console.warn("Picarta AI call failed:", e);
      }
      resolve(null);
    };
    reader.readAsDataURL(file);
  });
}

/**
 * Filtra nombres genéricos (calles, números, plus codes) para priorizar POIs
 */
function isGenericName(name) {
  if (!name) return true;
  const n = name.trim();
  const l = n.toLowerCase();
  
  // 1. Plus Code detection
  if (/^[A-Z0-9]{2,8}\+[A-Z0-9]{2,5}$/.test(n) || n.includes('+')) return true;
  
  // 2. OCR Noise / Date / Timestamp detection (e.g. 27.09.2025, 23:33, etc)
  const isDateOrTime = /(\d{1,2}[\.\/:-]\d{1,2}[\.\/:-]\d{2,4})/.test(n);
  // Revisa si tiene demasiados números (más del 40% son números) - típico de OCR de fechas
  const tooManyNumbers = (n.replace(/[^0-9]/g, '').length / n.length) > 0.4;
  // Caracteres imposibles en nombres de lugares reales (Basura OCR)
  const garbageChars = /[ΠΣΔΓΦΩ]/.test(n);
  // Palabras raras de OCR detectadas por el usuario (DAMO, PENE - a veces OCR confunde formas)
  const suspiciousOCR = /\b(DAMO|PENE|JESSDEV|ACKERMANAA)\b/i.test(n);
  
  if (isDateOrTime || (tooManyNumbers && n.length > 5) || garbageChars || suspiciousOCR) return true;

  // 3. Generic terms check
  const generics = [
    'costanera', 'avenida', 'calle', 'ruta', 'plaza', 'estacion', 
    'unknown', 'place', 'street', 'road', 'avenue', 'square',
    'provincia', 'buenos aires', 'argentina', 'tigre', 'colegiales', 'barrio'
  ];
  if (generics.some(g => l.includes(g))) return true;

  // 4. Street Address patterns
  const startsWithStreetType = /^(Av\.|Avenida|Calle|Ruta|Camino|Bv\.|Boulevard|Autopista|Pasaje|Diagonal)\s/i.test(n);
  const endsWithNumber = /\s\d+$/.test(n);
  const isHistoricalDate = /^\d+\sde\s/i.test(n); 
  
  if (startsWithStreetType || (endsWithNumber && !isHistoricalDate)) return true;

  // 5. Length check
  return l.length < 4;
}

/**
 * Calcula la distancia Haversine en metros
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000; // Radio de la Tierra en metros
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

initMap();

// --- Global Scope Functions (Moved from processBatchFiles) ---


// v5.0: Spatio-Temporal Clustering (Contextual Shared Memory)
function propagateLocationsByTime(items) {
  console.log("[Consensus] 🏁 Starting Spatio-Temporal Consensus...");
  
  // Sort items by detected timestamp
  const sorted = [...items].sort((a,b) => {
     const da = a.date || 0;
     const db = b.date || 0;
     return da - db;
  });

  const TIME_WINDOW = 30 * 60 * 1000; // 30 minutes window (Expanded for user request)

  let propagatedCount = 0;

  sorted.forEach(target => {
     // Skip if already has GPS or Global Memory hit
     if ((target.lat && target.lng) || target.poi) return;

     const targetTime = target.date || 0;
     if (!targetTime) {
        console.warn(`[Consensus] ⚠️ Item ${target.file.name} has no valid date. Skipping.`);
        return;
     }

     // Find best neighbor: closest in time that DOES have GPS
     let bestNeighbor = null;
     let minDiff = Infinity;

     sorted.forEach(n => {
        if (!n.lat || !n.lng || !n.date) return;
        if (n === target) return;

        const nTime = n.date;
        const diff = Math.abs(nTime - targetTime);
        
        if (diff <= TIME_WINDOW && diff < minDiff) {
           minDiff = diff;
           bestNeighbor = n;
        }
     });

     if (bestNeighbor) {
        console.log(`[Consensus] ⚡ Propagating location from ${bestNeighbor.file.name} to ${target.file.name} (Diff: ${Math.round(minDiff/1000)}s)`);
        
        target.lat = bestNeighbor.lat;
        target.lng = bestNeighbor.lng;
        // COPY NEIGHBOR'S POI ONLY IF IT EXISTS. DO NOT USE PLACEHOLDER.
        // If neighbor has no name yet, leave target.poi empty so performSearch triggers later.
        if (bestNeighbor.poi && bestNeighbor.poi !== "Ubicación por Cercanía Temporal") {
            target.poi = bestNeighbor.poi;
            // Visual Feedback for Name
            if (target.poiInput) target.poiInput.value = target.poi;
        }

        target.isConsensus = true;

        // Visual Feedback for GPS (Always)
        if (target.coordsDiv) target.coordsDiv.innerHTML = `<span style="color:var(--accent-success)">⚡ ${target.lat.toFixed(4)}, ${target.lng.toFixed(4)} (Heredado)</span>`;
        if (target.statusMsg) target.statusMsg.textContent = "⚡ GPS Heredado";
        
        propagatedCount++;
     }
   });
   
   console.log(`[Consensus] ✅ Finished. Propagated to ${propagatedCount} items.`);
}


function updateAlbumGallery() {
  const saved = JSON.parse(localStorage.getItem("rg_saved_captions_v1") || "{}");
  const albums = {};
  
  Object.entries(saved).forEach(([id, photo]) => {
    // Group strictly by POI Title (Merge different dates)
    const title = photo.caption.split(',').pop().trim();
    if (!title) return; 
    
    // Validate timestamp
    const ts = photo.date || photo.ts || Date.now();
    
    if (!albums[title]) {
      albums[title] = { 
        title, 
        count: 0, 
        photos: [], 
        preview: null,
        minTs: ts,
        maxTs: ts
      };
    }
    
    const album = albums[title];
    album.count++;
    album.photos.push({ id, ...photo });
    album.minTs = Math.min(album.minTs, ts);
    album.maxTs = Math.max(album.maxTs, ts);
    
    // Use first valid photo as preview
    if (!album.preview) {
      const thumb = document.querySelector(`.photoItem[data-id="${id}"] img`);
      if (thumb) album.preview = thumb.src;
    }
  });

  if (!el.albumGallery) return;
  el.albumGallery.innerHTML = "";
  
  // Show All / Reset Button
  if (Object.keys(albums).length > 0) {
     const resetCard = document.createElement("button");
     resetCard.className = "btn";
     resetCard.style.marginBottom = "10px";
     resetCard.textContent = "📑 Mostrar Todo / Reset";
     resetCard.onclick = () => filterByAlbum(null);
     el.albumGallery.appendChild(resetCard);
  }

  Object.entries(albums).forEach(([title, album]) => {
    const card = document.createElement("div");
    card.className = "album-card";
    const bgStyle = album.preview ? `background-image: url(${album.preview}); background-size: cover;` : `background: linear-gradient(45deg, var(--accent), var(--accent-secondary));`;
    
    // Format Date Range
    const d1 = new Date(album.minTs);
    const d2 = new Date(album.maxTs);
    const m1 = d1.toLocaleDateString(currentLanguage, { month: 'long', year: 'numeric' });
    const m2 = d2.toLocaleDateString(currentLanguage, { month: 'long', year: 'numeric' });
    const dateDisplay = (m1 === m2) ? m1 : `${m1} - ${m2}`;
    
    card.innerHTML = `
      <div class="album-cover-stack" style="${bgStyle}">
        <div class="album-count-badge">${album.count} fotos</div>
      </div>
      <div class="album-info">
        <div class="album-title">${album.title}</div>
        <div class="album-meta">${dateDisplay}</div>
      </div>
    `;
    card.onclick = () => filterByAlbum(album.title, album.photos);
    el.albumGallery.appendChild(card);
  });
}

function filterByAlbum(title, albumPhotos = []) {
   console.log("Filtrando por:", title);
   
   // 1. Limpiar markers previos del álbum
   if (albumMarkers) {
      albumMarkers.forEach(m => m.map = null);
      albumMarkers = [];
   } else {
     albumMarkers = [];
   }

   if (!title) {
     // RESET: Mostrar todo
     document.querySelectorAll(".photoItem").forEach(item => item.style.display = "flex");
     if (photoMarker) photoMarker.map = map;
     return;
   }

   // 2. Filtrar lista de fotos en UI
   const idsInAlbum = new Set(albumPhotos.map(p => p.id));
   document.querySelectorAll(".photoItem").forEach(item => {
     const id = item.dataset.id;
     item.style.display = idsInAlbum.has(id) ? "flex" : "none";
   });

   // 3. Crear markers para el álbum
   const bounds = new google.maps.LatLngBounds();
   let hasCoords = false;

   albumPhotos.forEach(p => {
     if (p.lat && p.lng) {
       const pos = { lat: Number(p.lat), lng: Number(p.lng) };
       const marker = new google.maps.marker.AdvancedMarkerElement({
         position: pos,
         map: map,
         title: p.caption
       });
       albumMarkers.push(marker);
       bounds.extend(pos);
       hasCoords = true;
     }
   });

   if (hasCoords) {
     map.fitBounds(bounds);
     if (map.getZoom() > 18) map.setZoom(17);
   }
}
