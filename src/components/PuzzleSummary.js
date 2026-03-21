
/**
 * Renders the Puzzle Summary UI for Batch Consensus
 * @param {HTMLElement} container - The DOM element to render into
 * @param {Object} batchData - Data object containing consensus results and image list
 */
export function renderPuzzleSummary(container, batchData) {
  const { consensus_result, images } = batchData;
  if (!container) return;
  
  // Icons (Lucide implementation as inline SVG)
  const icons = {
    shield: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>`,
    alert: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`,
    mapPin: `<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-0.5"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>`,
    eye: `<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-0.5"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`,
    type: `<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-0.5"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>`
  };

  const isWarning = consensus_result.is_warning || consensus_result.confidence_score < 0.75;
  const headerClass = isWarning ? 'border-amber-500 bg-amber-50' : 'border-green-500 bg-white';
  const scoreClass = isWarning ? 'text-amber-600 bg-amber-100' : 'text-green-600 bg-green-50';

  const html = `
    <div class="max-w-4xl mx-auto p-4 bg-slate-50 rounded-lg shadow-sm border border-slate-200 font-sans mt-4 mb-4">
      <!-- Header: Resultado del Consenso -->
      <div class="mb-4 p-3 rounded border-l-4 ${headerClass} shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
        <div class="flex-1">
           <h2 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Ubicación Inteligente</h2>
           <p class="text-base font-bold text-slate-800 leading-tight truncate-multiline">${consensus_result.place_name || "Buscando..."}</p>
        </div>
        <div class="flex flex-col items-end shrink-0">
           <div class="flex items-center ${scoreClass} px-2 py-1 rounded">
             ${isWarning ? icons.alert : icons.shield}
             <span class="text-[11px] font-bold">Confianza: ${(consensus_result.confidence_score * 100).toFixed(0)}%</span>
           </div>
           <p class="mt-1 text-[10px] text-slate-500 italic text-right max-w-[180px] leading-tight">"${consensus_result.match_reason}"</p>
        </div>
      </div>

      <!-- Grid del Puzzle -->
      <div class="max-h-60 overflow-y-auto pr-1">
        <div class="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
          ${images.map(img => `
            <div class="relative rounded overflow-hidden border ${img.role === 'ANCHOR_VISUAL' ? 'border-blue-500 ring-2 ring-blue-100' : 'border-slate-200'} bg-white hover:scale-105 transition-transform">
              <div class="aspect-square bg-slate-100 flex items-center justify-center text-slate-300 relative">
                 ${img.url ? `<img src="${img.url}" class="w-full h-full object-cover" loading="lazy" />` : `<span class="text-[9px]">IMG</span>`}
                 ${img.role === 'ANCHOR_VISUAL' ? `<div class="absolute top-0 right-0 bg-blue-600 text-white text-[8px] font-bold px-1 rounded-bl">ANCLA</div>` : ''}
              </div>
              
              <!-- Mini Badges -->
              <div class="p-1 context-badges bg-white/90">
                <div class="flex gap-1 flex-wrap justify-center">
                  ${img.exif?.has_gps ? `<span class="text-[9px] text-blue-600" title="GPS">${icons.mapPin}</span>` : ''}
                  ${img.vision_analysis?.landmark ? `<span class="text-[9px] text-purple-600" title="Hito">${icons.eye}</span>` : ''}
                  ${img.vision_analysis?.ocr_text ? `<span class="text-[9px] text-amber-600" title="Texto">${icons.type}</span>` : ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
      
      ${isWarning ? `
        <div class="mt-3 p-2 bg-amber-100/50 rounded text-[11px] text-amber-800 flex items-center border border-amber-200">
          ${icons.alert} <span><strong>Sugerencia:</strong> El sistema tiene dudas. Revisa las fotos sin "Ancla" o agrega una manualmente.</span>
        </div>
      ` : ''}
    </div>
  `;

  container.innerHTML = html;
}
