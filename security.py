# ============================================================
# NOMBRE_ARCHIVO: /utils/security.py
# ============================================================
# ============================================================
# security.py – VALIDACIONES DE SEGURIDAD
# LUMO ENGINE v0.9 – CONGELADO
# ============================================================

import re
from typing import Dict, Any

def validar_input(texto: str) -> bool:
    """Valida que el input no contenga caracteres peligrosos."""
    if not texto:
        return False
    patrones_peligrosos = [r'<script', r'javascript:', r'data:', r'on\w+=']
    for patron in patrones_peligrosos:
        if re.search(patron, texto, re.IGNORECASE):
            return False
    return True

def sanitizar_input(texto: str) -> str:
    """Limpia el input de caracteres potencialmente peligrosos."""
    return re.sub(r'[<>{}]', '', texto)

def validar_estructura_state(state: Dict[str, Any]) -> bool:
    """Valida que el estado tenga las llaves mínimas."""
    llaves_requeridas = ["estado", "nombre", "grado_num", "xp", "aciertos_tema", "error_count"]
    for llave in llaves_requeridas:
        if llave not in state:
            return False
    return True

