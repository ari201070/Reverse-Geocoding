#!/bin/bash
# Fase 5.1: Copia con robocopy nativo - Chipre
# REGLAS: Solo copiar, nunca mover

set -e

REORG_PLAN="./reorganization_plan.csv"
EXEC_LOG="./execution_log.csv"
TARGET_TRIP="cyprus"

echo "═══════════════════════════════════════════════════════════════"
echo "  FASE 5.1: COPIA CON ROBOCOPY - CHIPRE"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Initialize log
echo "original_path,target_path,status,file_size_bytes" > "$EXEC_LOG"

START_TIME=$(date +%s)

# Read plan and filter Cyprus
TOTAL=0
SUCCESS=0
FAILED=0
TOTAL_BYTES=0

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
    
    # Get source directory and filename
    src_dir_win=$(dirname "$src_win")
    src_file=$(basename "$src_win")
    
    # Convert to Git Bash paths
    src_dir=$(echo "$src_dir_win" | sed 's/^F:/\/f/' | sed 's/\\/\//g')
    dst_dir_win=$(dirname "$dst_win")
    dst_dir=$(echo "$dst_dir_win" | sed 's/^F:/\/f/' | sed 's/\\/\//g')
    
    # Create target directory
    mkdir -p "$dst_dir" 2>/dev/null || true
    
    # Get file size before copy
    if [ -f "$src_dir/$src_file" ]; then
        FILE_SIZE=$(stat -c%s "$src_dir/$src_file" 2>/dev/null || stat -f%z "$src_dir/$src_file" 2>/dev/null || echo 0)
    else
        FILE_SIZE=0
    fi
    
    # Use robocopy for fast copy (native Windows)
    # /NJH /NJS = No job header/summary
    # /NC /NS /NP = No classes/sizes/progress
    # /MT:8 = Multi-threaded with 8 threads
    # robocopy exit codes: 0=no change, 1=copied, 2=extra, 3=copied+extra, etc.
    ROBO_RESULT=$(robocopy "$src_dir_win" "$dst_dir_win" "$src_file" /NJH /NJS /NC /NS /NP /MT:8 2>&1)
    ROBO_EXIT=$?
    
    # Check if file was copied (exit codes 1, 2, 3, 5, 6, 7 = success)
    if [ $ROBO_EXIT -lt 8 ]; then
        echo "\"$src_win\",\"$dst_win\",\"SUCCESS\",$FILE_SIZE" >> "$EXEC_LOG"
        SUCCESS=$((SUCCESS + 1))
        TOTAL_BYTES=$((TOTAL_BYTES + FILE_SIZE))
        
        if [ $((SUCCESS % 10)) -eq 0 ]; then
            echo "  ✅ [$SUCCESS/$TOTAL] Copied"
        fi
    else
        echo "\"$src_win\",\"$dst_win\",\"ERROR\",0" >> "$EXEC_LOG"
        FAILED=$((FAILED + 1))
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
echo "   📦 Tamaño total: $((TOTAL_BYTES / 1024 / 1024)) MB"
echo "   ⏱️  Tiempo: $ELAPSED segundos"
if [ $ELAPSED -gt 0 ]; then
    SPEED=$(echo "scale=2; $TOTAL / $ELAPSED" | bc 2>/dev/null || echo "$((TOTAL / ELAPSED))")
    echo "   🚀 Velocidad: $SPEED archivos/segundo"
fi
echo ""
echo "📄 Log: execution_log.csv"
echo ""
echo "✅ Completado."
