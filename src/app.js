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
  
  for (const file of Array.from(files)) {
    const id = `${file.name}-${file.size}-${file.lastModified}`;
    const batchItem = {
      file, id, title: file.name, lat: null, lng: null, date: "", poi: null, consensus: false, visionLabels: []
    };

    // UI Item
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

    const poiInput = itemEl.querySelector(".batch-poi");
    const statusMsg = itemEl.querySelector(".status-msg");
    const coordsDiv = itemEl.querySelector(".batch-coords");
    const searchBtn = itemEl.querySelector(".btn-search");

    // Extract EXIF Greedy
    try {
      // @ts-ignore
      const fullMeta = await window.exifr.parse(file, { gps: true, exif: true, xmp: true, iptc: true });
      const coords = extractGpsCascading(fullMeta);
      
      if (coords) {
        batchItem.lat = coords.lat;
        batchItem.lng = coords.lng;
        batchItem.date = fullMeta.DateTimeOriginal || fullMeta.DateTime || "";
        itemEl.querySelector(".batch-date").value = batchItem.date;
        coordsDiv.textContent = `${batchItem.lat.toFixed(6)}, ${batchItem.lng.toFixed(6)}`;
        
        // 1. Analyze with Vision AI first
        statusMsg.textContent = t("status_analyzing");
        const visionDiv = itemEl.querySelector(".vision-tags");
        try {
           const labels = await analyzeImage(file);
           if (labels && labels.length > 0) {
             batchItem.visionLabels = labels;
             visionDiv.textContent = t("vision_detected") + " " + labels.slice(0, 3).join(", ");
           }
        } catch (vErr) { console.warn("Vision err in batch", vErr); }

        // 2. Search POI with keywords
        statusMsg.textContent = t("status_searching_poi");
        await performSearch(batchItem, poiInput, statusMsg);
      } else {
        // Fallback Level 3: Picarta AI
        let picartaSuccess = false;
        if (el.usePicarta.checked) {
           statusMsg.textContent = t("status_analyzing") + " (Picarta)...";
           const picartaLoc = await localizeWithPicarta(file);
           if (picartaLoc) {
              batchItem.lat = picartaLoc.lat;
              batchItem.lng = picartaLoc.lng;
              batchItem.source = 'picarta';
              batchItem.isEstimated = true;
              
              const pBadge = document.createElement("span");
              pBadge.className = "badge";
              pBadge.textContent = "✨ AI LOC";
              pBadge.style.background = "var(--accent)";
              pBadge.style.marginLeft = "5px";
              itemEl.querySelector(".title").appendChild(pBadge);
              
              coordsDiv.textContent = `${batchItem.lat.toFixed(6)}, ${batchItem.lng.toFixed(6)}`;
              
              // Proceed to search POI
              statusMsg.textContent = t("status_searching_poi");
              await performSearch(batchItem, poiInput, statusMsg);
              picartaSuccess = true;
           }
        }

        if (!picartaSuccess) {
            coordsDiv.innerHTML = `${t('status_found_geocoder').split('(')[0]} <button class="btn-mini btn-manual-geo" title="${t('btn_manual_geo')}">📍</button>`;
            statusMsg.textContent = t("status_no_coords");
            
            // Manual geo button logic
            coordsDiv.querySelector(".btn-manual-geo").onclick = () => {
              alert(t("manual_geo_alert"));
              window.pendingManualGeo = { batchItem, itemEl, coordsDiv, statusMsg, poiInput, file };
              el.batchModal.style.display = "none"; // Hide to let user click
            };
        }
      }
    } catch (e) {
      console.warn("Exif error in batch", e);
      coordsDiv.textContent = "Error EXIF";
    }

    batchFiles.push({ ...batchItem, el: itemEl });
    applyConsensus();

    // Listen for manual changes to trigger consensus
    poiInput.addEventListener("input", () => {
      const currentVal = poiInput.value.trim();
      const bf = batchFiles.find(b => b.id === id);
      if (bf) bf.poi = currentVal;
      applyConsensus();
    });

    searchBtn.addEventListener("click", () => performSearch(batchItem, poiInput, statusMsg));
  }
}

async function performSearch(batchItem, poiInput, statusMsg) {
  if (!batchItem.lat || !batchItem.lng) return;
  // For large POIs like "Aquafan", a small radius fails.
  // Use slider radius but ensure it's at least 500 for the fallback.
  const radius = Math.max(parseInt(el.radiusRange.value) || 20, 500);
  const keywords = (batchItem.visionLabels || []).join(" ");
  
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
        type: (batchItem.visionLabels && batchItem.visionLabels.length) ? undefined : 'tourist_attraction',
        keyword: (batchItem.visionLabels || []).join(" ") || undefined
      };
      console.log("Searching POI near:", request.location, "with radius:", radius);

      service.nearbySearch(request, (results, status) => {
        try {
          if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length > 0) {
            // Ranking logic: tourist attractions and malls first, then others
            const best = results.sort((a, b) => {
              const score = (r) => {
                let s = 0;
                if (r.types.includes('tourist_attraction')) s += 10;
                if (r.types.includes('shopping_mall')) s += 9;
                if (r.types.includes('park')) s += 8;
                if (r.types.includes('museum')) s += 8;
                if (r.types.includes('point_of_interest')) s += 5;
                if (r.types.includes('establishment')) s += 2;
                return s;
              };
              return score(b) - score(a);
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
      const poi = results.find(r => 
        r.types.includes("point_of_interest") || 
        r.types.includes("establishment") || 
        r.types.includes("park") ||
        r.types.includes("tourist_attraction")
      );
      const best = poi || results[0];
      let name = best.formatted_address;
      // If it's an address, try to get street name + number instead of just index 0
      if (!poi && best.address_components.length > 1) {
         const street = best.address_components.find(c => c.types.includes("route"))?.long_name;
         const num = best.address_components.find(c => c.types.includes("street_number"))?.long_name;
         if (street) name = street + (num ? " " + num : "");
      }

      batchItem.poi = name;
      poiInput.value = name;
      statusMsg.textContent = t("status_found_geocoder");
      applyConsensus();
    } else {
      statusMsg.textContent = "No se encontraron resultados.";
    }
  });
}

// --- Consensus Logic ---
function applyConsensus() {
  const counts = {};
  let bestPoi = null;
  let maxCount = 0;

  batchFiles.forEach(bf => {
    if (bf.poi && bf.poi.trim().length > 0) {
      counts[bf.poi] = (counts[bf.poi] || 0) + 1;
      if (counts[bf.poi] > maxCount) {
        maxCount = counts[bf.poi];
        bestPoi = bf.poi;
      }
    }
  });

  // If > 2 photos have the same POI, apply consensus to others ONLY IF THEY ARE EMPTY
  if (maxCount >= 2 && bestPoi) {
    batchFiles.forEach(bf => {
      const poiInput = bf.el.querySelector(".batch-poi");
      if (!poiInput.value.trim()) {
        bf.poi = bestPoi;
        poiInput.value = bestPoi;
        bf.consensus = true;
        
        const consensusArea = bf.el.querySelector(".consensus-area");
        consensusArea.innerHTML = `<span class="consensus-badge">${t('consensus_badge')}</span>`;
      }
    });
  }
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
      // ... same click logic ...
      const lat = e.latLng.lat();


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
    photoMarker = new google.maps.Marker({
      position: pos,
      map: map,
      title: "Foto",
      animation: google.maps.Animation.DROP
    });
  } else {
    photoMarker.setPosition(pos);
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
    analyzeImage(file).then(labels => {
      if (labels && labels.length > 0) {
        item.dataset.visionLabels = labels.join(',');
        const labelsTag = document.createElement("div");
        labelsTag.className = "small";
        labelsTag.style.color = "var(--accent)";
        labelsTag.textContent = t("vision_detected") + " " + labels.slice(0, 3).join(', ');
        meta.insertBefore(labelsTag, title);
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
           resolve(data.labels || []);
        } else {
           resolve([]);
        }
      } catch (e) {
        console.warn("Vision AI skipped:", e.message);
        resolve([]);
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
  const keywords = itemEl.dataset.visionLabels || null;

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
  if (!window.google || !window.google.maps || !window.google.maps.places) {
    el.selectedInfo.textContent = "Error: Buscador local de Google no disponible.";
    return;
  }

  el.selectedInfo.textContent = t("status_searching_local");
  const radius = Math.max(Number(el.radiusRange.value) || 20, 500); 
  const service = new google.maps.places.PlacesService(el.mapDiv);
  const request = {
    location: { lat, lng },
    radius: radius,
    type: keywords ? undefined : 'tourist_attraction',
    keyword: keywords || undefined
  };

  service.nearbySearch(request, (results, status) => {
    try {
      if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length > 0) {
        // Ranking logic: tourist attractions and malls first, then others
        const best = results.sort((a, b) => {
          const score = (r) => {
            let s = 0;
            if (r.types.includes('tourist_attraction')) s += 10;
            if (r.types.includes('shopping_mall')) s += 9;
            if (r.types.includes('park')) s += 8;
            if (r.types.includes('museum')) s += 8;
            if (r.types.includes('point_of_interest')) s += 5;
            if (r.types.includes('establishment')) s += 2;
            return s;
          };
          return score(b) - score(a);
        })[0];

        const data = {
          source: 'local_fallback',
          place: {
            name: best.name,
            formatted_address: best.vicinity || best.formatted_address,
            geometry: best.geometry,
            types: best.types
          },
          plus_code: best.plus_code
        };
        renderPoiResult(data, itemEl);
      } else {
        el.selectedInfo.textContent = t("status_no_coords");
      }
    } catch (e) {
      el.selectedInfo.textContent = "Error en el buscador local.";
    }
  });
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
 * Picarta AI Integration (Visual Geolocation)
 */
async function localizeWithPicarta(file) {
  const token = import.meta.env.VITE_PICARTA_API_TOKEN;
  if (!token || !el.usePicarta.checked) return null;

  console.log("Attempting Picarta AI localization...");
  
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = async () => {
      try {
        const base64 = reader.result.split(',')[1];
        const res = await fetch("https://picarta.ai/classify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            TOKEN: token,
            IMAGE: base64,
            TOP_K: 1
          })
        });

        if (res.ok) {
          const data = await res.json();
          console.log("Picarta Response:", data);
          
          if (data && data.ai_lat && data.ai_lon) {
            resolve({
              lat: data.ai_lat,
              lng: data.ai_lon,
              source: 'picarta',
              city: data.city || '',
              country: data.country || ''
            });
            return;
          }
        }
      } catch (e) {
        console.warn("Picarta AI failed:", e);
      }
      resolve(null);
    };
    reader.readAsDataURL(file);
  });
}

// Global hook for manual geocoding from modal

window.addEventListener("click", (e) => {
  if (window.pendingManualGeo && typeof map !== 'undefined') {
    // Si hay un geoposicionamiento pendiente y se hizo clic en el mapa
    // Esto se maneja mejor integrándolo en el listener de clic del mapa mismo
  }
});

initMap();
