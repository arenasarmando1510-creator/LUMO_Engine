# ============================================================
# NOMBRE_ARCHIVO: /core/session_manager.py
# ============================================================
# ============================================================
# session_manager.py – GESTIÓN DE SESIÓN
# LUMO ENGINE v0.9.3 – CORREGIDO (Ciclo circular)
# ============================================================

import copy
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from core.fsm import STATE_TABLE, initialize_state, state_guard, inicializar_semilla, GATEKEEPER, UI_MAP
from core.adn_manager import guardar_sesion, cargar_sesion, listar_sesiones
# from core.orchestrator import EJECUTAR  # <--- ELIMINADO (importación local dentro de process_input)
from utils.logger import log_fsm_transition, log_user_action, log_error

# ============================================================
# PROCESAR MISIÓN CON TCC
# ============================================================
def procesar_mision_con_tcc(input_usuario, state, memory, onboarding_queue):
    from core.acc_controller import TCC_MOTOR
    if input_usuario not in ["A", "B", "C", "D"]:
        return state, memory, onboarding_queue, "Elige A, B, C o D.\n🔊 ⋮ y bocinita", False
    
    if input_usuario == "C":
        return state, memory, onboarding_queue, UI_MAP["ESPERA_MISION_C_TAREAS"], False
    
    state["mision"] = input_usuario
    
    tcc = TCC_MOTOR()
    config_tcc = tcc.activar(state, memory)
    state["tcc_config"] = config_tcc
    
    for paso in onboarding_queue:
        if paso["id"] == "mision":
            paso["val"] = input_usuario
            break
    
    return state, memory, onboarding_queue, config_tcc["mensaje"], True

# ============================================================
# AVANZAR_ONBOARDING
# ============================================================

def avanzar_onboarding(input_usuario, state, memory, onboarding_queue):
    for paso in onboarding_queue:
        if paso["val"] is None:
            if paso["id"] == "nombre":
                if input_usuario.isdigit() or len(input_usuario) < 2:
                    return state, memory, onboarding_queue, UI_MAP["CAPTURA_NOMBRE_VALIDACION"], False
                state["nombre"] = input_usuario
                memory["nombre"] = input_usuario
                paso["val"] = input_usuario
                return state, memory, onboarding_queue, None, True
            elif paso["id"] == "grado":
                grado_num = int(input_usuario) if input_usuario.isdigit() else 0
                if grado_num == 0:
                    return state, memory, onboarding_queue, UI_MAP["CAPTURA_GRADO_ERROR"], False
                state["grado_num"] = grado_num
                memory["grado_num"] = grado_num
                paso["val"] = input_usuario
                return state, memory, onboarding_queue, None, True
            elif paso["id"] == "fecha_inicio":
                if state["modo"] != "INTENSIVE":
                    paso["val"] = "N/A"
                    continue
                from utils.date_utils import parsear_fecha
                fecha_parseada = parsear_fecha(input_usuario)
                if not fecha_parseada:
                    return state, memory, onboarding_queue, UI_MAP["CAPTURA_FECHAS_ERROR"], False
                state["fecha_inicio_str"] = input_usuario
                paso["val"] = input_usuario
                return state, memory, onboarding_queue, None, True
            elif paso["id"] == "fecha_fin":
                from utils.date_utils import parsear_fecha
                fecha_parseada = parsear_fecha(input_usuario)
                if not fecha_parseada:
                    return state, memory, onboarding_queue, UI_MAP["CAPTURA_FECHAS_ERROR"], False
                state["fecha_fin_str"] = input_usuario
                paso["val"] = input_usuario
                return state, memory, onboarding_queue, None, True
            elif paso["id"] == "personaje":
                if input_usuario not in ["A", "B", "C", "D"]:
                    return state, memory, onboarding_queue, "Elige A, B, C o D.\n🔊 ⋮ y bocinita", False
                state["personaje_elegido"] = input_usuario
                memory["personaje_elegido"] = input_usuario
                paso["val"] = input_usuario
                return state, memory, onboarding_queue, None, True
            elif paso["id"] == "mision":
                state, memory, onboarding_queue, mensaje, exito = procesar_mision_con_tcc(
                    input_usuario, state, memory, onboarding_queue
                )
                if not exito:
                    return state, memory, onboarding_queue, mensaje, False
                if input_usuario == "C":
                    return state, memory, onboarding_queue, mensaje, False
                paso["val"] = input_usuario
                return state, memory, onboarding_queue, None, True
            return state, memory, onboarding_queue, "Error interno: paso desconocido", False
    return state, memory, onboarding_queue, None, "COMPLETO"

# ============================================================
# SESSION MANAGER
# ============================================================

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self._cargar_sesiones_guardadas()
    
    def _cargar_sesiones_guardadas(self):
        session_ids = listar_sesiones()
        for sid in session_ids:
            data = cargar_sesion(sid)
            if data:
                self.sessions[sid] = data
    
    def _generate_session_id(self, nombre: str = "") -> str:
        timestamp = datetime.now().isoformat()
        base = f"{nombre}_{timestamp}"
        return hashlib.md5(base.encode()).hexdigest()[:8]
    
    def create_session(self, nombre: str = "") -> str:
        session_id = self._generate_session_id(nombre)
        inicializar_semilla(session_id)
        self.sessions[session_id] = {
            "state": initialize_state({}),
            "memory": {
                "nombre": nombre,
                "fecha_inicio_str": "",
                "fecha_fin_str": "",
                "personaje_elegido": "",
                "talentos_detectados": [],
                "session_stats": {"aciertos": 0, "errores": 0}
            },
            "onboarding_queue": copy.deepcopy([
                {"id": "nombre", "val": None, "estado": "CAPTURA_NOMBRE"},
                {"id": "grado", "val": None, "estado": "CAPTURA_GRADO"},
                {"id": "fecha_inicio", "val": None, "estado": "CAPTURA_FECHAS"},
                {"id": "fecha_fin", "val": None, "estado": "CAPTURA_FECHAS"},
                {"id": "personaje", "val": None, "estado": "ESPERA_PERSONAJE"},
                {"id": "mision", "val": None, "estado": "ESPERA_MISION"}
            ])
        }
        guardar_sesion(session_id, self.sessions[session_id])
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        if session_id not in self.sessions:
            data = cargar_sesion(session_id)
            if data:
                self.sessions[session_id] = data
                return data
            return None
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, state: dict, memory: dict, onboarding_queue: list) -> None:
        if session_id in self.sessions:
            self.sessions[session_id]["state"] = state
            self.sessions[session_id]["memory"] = memory
            self.sessions[session_id]["onboarding_queue"] = onboarding_queue
            guardar_sesion(session_id, self.sessions[session_id])
    
    def delete_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
            try:
                import os
                os.remove(os.path.join("./sessions/", f"{session_id}.json"))
            except:
                pass
    
    def process_input(self, session_id: str, user_input: str) -> Dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "display_text": "Sesión no encontrada."}
        
        state = session["state"]
        memory = session["memory"]
        onboarding_queue = session["onboarding_queue"]
        
        log_user_action(
            session_id=session_id,
            action="user_input",
            data={"input_preview": user_input[:100] if user_input else "", "input_length": len(user_input) if user_input else 0}
        )
        
        estado_anterior = state.get("estado", "unknown")
        
        try:
            # 🔥 IMPORTACIÓN LOCAL: Rompe el ciclo circular
            from core.orchestrator import EJECUTAR
            
            state, memory, onboarding_queue, resultado_texto = EJECUTAR(
                user_input, state, memory, onboarding_queue
            )
            
            estado_nuevo = state.get("estado", "unknown")
            log_fsm_transition(
                session_id=session_id,
                from_state=estado_anterior,
                to_state=estado_nuevo,
                input_text=user_input,
                trace_id=str(uuid.uuid4())
            )
            
        except Exception as e:
            log_error(
                session_id=session_id,
                error_type="session_manager_error",
                error_message=str(e)
            )
            raise
        
        self.update_session(session_id, state, memory, onboarding_queue)
        
        return {"status": "success", "display_text": resultado_texto}    
    def _cargar_sesiones_guardadas(self):
        session_ids = listar_sesiones()
        for sid in session_ids:
            data = cargar_sesion(sid)
            if data:
                self.sessions[sid] = data
    
    def _generate_session_id(self, nombre: str = "") -> str:
        timestamp = datetime.now().isoformat()
        base = f"{nombre}_{timestamp}"
        return hashlib.md5(base.encode()).hexdigest()[:8]
    
    def create_session(self, nombre: str = "") -> str:
        session_id = self._generate_session_id(nombre)
        inicializar_semilla(session_id)
        self.sessions[session_id] = {
            "state": initialize_state({}),
            "memory": {
                "nombre": nombre,
                "fecha_inicio_str": "",
                "fecha_fin_str": "",
                "personaje_elegido": "",
                "talentos_detectados": [],
                "session_stats": {"aciertos": 0, "errores": 0}
            },
            "onboarding_queue": copy.deepcopy([
                {"id": "nombre", "val": None, "estado": "CAPTURA_NOMBRE"},
                {"id": "grado", "val": None, "estado": "CAPTURA_GRADO"},
                {"id": "fecha_inicio", "val": None, "estado": "CAPTURA_FECHAS"},
                {"id": "fecha_fin", "val": None, "estado": "CAPTURA_FECHAS"},
                {"id": "personaje", "val": None, "estado": "ESPERA_PERSONAJE"},
                {"id": "mision", "val": None, "estado": "ESPERA_MISION"}
            ])
        }
        guardar_sesion(session_id, self.sessions[session_id])
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        if session_id not in self.sessions:
            data = cargar_sesion(session_id)
            if data:
                self.sessions[session_id] = data
                return data
            return None
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, state: dict, memory: dict, onboarding_queue: list) -> None:
        if session_id in self.sessions:
            self.sessions[session_id]["state"] = state
            self.sessions[session_id]["memory"] = memory
            self.sessions[session_id]["onboarding_queue"] = onboarding_queue
            guardar_sesion(session_id, self.sessions[session_id])
    
    def delete_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
            try:
                import os
                os.remove(os.path.join("./sessions/", f"{session_id}.json"))
            except:
                pass
    
    def process_input(self, session_id: str, user_input: str) -> Dict:
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "display_text": "Sesión no encontrada."}
        
        state = session["state"]
        memory = session["memory"]
        onboarding_queue = session["onboarding_queue"]
        
        log_user_action(
            session_id=session_id,
            action="user_input",
            data={"input_preview": user_input[:100] if user_input else "", "input_length": len(user_input) if user_input else 0}
        )
        
        estado_anterior = state.get("estado", "unknown")
        
        try:
            state, memory, onboarding_queue, resultado_texto = EJECUTAR(
                user_input, state, memory, onboarding_queue
            )
            
            estado_nuevo = state.get("estado", "unknown")
            log_fsm_transition(
                session_id=session_id,
                from_state=estado_anterior,
                to_state=estado_nuevo,
                input_text=user_input,
                trace_id=str(uuid.uuid4())
            )
            
        except Exception as e:
            log_error(
                session_id=session_id,
                error_type="session_manager_error",
                error_message=str(e)
            )
            raise
        
        self.update_session(session_id, state, memory, onboarding_queue)
        
        return {"status": "success", "display_text": resultado_texto}

