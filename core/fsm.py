# ============================================================
# fsm.py – MÁQUINA DE ESTADOS (FSM)
# LUMO ENGINE v0.9 – CONGELADO
# ============================================================

import random
import re
import copy
from typing import Dict, Any, Optional, List

# ============================================================
# STATE_TABLE – FSM DECLARATIVA
# ============================================================

STATE_TABLE = {
    "SELECCION_ENTRADA": {"valid": ["A", "B", "C"], "next": {"A": "ONBOARDING", "B": "ESPERA_ADN", "C": "ESPERA_ADN"}},
    "ONBOARDING": {"valid": ["*"], "next": "clase", "action": "avanzar_onboarding"},
    "ESPERA_ADN": {"valid": ["*"], "next": "clase", "action": "restaurar_adn"},
    "clase": {"valid": ["*"], "next": "CIERRE_TEMA", "action": "ejecutar_pedagogia"},
    "CIERRE_TEMA": {"valid": ["A", "B"], "next": {"A": "clase", "B": "clave"}},
    "clave": {"valid": ["*"], "next": "SELECCION_ENTRADA", "action": "reiniciar_sesion"}
}

# ============================================================
# INICIALIZACIÓN DE ESTADO
# ============================================================

def initialize_state(state: dict) -> dict:
    """Inicializa todas las llaves críticas del estado."""
    defaults = {
        "estado": "SELECCION_ENTRADA",
        "modo": "BASIC",
        "nombre": "",
        "grado_num": 0,
        "semana_n": 1,
        "cur_actual": {},
        "error_count": 0,
        "aciertos_tema": 0,
        "talentos_detectados": [],
        "progreso_estudiante": [],
        "xp": 0,
        "fecha_inicio_str": "",
        "fecha_fin_str": "",
        "personaje_elegido": "",
        "cur_context": {},
        "adn_emitido": False,
        "humor_usado_en_tema": False,
        "ultima_respuesta": "",
        "ultima_pregunta_id": "",
        "zoom_usado": False,
        "rescate_usado": False,
        "tema_actual_completado": False,
        "confirmacion_curso": False,
        "side_quests": 0,
        "turnos_totales": 0,
        "ultimo_estado_valido": "SELECCION_ENTRADA",
        "nivel_dominio": "NOVATO",
        "pregunta_actual": None,
        "intentos_pregunta": 0,
        "historial_preguntas": [],
        "mision": None,
        "errores_examen": 0,
        "tcc_config": {}
    }
    for key, value in defaults.items():
        state.setdefault(key, value)
    return state

# ============================================================
# STATEGUARD – WRAPPER DE MUTACIÓN DE ESTADO
# ============================================================

def state_guard(state: dict, action: str, delta: int = 1) -> dict:
    """Única fuente de mutación de estado."""
    if not isinstance(state, dict):
        raise ValueError("StateGuard: state debe ser un diccionario")
    
    nuevo_state = state.copy()
    
    if action == "acierto":
        nuevo_state["aciertos_tema"] = nuevo_state.get("aciertos_tema", 0) + delta
        nuevo_state["xp"] = nuevo_state.get("xp", 0) + (10 * delta)
    elif action == "error":
        nuevo_state["error_count"] = nuevo_state.get("error_count", 0) + delta
    elif action == "reinicio":
        nuevo_state["aciertos_tema"] = 0
        nuevo_state["error_count"] = 0
    elif action == "xp_extra":
        nuevo_state["xp"] = nuevo_state.get("xp", 0) + delta
    else:
        raise ValueError(f"StateGuard: acción desconocida '{action}'")
    
    return nuevo_state

# ============================================================
# DETERMINISMO POR SEMILLA
# ============================================================

def inicializar_semilla(session_id: str) -> None:
    """Inicializa la semilla de random basada en session_id."""
    seed_value = hash(session_id) % (2**32)
    random.seed(seed_value)

# ============================================================
# GATEKEEPER (CON HMAC)
# ============================================================

def GATEKEEPER(INP, state, memory):
    if not INP or INP == "":
        return state, memory, "¡Sistemas iniciados! 🚀\n\n¡Hola, hola! ✨ Soy LUMO, tu guía en AprendIA.\n\nPor favor, escribe aquí tu Llave Mágica (KEY) 🔑\n\n📢 AVISO: Si mi voz se apaga, corazón, pícale a los tres puntitos (⋮) y busca la bocinita 🔊."
    
    if INP[0] == "{" and "coord" in INP:
        try:
            import json
            from core.adn_manager import verificar_firma_adn
            adn = json.loads(INP)
            if not verificar_firma_adn(adn):
                return state, memory, "¡Llave corrupta! Contacta a tu guía. 🔒"
            if "coord" not in adn or "name" not in adn or "mode" not in adn:
                return state, memory, "ADN corrupto: faltan campos obligatorios."
            state["cur_actual"] = adn.get("coord", {})
            state["progreso_estudiante"] = adn.get("progreso_estudiante", [])
            state["talentos_detectados"] = adn.get("talentos_detectados", [])
            state["xp"] = adn.get("xp", 0)
            state["nombre"] = adn.get("name", "")
            state["modo"] = adn.get("mode", "BASIC")
            state["grado_num"] = adn.get("grado", 0)
            state["semana_n"] = adn.get("semana", 1)
            state["aciertos_tema"] = adn.get("aciertos_tema", 0)
            state["error_count"] = adn.get("error_count", 0)
            memory["nombre"] = adn.get("name", "")
            state["estado"] = "clase"
            return state, memory, "✨ ¡Reporte aceptado! 🚀\n\nSesión restaurada con seguridad verificada."
        except json.JSONDecodeError:
            return state, memory, "ADN corrupto: formato inválido."
        except:
            return state, memory, "ADN corrupto."
    
    if not re.match(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$', INP):
        return state, memory, "Llave incorrecta."
    
    g = INP.split("-")
    if g[0][0] == 'B':
        state["modo"] = "BASIC"
    elif g[0][0] == 'I':
        state["modo"] = "INTENSIVE"
    else:
        return state, memory, "Clave inválida (modo)."
    
    state["estado"] = "SELECCION_ENTRADA"
    state["nombre"] = ""
    state["grado_num"] = 0
    state["semana_n"] = 1
    state["progreso_estudiante"] = []
    state["xp"] = 0
    state["talentos_detectados"] = []
    state["side_quests"] = 0
    state["aciertos_tema"] = 0
    state["error_count"] = 0
    
    return state, memory, UI_MAP["SELECCION_ENTRADA"]

# ============================================================
# UI_MAP (DEPURADO)
# ============================================================

UI_MAP = {
    "SELECCION_ENTRADA": "✨ A) 🆕 Soy nuevo\n\n📅 B) 📄 Tengo reporte anterior\n\n🚀 C) ⚡ Continuar donde me quedé\n\n🔊 ⋮ y bocinita",
    "CAPTURA_NOMBRE_BIENVENIDA": "¡Qué alegría que seas nuevo! ✨\n\nPara preparar tu mochila, cuéntame, ¿cómo te llamas?\n\n🔊 *Si mi voz se apaga, pícale a los tres puntitos (⋮) y busca la bocinita.*",
    "CAPTURA_NOMBRE_VALIDACION": "¡Ese nombre es muy corto o es un número! ¿Cómo te llamas en realidad? ✨\n\n🔊 *Recuerda: Si mi voz se apaga, corazón, pícale a los tres puntitos (⋮) y busca la bocinita.*",
    "CAPTURA_GRADO_ERROR": "Escribe el número del grado (1 a 6) o su nombre.\n\n🔊 ⋮ y bocinita",
    "CAPTURA_GRADO_RESPUESTA_A_INTENSIVE": "¡Qué padre! En {grado}° grado vamos a aprender cosas bien divertidas. 🚀\n\n¿Cuál es tu fecha de inicio y la fecha final de tu meta? (Ej: '1 de septiembre de 2025 al 30 de junio de 2026').\n\n🔊 ⋮ y bocinita",
    "CAPTURA_GRADO_RESPUESTA_A_BASIC": "¡Qué padre! En {grado}° grado vamos a aprender cosas bien divertidas. 🚀\n\n¿Cuál es la fecha final de tu meta? (Ej: 30 de junio de 2026).\n\n🔊 ⋮ y bocinita",
    "CAPTURA_FECHAS_ERROR": "No entendí la fecha. Por favor, escríbela en formato 'día mes año'. Ej: 1 sep 2025 al 30 jun 2026\n\n🔊 ⋮ y bocinita",
    "CAPTURA_FECHAS_REINTENTO": "Vamos a intentarlo de nuevo. ¿Cuál es tu fecha de inicio y fecha final? (Ej: '1 sep 2025 al 30 jun 2026')\n\n🔊 ⋮ y bocinita",
    "ESPERA_PERSONAJE": "🎭 ¡Último paso, {nombre}! 🚀 ¿Quién quieres que te acompañe en tu mochila hoy?\n\n👨‍🏫 A) LUMO MAESTRO. Un guía súper paciente, cariñoso y sabio, como tu maestro favorito.\n\n🎮 B) LUMO DIVERTIDO. ¡Puros chistes, juegos y misiones espaciales! Tu compañero de aventuras para aprender riendo.\n\n🧭 C) LUMO EXPLORADOR. Un detective aventurero para resolver misterios del mundo. Tu guía para descubrir el porqué de las cosas.\n\n🎨 D) ¡TU PERSONAJE FAVORITO! Elige a quien tú quieras. Puedo ser Spider-Man, Bob Esponja, Sonic, Bluey o Messi. 🌟\n\n---\n📢 ¡Dímelo fuerte con tu voz o presiona una opción! 🎤\n🔊 Toca los tres puntitos (⋮) y la bocinita si dejas de escucharme.",
    "ESPERA_MISION_INTENSIVE": "🚀 MODO INTENSIVO ACTIVADO\n\n¿Qué meta conquistaremos?\n\n✨ A) Curso Completo. ¡Avance integral por todo tu grado!\n\n📖 B) Materia o Tema. ¡Domina cualquier tema, de cualquier parcial o materia!\n\n✏️ C) Tareas. ¡Pega tu tarea y la convertimos en un reto fácil!\n\n🎯 D) EXAMEN FLEXIBLE. ¡Ponte a prueba con retos de cualquier parcial, tema o materia a tu elección!\n\n🔊 ⋮ y bocinita",
    "ESPERA_MISION_BASIC": "🌟 MODO BASIC\n\n¿Qué misión cumpliremos hoy?\n\n✨ A) Curso Completo. ¡Recorreremos todo el camino de tu grado juntos!\n\n📖 B) Materia o Tema. ¡Elegiremos algo específico!\n\n✏️ C) Tareas. ¡Pega aquí la foto de tu tarea o investigación!\n\n🔊 ⋮ y bocinita",
    "ESPERA_MISION_C_TAREAS": "Próximamente podrás subir tareas. Por ahora elige A, B o D.\n🔊 ⋮ y bocinita",
    "SELECCION_TEMA_EXITO": "✅ Tema seleccionado. Preparando clase...",
    "ESPERA_ADN": "Perfecto. Para continuar, pega aquí tu ADN DEL FREEWAY (el JSON).\n🔊 ⋮ y bocinita",
    "CIERRE_TEMA_MENU": "✨ ¡Lo logramos! 🌟 Terminamos de explorar {tema}.\n👉 ¿Qué quieres hacer ahora, corazón?\n🎮 A) Seguir con otro tema\n💤 B) Descansar y salir",
    "ERROR_SELECCION": "Elige A, B, C o D.\n🔊 ⋮ y bocinita"
}

