#!/bin/bash
# Fase 5.1: Copia final de Chipre con rutas normalizadas

REORG_PLAN="./reorganization_plan.csv"
TARGET_TRIP="cyprus"

echo "═══════════════════════════════════════════════════════════════"
echo "  FASE 5.1: COPIA FINAL - CHIPRE (RUTAS NORMALIZADAS)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

START_TIME=$(date +%s)

# Read plan and filter Cyprus
TOTAL=0
SUCCESS=0
FAILED=0

while IFS= read -r line; do
    # Skip header
    [[ "$line" == id,* ]] && continue
    
    # Parse CSV line
    IFS=',' read -r id original_path proposed_target_path trip_name has_conflict <<< "$line"
    
    # Skip non-Cyprus
    [[ "$trip_name" != "$TARGET_TRIP" ]] && continue
    
    TOTAL=$((TOTAL + 1))
    
    # Remove quotes
    src_win=$(echo "$original_path" | tr -d '"')
    dst_win=$(echo "$proposed_target_path" | tr -d '"')
    
    # Convert to Git Bash paths
    src_unix=$(echo "$src_win" | sed 's/^F:/\/f/' | sed 's/\\/\//g')
    dst_unix=$(echo "$dst_win" | sed 's/^F:/\/f/' | sed 's/\\/\//g')
    
    src_dir=$(dirname "$src_unix")
    dst_dir=$(dirname "$dst_unix")
    
    # Create target directory
    mkdir -p "$dst_dir" 2>/dev/null || true
    
    # Check if source exists
    if [ ! -f "$src_unix" ]; then
        echo "  ❌ [$TOTAL] Not found: $(basename "$src_win")"
        FAILED=$((FAILED + 1))
        continue
    fi
    
    # Get file size
    FILE_SIZE=$(stat -c%s "$src_unix" 2>/dev/null || stat -f%z "$src_unix" 2>/dev/null || echo 0)
    
    # Copy with robocopy (native Windows)
    robocopy "$(dirname "$src_win")" "$(dirname "$dst_win")" "$(basename "$src_win")" /NJH /NJS /NC /NS /NP /MT:8 > /dev/null 2>&1
    ROBO_EXIT=$?
    
    if [ $ROBO_EXIT -lt 8 ]; then
        SUCCESS=$((SUCCESS + 1))
        if [ $((SUCCESS % 10)) -eq 0 ]; then
            echo "  ✅ [$SUCCESS/$TOTAL] Copied"
        fi
    else
        FAILED=$((FAILED + 1))
        echo "  ❌ [$TOTAL] Failed: $(basename "$src_win")"
    fi
    
done < "$REORG_PLAN"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  REPORTE FINAL"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 RESUMEN:"
echo "   Total archivos: $TOTAL"
echo "   ✅ Copiados: $SUCCESS"
echo "   ❌ Fallidos: $FAILED"
echo "   ⏱️  Tiempo: $ELAPSED segundos"
if [ $ELAPSED -gt 0 ]; then
    SPEED=$(echo "scale=2; $SUCCESS / $ELAPSED" | bc 2>/dev/null || echo "$((SUCCESS / ELAPSED))")
    echo "   🚀 Velocidad: $SPEED archivos/segundo"
fi
echo ""
echo "✅ Completado."
