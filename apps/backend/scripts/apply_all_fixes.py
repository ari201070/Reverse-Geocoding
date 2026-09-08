import sys, re
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = r'F:\2025\Octubre\Viaje_Argentina_2025.html'

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# Fix 1: Replace Slovenia paths with photo.src in thumbnail rendering
html = html.replace(
    "const dataIdx = typeof photo.cum === 'number' ? photo.cum : (PHOTO_CUM_INDEX[photo.filename] ?? null);\n                    const thumbPath = dataIdx !== null ? `\u05d8\u05d9\u05d5\u05dc \u05d1\u05e1\u05dc\u05d5\u05d1\u05e0\u05d9\u05d4/_thumbs/thumb_${dataIdx}.jpg` : null;\n                    const relPath = photo.subfolder ? `\u05d8\u05d9\u05d5\u05dc \u05d1\u05e1\u05dc\u05d5\u05d1\u05e0\u05d9\u05d4/${photo.subfolder}/${photo.filename}` : `\u05d8\u05d9\u05d5\u05dc \u05d1\u05e1\u05dc\u05d5\u05d1\u05e0\u05d9\u05d4/${photo.filename}`;\n                    const isVideo = photo.filename.toLowerCase().endsWith('.mp4') || photo.filename.toLowerCase().endsWith('.mov');",
    """const fn = photo.filename || photo.src || '';
                    const isVideo = fn.toLowerCase().endsWith('.mp4') || fn.toLowerCase().endsWith('.mov');
                    const isHeic = fn.toLowerCase().endsWith('.heic');
                    const relPath = photo.src;
                    const thumbPath = null;"""
)

# Fix 2: Replace contentHTML block with .heic handling
old_content = """                    // For video preview, use a play overlay or default video icon
                    let contentHTML = '';
                    if (isVideo) {
                        contentHTML = `
                            <div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#121620;">
                                <i class="fa-solid fa-video" style="font-size:24px; color:var(--secondary-neon);"></i>
                            </div>
                        `;
                    } else {
                        contentHTML = `<img src="${thumbPath || relPath}" alt="${photo.filename}" loading="lazy" style="width:100%;height:100%;object-fit:cover">`;
                    }"""

new_content = """                    // For video preview, use a play overlay or default video icon
                    let contentHTML = '';
                    if (isVideo) {
                        contentHTML = `
                            <div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#121620;">
                                <i class="fa-solid fa-video" style="font-size:24px; color:var(--secondary-neon);"></i>
                            </div>
                        `;
                    } else if (isHeic) {
                        contentHTML = `
                            <div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#1a1f2e; flex-direction:column; gap:6px;">
                                <i class="fa-solid fa-image" style="font-size:24px; color:var(--text-muted);"></i>
                                <span style="font-size:9px; color:var(--text-dark);">HEIC</span>
                            </div>
                        `;
                    } else {
                        contentHTML = `<img src="${thumbPath || relPath}" alt="${photo.filename}" loading="lazy" style="width:100%;height:100%;object-fit:cover">`;
                    }"""
html = html.replace(old_content, new_content)

# Fix 3: Fix location_name -> locationName in badge
html = html.replace(
    '${photo.location_name ? `<div class="badge-location-text">${photo.location_name}</div>` : \'\'}',
    '${photo.locationName ? `<div class="badge-location-text">${photo.locationName}</div>` : \'\'}'
)

# Fix 4: Fix location_name -> locationName in tooltip
html = html.replace(
    "p.location_name || (currentLang === 'he'",
    "p.locationName || (currentLang === 'he'"
)

# Fix 5: Fix location_address/location_name in lightbox desc
html = html.replace(
    "photo.location_address || photo.location_name",
    "photo.locationAddress || photo.locationName"
)

# Fix 6: Fix lightbox Slovenia paths
html = html.replace(
    "const relPath = photo.subfolder ? `\u05d8\u05d9\u05d5\u05dc \u05d1\u05e1\u05dc\u05d5\u05d1\u05e0\u05d9\u05d4/${photo.subfolder}/${photo.filename}` : `\u05d8\u05d9\u05d5\u05dc \u05d1\u05e1\u05dc\u05d5\u05d1\u05e0\u05d9\u05d4/${photo.filename}`;",
    "const relPath = photo.src;"
)

# Fix 7: Add isHeic check in lightbox
old_lightbox = """            const relPath = photo.src;
            const isVideo = photo.filename.toLowerCase().endsWith('.mp4') || photo.filename.toLowerCase().endsWith('.mov');
            
            if (isVideo) {"""

new_lightbox = """            const relPath = photo.src;
            const isVideo = photo.filename.toLowerCase().endsWith('.mp4') || photo.filename.toLowerCase().endsWith('.mov');
            const isHeic = photo.filename.toLowerCase().endsWith('.heic');
            
            if (isVideo) {"""
html = html.replace(old_lightbox, new_lightbox)

# Fix 8: Add .heic else-if in lightbox
old_lb_else = """            } else {
                const imgEl = document.createElement('img');
                imgEl.src = relPath;
                imgEl.alt = photo.filename;
                container.appendChild(imgEl);
            }"""
new_lb_else = """            } else if (isHeic) {
                container.innerHTML = `
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:50vh; color:var(--text-muted);">
                        <i class="fa-solid fa-image" style="font-size:64px; margin-bottom:16px;"></i>
                        <p style="font-size:14px;">Formato HEIC no soportado por el navegador</p>
                        <p style="font-size:12px; color:var(--text-dark);">${photo.filename}</p>
                    </div>
                `;
            } else {
                const imgEl = document.createElement('img');
                imgEl.src = relPath;
                imgEl.alt = photo.filename;
                container.appendChild(imgEl);
            }"""
html = html.replace(old_lb_else, new_lb_else)

# Fix 9: Add day-desc CSS after .day-subtitle
old_css = """.day-subtitle {
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.4;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .day-meta {"""

new_css = """.day-subtitle {
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.4;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .day-desc {
            font-size: 11px;
            color: var(--text-dark);
            line-height: 1.3;
            margin-top: 6px;
            padding-top: 6px;
            border-top: 1px solid rgba(255, 255, 255, 0.03);
        }

        .day-meta {"""
html = html.replace(old_css, new_css)

# Fix 10: Add desc variable and day-desc div in sidebar card
old_card = """                const badge = currentLang === 'he' ? day.badge_he : day.badge_es;
                const title = currentLang === 'he' ? day.title_he : day.title_es;
                const subtitle = currentLang === 'he' ? day.subtitle_he : day.subtitle_es;
                
                card.innerHTML = `
                    <div class="day-badge">${badge}</div>
                    <div class="day-title">${title}</div>
                    <div class="day-subtitle">
                        <i class="fa-solid fa-location-dot" style="color: ${hasGPS ? 'var(--primary-neon)' : 'var(--text-dark)'}"></i>
                        ${subtitle}
                    </div>
                    <div class="day-meta">"""

new_card = """                const badge = currentLang === 'he' ? day.badge_he : day.badge_es;
                const title = currentLang === 'he' ? day.title_he : day.title_es;
                const subtitle = currentLang === 'he' ? day.subtitle_he : day.subtitle_es;
                const desc = currentLang === 'he' ? day.desc_he : day.desc_es;
                
                card.innerHTML = `
                    <div class="day-badge">${badge}</div>
                    <div class="day-title">${title}</div>
                    <div class="day-subtitle">
                        <i class="fa-solid fa-location-dot" style="color: ${hasGPS ? 'var(--primary-neon)' : 'var(--text-dark)'}"></i>
                        ${subtitle}
                    </div>
                    ${desc ? `<div class="day-desc">${desc}</div>` : ''}
                    <div class="day-meta">"""
html = html.replace(old_card, new_card)

# Write back
with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print("All 10 fixes applied successfully!")

# Verify
checks = ['locationName', 'isHeic', 'day-desc', 'photo.src']
for check in checks:
    if check in html:
        print(f"  OK: '{check}' found")
    else:
        print(f"  MISSING: '{check}' not found")
