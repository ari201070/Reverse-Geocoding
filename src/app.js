// Cliente: maneja UI, EXIF, mapa y llama al endpoint /api/find-poi (serverless)
// Requiere que deployes api/find-poi en /api o uses vercel dev para desarrollo local.

const el = {
  consent: document.getElementById("consent"),
  anonymize: document.getElementById("anonymize"),
  stripExif: document.getElementById("stripExif"),
  radiusRange: document.getElementById("radiusRange"),
  radiusValue: document.getElementById("radiusValue"),
  imagesInput: document.getElementById("imagesInput"),
  photosList: document.getElementById("photosList"),
  mapDiv: document.getElementById("map"),
  selectedInfo: document.getElementById("selectedInfo"),
  placesList: document.getElementById("placesList"),
};

let map, photoMarker, radiusCircle;
let currentSelected = null;
function initMap() {
  // @ts-ignore
  map = L.map(el.mapDiv).setView([-34.6037, -58.3816], 5);
  // @ts-ignore
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  map.on("click", async (e) => {
    if (!currentSelected) {
      alert("Seleccioná una foto primero.");
      return;
    }
    const { lat, lng } = e.latlng;
    updateMarkerAndCircle(lat, lng);
    await handleFindPoi(lat, lng, currentSelected.itemEl);
  });
}
function updateMarkerAndCircle(lat, lng) {
  if (!map) return;
  // @ts-ignore
  if (!photoMarker) photoMarker = L.marker([lat, lng]).addTo(map);
  else photoMarker.setLatLng([lat, lng]);
  const radius = Number(el.radiusRange.value) || 500;
  // @ts-ignore
  if (!radiusCircle)
    radiusCircle = L.circle([lat, lng], {
      radius,
      color: "#3388ff",
      opacity: 0.3,
    }).addTo(map);
  else {
    radiusCircle.setLatLng([lat, lng]);
    radiusCircle.setRadius(radius);
  }
  map.setView([lat, lng], Math.max(13, Math.round(14 - Math.log(radius) + 1)));
}

el.radiusRange.addEventListener("input", async () => {
  el.radiusValue.textContent = el.radiusRange.value;
  if (radiusCircle && currentSelected && currentSelected.lat) {
    radiusCircle.setRadius(Number(el.radiusRange.value));
    await handleFindPoi(
      currentSelected.lat,
      currentSelected.lng,
      currentSelected.itemEl
    );
  }
});

initMap();
el.radiusValue.textContent = el.radiusRange.value;

el.imagesInput.addEventListener("change", async (ev) => {
  const files = Array.from(ev.target.files || []);
  for (const file of files) {
    await processImageFile(file);
  }
});

function roundCoords(lat, lng, decimals = 4) {
  const f = Math.pow(10, decimals);
  return [Math.round(lat * f) / f, Math.round(lng * f) / f];
}

async function processImageFile(file) {
  const id = `${file.name}_${file.size}_${file.lastModified}`;
  const imgUrl = URL.createObjectURL(file);

  const item = document.createElement("div");
  item.className = "photoItem";
  item.dataset.id = id;
  const img = document.createElement("img");
  img.className = "photoThumb";
  img.src = imgUrl;
  img.alt = file.name;
  const meta = document.createElement("div");
  meta.className = "photoMeta";
  const title = document.createElement("div");
  title.textContent = file.name;
  const metaRow = document.createElement("div");
  metaRow.className = "metaRow";
  metaRow.textContent = "Extrayendo EXIF...";
  const rowButtons = document.createElement("div");
  rowButtons.className = "rowButtons";

  const useBtn = document.createElement("button");
  useBtn.className = "btn";
  useBtn.textContent = "Usar ubicación";
  const manualBtn = document.createElement("button");
  manualBtn.className = "btn";
  manualBtn.textContent = "Marcar manualmente";
  const saveBtn = document.createElement("button");
  saveBtn.className = "btn primary";
  saveBtn.textContent = "Guardar sugerido";

  rowButtons.appendChild(useBtn);
  rowButtons.appendChild(manualBtn);
  rowButtons.appendChild(saveBtn);
  meta.appendChild(title);
  meta.appendChild(metaRow);
  meta.appendChild(rowButtons);
  item.appendChild(img);
  item.appendChild(meta);
  el.photosList.prepend(item);

  // Extraer EXIF
  let exif = null;
  try {
    exif = await window.exifr.parse(file, {
      gps: true,
      exif: true,
      iptc: false,
    });
  } catch (e) {
    console.warn("exifr error", e);
  }

  let lat, lng, dateTaken;
  if (exif && exif.latitude && exif.longitude) {
    lat = exif.latitude;
    lng = exif.longitude;
    dateTaken = exif.DateTimeOriginal || exif.DateTime || "";
    metaRow.textContent = `Coordenadas: ${lat.toFixed(6)}, ${lng.toFixed(6)}${
      dateTaken ? " · " + dateTaken : ""
    }`;
    useBtn.disabled = false;
    manualBtn.disabled = false;
  } else {
    metaRow.textContent = "No se encontraron coordenadas EXIF en esta imagen.";
    useBtn.disabled = true;
    manualBtn.disabled = false;
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
    alert("Hacé click en el mapa para establecer ubicación para esta foto.");
    highlightSelectedPhoto(item);
  });

  saveBtn.addEventListener("click", () => {
    const caption = item.dataset.selectedCaption;
    if (!caption) {
      alert("No hay sugerencia seleccionada.");
      return;
    }
    // Guardar local como ejemplo
    const saved = JSON.parse(
      localStorage.getItem("rg_saved_captions_v1") || "{}"
    );
    saved[id] = { caption, ts: Date.now() };
    localStorage.setItem("rg_saved_captions_v1", JSON.stringify(saved));
    alert("Sugerencia guardada localmente.");
  });

  const captions = JSON.parse(
    localStorage.getItem("rg_saved_captions_v1") || "{}"
  );
  if (captions[id] && captions[id].caption) {
    item.dataset.selectedCaption = captions[id].caption;
    const s = document.createElement("div");
    s.className = "small";
    s.textContent = "Caption guardado: " + captions[id].caption;
    meta.appendChild(s);
  }
}

function highlightSelectedPhoto(itemEl) {
  document
    .querySelectorAll(".photoItem")
    .forEach((i) => (i.style.boxShadow = "none"));
  if (itemEl) itemEl.style.boxShadow = "0 0 0 2px rgba(43,124,255,0.15)";
}

async function handleFindPoi(lat, lng, itemEl) {
  el.selectedInfo.textContent = "Buscando POI...";
  el.placesList.innerHTML = "";

  // aplicar anonimizado si seleccionado al mostrar/guardar
  const anonymize = el.anonymize.checked;
  const [rlat, rlng] = anonymize ? roundCoords(lat, lng, 4) : [lat, lng];

  // preparar payload
  const payload = {
    latitude: lat,
    longitude: lng,
    radius: Number(el.radiusRange.value) || 500,
    keywords: null, // opcional: puedes extraer keywords desde análisis visual o meta
  };

  try {
    const res = await fetch("/api/find-poi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const txt = await res.text().catch(() => null);
      throw new Error(`HTTP ${res.status} ${txt || ""}`);
    }
    const data = await res.json();
    if (!data || !data.place) {
      el.placesList.innerHTML =
        '<div class="small">No se encontró lugar. Probá aumentar el radio o mover el punto.</div>';
      return;
    }

    // Mostrar resultado
    const p = data.place;
    const item = document.createElement("div");
    item.className = "placeItem";
    const info = document.createElement("div");
    info.className = "placeInfo";
    const name = document.createElement("div");
    name.className = "placeName";
    name.textContent = p.name || p.formatted_address || "Sin nombre";
    const meta = document.createElement("div");
    meta.className = "placeTypes";
    meta.textContent = `${data.source || ""} · ${
      data.distanceMeters ? data.distanceMeters + " m" : ""
    } · ${p.types ? p.types.join(", ") : ""}`;
    info.appendChild(name);
    info.appendChild(meta);
    item.appendChild(info);
    el.placesList.appendChild(item);

    // Guardar sugerencia en dataset
    itemEl.dataset.selectedCaption = p.name || p.formatted_address;
  } catch (err) {
    el.selectedInfo.textContent = "Error buscando POI.";
    el.placesList.innerHTML = `<div class="small" style="color:red">${err.message}</div>`;
  }
}
