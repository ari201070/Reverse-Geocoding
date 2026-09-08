# Master Sync Source: Project Fusion (July 2026)

## 1. Unified Architecture Principles (Antigravity 2.0)
- **Zero-OPEX:** Absolute priority for FOSS and Free Tiers.
- **Independence:** Decoupling from Google Maps and Google Vision paid APIs.
- **Spatial Sovereignty:** Local caching using H3 Resolution 9 (~11m) and PostGIS.
- **Consensus Truth Engine:** Multi-signal scoring (OCR, Landmarks, GPS) with a 75% threshold for auto-resolution.

---

## 2. Global Repository Sync Status (github.com/ari201070)
- **Reverse-Geocoding:** `2eb244d` (feat: offline geocoding, consensus, H3 optimization).
- **Travel-Booking-Document-Hub:** `c0df78f` (chore: externalized gemini initialization).
- **viaje-argentina-octubre-2025:** `ea51a02f` (Merge branch 'develop' - includes UI components for Gallery, Maps, and Vouchers).

---

## 3. Integration Core: GeoPy & Geodesic Intelligence
- **Library:** `geopy` 2.5.0 installed locally.
- **Velocity Veto Protocol:** Physical validation of movements between photos.
- **Algorithm:** Uses `geopy.distance.geodesic` to calculate the speed required between two timestamps.
- **Threshold:** >120 km/h triggers an `AMBIGUOUS` status and escalates to Level 4 (OSINT).

---

## 4. Integration Core: Geoapify Handler (API Level 4)
- **Component:** `api/geoapify-handler.js`
- **Quota:** 3,000 requests/day (Free Tier).
- **Functionality:** Provides normalized reverse geocoding (POI name, address, city, country) as a high-reliability fallback before OpenCage.

---

## 5. Merging Project: viaje-argentina-octubre-2025
- **Purpose:** Frontend and visualization layer for the 30-day Argentina trip.
- **Key Components:**
  - `GalleryDashboard.jsx` / `PhotoLightbox.jsx`: Specialized media viewing.
  - `InteractiveMap.jsx`: Leaflet-based visualization for GPS-tagged media.
  - `VoucherDashboard.jsx`: UI for flight/hotel documentation.
- **Data Link:** Uses `photo_catalog.db` as the shared source of truth.
- **Service Ports:** 
  - Georeferencing (Backend/Analysis): `http://localhost:4096`
  - Document Hub (Receipts/Anchors): `http://localhost:4097`

---

## 6. Project Link: Travel-Booking-Document-Hub
- **Scope:** Managing 30 days of trip documentation (Bookings, Tickets, Receipts).
- **Cross-Validation:** Receipts from the Hub provide "Master Anchors" for photo geocoding (e.g., a restaurant receipt confirms the location of photos taken at that time).

---

## 7. OSINT & Forensics (Level 4 Escalation)
- **Tools:** TinEye (pixel match), Yandex (texture/pattern), Wikidata.
- **Visual Prep:** Mandatory use of GIMP (Perspective Correction) to flatten images before reverse visual search.
- **Human-in-the-Loop:** Required when consensus score < 0.75.
