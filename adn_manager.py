# ============================================================
# NOMBRE_ARCHIVO: /core/adn_manager.py
# ============================================================
# ============================================================
# adn_manager.py – PERSISTENCIA Y HMAC
# LUMO ENGINE v0.9 – CONGELADO
# ============================================================

import json
import hashlib
import hmac
import os
from typing import Dict, Any, Optional, List

# ============================================================
# CONFIGURACIÓN DE SEGURIDAD (HMAC)
# ============================================================

SECRET_KEY = b"LUMO_PILOT_SECRET_KEY_2026"

def firmar_adn(data: Dict) -> str:
    data_sin_firma = {k: v for k, v in data.items() if k != 'sig'}
    json_str = json.dumps(data_sin_firma, sort_keys=True, ensure_ascii=False)
    return hmac.new(SECRET_KEY, json_str.encode(), hashlib.sha256).hexdigest()

def verificar_firma_adn(data: Dict) -> bool:
    if 'sig' not in data:
        return False
    firma_esperada = firmar_adn(data)
    return data['sig'] == firma_esperada

def generar_adn_seguro(data: Dict) -> Dict:
    data['sig'] = firmar_adn(data)
    return data

# ============================================================
# CONFIGURACIÓN DE PERSISTENCIA (LOCAL)
# ============================================================

SESSIONS_DIR = "./sessions/"
os.makedirs(SESSIONS_DIR, exist_ok=True)

def guardar_sesion(session_id: str, data: Dict) -> bool:
    try:
        filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo guardar sesión {session_id}: {e}")
        return False

def cargar_sesion(session_id: str) -> Optional[Dict]:
    try:
        filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar sesión {session_id}: {e}")
        return None

def listar_sesiones() -> List[str]:
    try:
        files = os.listdir(SESSIONS_DIR)
        return [f.replace('.json', '') for f in files if f.endswith('.json')]
    except:
        return []

