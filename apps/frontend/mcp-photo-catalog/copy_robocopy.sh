#!/bin/bash
# Fase 5.1: Copia directa con robocopy

REORG_PLAN="./reorganization_plan.csv"
TARGET_TRIP="cyprus"

echo "Starting Cyprus copy with robocopy..."

# Create target directory
mkdir -p "/f/Fotos_Organizadas/Viajes/Chipre/2023-08"

# Extract Cyprus files from CSV and copy with robocopy
grep ",$TARGET_TRIP," "$REORG_PLAN" | while IFS=',' read -r id src dst trip conflict; do
    # Remove quotes
    src=$(echo "$src" | tr -d '"')
    dst=$(echo "$dst" | tr -d '"')
    
    # Convert paths
    src_unix=$(echo "$src" | sed 's/^F:/\/f/' | sed 's/\\/\//g')
    dst_unix=$(echo "$dst" | sed 's/^F:/\/f/' | sed 's/\\/\//g')
    
    src_dir=$(dirname "$src_unix")
    file=$(basename "$src_unix")
    dst_dir=$(dirname "$dst_unix")
    
    # Create dir if needed
    mkdir -p "$dst_dir" 2>/dev/null
    
    # Copy with robocopy
    if [ -f "$src_unix" ]; then
        robocopy "$(dirname "$src")" "$(dirname "$dst")" "$(basename "$src")" /NJH /NJS /NC /NS /NP /MT:8 > /dev/null 2>&1
        echo "Copied: $file"
    else
        echo "Not found: $src_unix"
    fi
done

echo "Done."
