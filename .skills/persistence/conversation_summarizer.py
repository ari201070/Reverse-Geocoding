#!/usr/bin/env python3
"""
Conversation Summarizer for OpenCode
- Lee el historial de la sesión actual
- Genera resumen incremental cada N mensajes
- Guarda en archivo para inyectar al cambiar modelo
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
SUMMARY_DIR = Path(__file__).parent / ".conversation_summaries"
SUMMARY_DIR.mkdir(exist_ok=True)

def get_current_session() -> str:
    """Obtiene la sesión más reciente del proyecto actual"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM session
        WHERE directory LIKE '%Reverse-Geocoding%'
        ORDER BY time_updated DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_messages(session_id: str, limit: int = 100) -> List[Dict]:
    """Obtiene mensajes de una sesión (desde tabla part)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data, time_created FROM part
        WHERE session_id = ? AND json_extract(data, '$.type') = 'text'
        ORDER BY time_created ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for data_json, timestamp in rows:
        data = json.loads(data_json)
        text = data.get("text", "")
        if text.strip():
            # Determinar role por alternancia o heurística
            role = "user" if len(messages) % 2 == 0 else "assistant"
            messages.append({
                "role": role,
                "content": text,
                "timestamp": timestamp
            })
    return messages[-limit:]

def generate_summary(messages: List[Dict], model: str = "ollama/qwen2.5-coder:7b") -> str:
    """Genera resumen extrayendo puntos clave programáticamente (sin llamar a Ollama)"""
    
    # Palabras clave técnicas para detectar temas
    tech_keywords = [
        'optimiz', 'proceso', 'servicio', 'memoria', 'ram', 'cpu',
        'ollama', 'modelo', 'config', 'docker', 'git', 'deploy',
        'adb', 'android', 'reverse', 'geocod', 'api', 'database',
        'sql', 'migration', 'service', 'deshabilit', 'desinstal'
    ]
    
    # Filtrar mensajes con contenido técnico relevante
    relevant = []
    for m in messages[-20:]:  # últimos 20
        content_lower = m['content'].lower()
        if any(kw in content_lower for kw in tech_keywords):
            relevant.append(m)
    
    # Extraer acciones (líneas que empiezan con verbos de acción)
    actions = []
    files = []
    for m in relevant:
        lines = m['content'].split('\n')
        for line in lines:
            line = line.strip()
            if any(line.lower().startswith(v) for v in ['ejecut', 'instal', 'desinstal', 'deshabilit', 'configur', 'crear', 'modif', 'actualiz', 'reinici', 'matar', 'kill', 'stop', 'start', 'sc.exe', 'msiexec', 'winget']):
                actions.append(line[:150])
            # Detectar rutas de archivos
            if 'C:\\' in line or '/home' in line or '.py' in line or '.js' in line or '.json' in line or '.md' in line:
                files.append(line[:150])
    
    # Construir resumen estructurado
    summary_parts = []
    
    if actions:
        summary_parts.append("**Acciones ejecutadas:**")
        for a in actions[-10:]:
            summary_parts.append(f"- {a}")
    
    if files:
        summary_parts.append("\n**Archivos/rutas mencionados:**")
        for f in list(set(files))[-5:]:
            summary_parts.append(f"- {f}")
    
    # Temas detectados
    topics = set()
    for m in relevant:
        for kw in tech_keywords:
            if kw in m['content'].lower():
                topics.add(kw)
    if topics:
        summary_parts.append(f"\n**Temas técnicos:** {', '.join(sorted(topics))}")
    
    # Último intercambio
    last_user = next((m for m in reversed(messages) if m['role'] == 'user'), None)
    last_assistant = next((m for m in reversed(messages) if m['role'] == 'assistant'), None)
    if last_user:
        summary_parts.append(f"\n**Última pregunta usuario:** {last_user['content'][:200]}")
    if last_assistant:
        summary_parts.append(f"**Última respuesta:** {last_assistant['content'][:200]}")
    
    return "\n".join(summary_parts) if summary_parts else "[Sin contenido técnico relevante]"

def save_summary(session_id: str, summary: str, msg_count: int):
    """Guarda resumen con timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = SUMMARY_DIR / f"summary_{session_id[:8]}_{timestamp}_{msg_count}msg.md"
    
    content = f"""# Resumen de Conversación - {timestamp}
**Sesión:** {session_id}
**Mensajes cubiertos:** {msg_count}
**Generado:** {datetime.now().isoformat()}

---

{summary}

---
*Úsalo al cambiar modelo: `opencode --model <modelo> \"Contexto previo: {summary}\"`*
"""
    filename.write_text(content, encoding="utf-8")
    print(f"[OK] Resumen guardado: {filename}")
    return filename

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Resumidor de conversaciones OpenCode")
    parser.add_argument("--every", type=int, default=10, help="Resumir cada N mensajes nuevos")
    parser.add_argument("--model", default="ollama/qwen2.5-coder:7b", help="Modelo para resumir")
    parser.add_argument("--once", action="store_true", help="Ejecutar una vez y salir")
    args = parser.parse_args()
    
    session_id = get_current_session()
    if not session_id:
        print("[ERROR] No se encontro sesion activa para Reverse-Geocoding")
        return
    
    print(f"[INFO] Sesion: {session_id}")
    
    if args.once:
        messages = get_messages(session_id)
        if len(messages) < 3:
            print("[SKIP] Pocos mensajes para resumir")
            return
        summary = generate_summary(messages, args.model)
        save_summary(session_id, summary, len(messages))
    else:
        # Modo daemon - verificar periódicamente
        import time
        last_count = 0
        print(f"[DAEMON] Resumiendo cada {args.every} mensajes nuevos (Ctrl+C para parar)")
        try:
            while True:
                messages = get_messages(session_id)
                new_count = len(messages) - last_count
                if new_count >= args.every:
                    summary = generate_summary(messages, args.model)
                    save_summary(session_id, summary, len(messages))
                    last_count = len(messages)
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n[BYE] Detenido")

if __name__ == "__main__":
    main()
