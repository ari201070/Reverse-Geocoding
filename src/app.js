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

async function setLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem("language", lang);
  await initI18n();
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
    const id = `${file.name}-${file.size}-${file.lastModified}`;
    const batchItem = {
      file, id, title: file.name, lat: null, lng: null, date: "", poi: null, consensus: false, visionLabels: []
    };

    const itemEl = document.createElement("div");
    itemEl.className = "batch-item";
    itemEl.innerHTML = `
      <img src="${URL.createObjectURL(file)}" />
      <div class="batch-item-fields">
        <input type="text" class="batch-title" value="${file.name}" placeholder="${t('app_title')}..." />
        <input type="text" class="batch-date" placeholder="${t('status_analyzing')}..." />
        <div class="batch-coords small" style="opacity:0.6; font-size:0.7rem">${t('status_searching_poi')}...</div>
      </div>
      <div class="batch-item-fields">
        <div style="display:flex; gap:5px">
          <input type="text" class="batch-poi" placeholder="Lugar (POI)..." style="flex:1" />
          <button class="btn btn-search" title="Buscar de nuevo">🔍</button>
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

  // --- Phase 1: FAST Parallel Metadata/Vision (Global Signal First) ---
  // This allows any photo to share its findings with others immediately
  await Promise.all(items.map(async (itm) => {
    try {
      itm.statusMsg.textContent = t("status_analyzing");
      
      // EXIF Parallel
      const fullMeta = await window.exifr.parse(itm.file, { gps: true, exif: true, xmp: true, iptc: true });
      const coords = extractGpsCascading(fullMeta);
      if (coords) {
        itm.lat = coords.lat;
        itm.lng = coords.lng;
        const d = fullMeta.DateTimeOriginal || fullMeta.DateTime || null;
        itm.date = d instanceof Date ? d.getTime() : (typeof d === 'number' ? d : itm.file.lastModified);
        itm.el.querySelector(".batch-date").value = d instanceof Date ? d.toLocaleString() : new Date(itm.date).toLocaleString();
        itm.coordsDiv.textContent = `${itm.lat.toFixed(6)}, ${itm.lng.toFixed(6)}`;
      }

      // Vision Parallel
      const visionData = await analyzeImage(itm.file);
      if (visionData) {
        const { labels, landmarks, texts } = visionData;
        itm.visionLabels = labels;
        itm.visionLandmarks = landmarks;
        itm.visionTexts = texts;
        
        const primaryTag = landmarks[0] || texts[0] || labels[0] || "";
        if (primaryTag) {
          itm.visionDiv.textContent = "🔍 " + t("vision_detected") + ": " + primaryTag;
          if (landmarks[0] || (texts[0] && texts[0].length > 3)) {
            itm.poiInput.value = landmarks[0] || texts[0];
            itm.poi = landmarks[0] || texts[0];
            itm.poiKeywords = landmarks[0] || texts[0];
          }
        }
      }
      
      // Proactive consensus after each quick signal to propagate landmarks ASAP
      applyConsensus();
    } catch (err) {
      console.warn("Signal extraction failed for item", itm.id, err);
    }
  }));

  // --- Phase 2: Deep Search & Fallbacks ---
  // Now that we have all metadata and initial consensus, we search or fallback
  for (const itm of items) {
    if (itm.poi && !isGenericName(itm.poi) && itm.consensus) {
       // already has a strong name from neighborhood consensus
       itm.statusMsg.textContent = t("status_found_backend");
       continue; 
    }

    if (itm.lat && itm.lng) {
      itm.statusMsg.textContent = t("status_searching_poi");
      await performSearch(itm, itm.poiInput, itm.statusMsg);
    } else {
      // Final Fallback: Picarta
      if (el.usePicarta.checked) {
        itm.statusMsg.textContent = t("status_analyzing") + " (Picarta)...";
        const aiLoadingBadge = document.createElement("span");
        aiLoadingBadge.className = "badge ai-loading-pulse";
        aiLoadingBadge.textContent = "✨ AI GEOLOCATING...";
        aiLoadingBadge.style.background = "var(--purple-600)";
        itm.el.querySelector(".batch-item-fields").appendChild(aiLoadingBadge);

        const picartaLoc = await localizeWithPicarta(itm.file);
        aiLoadingBadge.remove();

        if (picartaLoc) {
          itm.lat = picartaLoc.lat;
          itm.lng = picartaLoc.lng;
          itm.source = 'picarta';
          itm.isEstimated = true;
          
          const pBadge = document.createElement("span");
          pBadge.className = "ai-badge-premium";
          pBadge.innerHTML = `✨ AI: ${picartaLoc.city || 'Ubicación'} (${picartaLoc.country || 'Estimada'})`;
          itm.el.querySelector(".batch-item-fields").appendChild(pBadge);
          itm.coordsDiv.textContent = `${itm.lat.toFixed(6)}, ${itm.lng.toFixed(6)}`;
          
          itm.statusMsg.textContent = t("status_searching_poi");
          await performSearch(itm, itm.poiInput, itm.statusMsg);
        } else {
          showManualGeoFallback(itm);
        }
      } else {
        showManualGeoFallback(itm);
      }
    }
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
function applyConsensus() {
  const clusters = clusterPhotosByContext(batchFiles);
  
  clusters.forEach(cluster => {
    if (cluster.length > 1) { // Only consensus if more than 1
      const result = getMostCommonCaption(cluster);
      const consensusCaption = result.winner;
      const scores = result.scores;
      
      if (consensusCaption) {
        cluster.forEach(bf => {
          const pi = bf.el.querySelector(".batch-poi");
          const inputVal = pi ? pi.value.trim() : "";
          
          // Scoring logic (v2.2):
          // 1. If consensusCaption is a landmark and inputVal is just an establishment, consensus wins.
          // 2. If consensusCaption has a significantly higher score (e.g. 2x) than inputVal, consensus wins.
          const consensusScore = scores.get(consensusCaption) || 0;
          const inputScore = scores.get(inputVal) || 0;

          const isConsensusLandmark = /jardin|jardín|parque|museo|monumento|plaza|palacio|recoleta|tigre/i.test(consensusCaption);
          const isInputEstablishment = !isConsensusLandmark && inputVal.length > 0;

          const isBetter = (!isGenericName(consensusCaption) && isGenericName(inputVal)) || 
                           (isConsensusLandmark && isInputEstablishment) ||
                           (consensusScore > (inputScore * 1.5) && consensusScore > 5);
          
          if (!inputVal || bf.consensus || isBetter) {
             bf.poi = consensusCaption;
             bf.consensus = true;
             if (pi) pi.value = consensusCaption;
             
             const ca = bf.el.querySelector(".consensus-area");
             if (ca) ca.innerHTML = `<span class="consensus-badge">${t('consensus_badge')}</span>`;
          }
        });
      }
    }
  });
}

function clusterPhotosByContext(photos) {
  const clusters = [];
  const processed = new Set();
  
  for (const photo of photos) {
    if (processed.has(photo)) continue;
    const cluster = [photo];
    processed.add(photo);
    
    for (const other of photos) {
      if (processed.has(other)) continue;
      if (!photo.lat || !photo.lng || !other.lat || !other.lng) continue;

      // Group: < 10 mins AND < 150 meters (More generous for large parks/attractions)
      const timeDiff = Math.abs((photo.date || 0) - (other.date || 0));
      const dist = calculateDistance(photo.lat, photo.lng, other.lat, other.lng);
      
      if (timeDiff < (10 * 60 * 1000) && dist < 150) { 
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
      // Scoring (v2.2): 
      let points = 1;
      const isGeneric = isGenericName(name);
      if (!isGeneric) points += 50; // Gran bonus por no ser genérico/ruido
      
      const isLandmarkString = /jardin|jardín|parque|museo|monumento|plaza|palacio|recoleta|tigre|plazoleta/i.test(l);
      if (isLandmarkString) points += 100; // Landmark es ley (x100)
      
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
    saved[saveId] = { caption: finalCaption, ts: Date.now() };
    localStorage.setItem("rg_saved_captions_v1", JSON.stringify(saved));
  });
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
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
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
      locationRestricted: {
        center: { lat, lng },
        radius: radius
      },
      fields: ['displayName', 'formattedAddress', 'location', 'types', 'plusCode']
    };

    // If we have keywords, we use them to bias the search
    // Note: searchNearby v4 doesn't have a direct 'keyword' field like textSearch,
    // but we can filter/rank results or use textSearch if keywords are present.
    // For now, let's stick to nearby and rank results by keyword match.

    const { places } = await Place.searchNearby(request);

    if (places && places.length > 0) {
      // Logic: Rank by specificity and keyword match
      const ranked = places.map(p => ({
        name: p.displayName,
        formatted_address: p.formattedAddress,
        geometry: { location: { lat: p.location.lat(), lng: p.location.lng() } },
        types: p.types,
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
