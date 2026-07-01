# ============================================================
# NOMBRE_ARCHIVO: /utils/logger.py
# ============================================================
# ============================================================
# logger.py – SISTEMA DE LOGGING ESTRUCTURADO (JSON)
# ITERACIÓN 6 – OBSERVABILIDAD
# LUMO ENGINE v0.9 – CONGELADO
# ============================================================

import json
from datetime import datetime
from typing import Dict, Any, Optional
import os

LOG_LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
CURRENT_LOG_LEVEL = os.environ.get("LUMO_LOG_LEVEL", "INFO")

def crear_evento_log(session_id: str, level: str, event_type: str, data: Dict[str, Any], trace_id: Optional[str] = None) -> Dict:
    return {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "level": level,
        "event_type": event_type,
        "trace_id": trace_id,
        "data": data
    }

def log_event(session_id: str, level: str, event_type: str, data: Dict[str, Any], trace_id: Optional[str] = None) -> None:
    if LOG_LEVELS.get(level, 999) < LOG_LEVELS.get(CURRENT_LOG_LEVEL, 1):
        return
    evento = crear_evento_log(session_id, level, event_type, data, trace_id)
    print(json.dumps(evento, ensure_ascii=False))

def log_fsm_transition(session_id: str, from_state: str, to_state: str, input_text: str, trace_id: Optional[str] = None) -> None:
    log_event(
        session_id=session_id,
        level="INFO",
        event_type="fsm_transition",
        data={
            "from_state": from_state,
            "to_state": to_state,
            "input_preview": input_text[:100] if input_text else "",
            "input_length": len(input_text) if input_text else 0
        },
        trace_id=trace_id
    )

def log_gemini_request(session_id: str, trace_id: str, prompt_hash: str, latency_ms: float, success: bool, error: Optional[str] = None) -> None:
    log_event(
        session_id=session_id,
        level="INFO" if success else "ERROR",
        event_type="gemini_request",
        data={
            "trace_id": trace_id,
            "prompt_hash": prompt_hash,
            "latency_ms": round(latency_ms, 2),
            "success": success,
            "error": error
        },
        trace_id=trace_id
    )

def log_error(session_id: str, error_type: str, error_message: str, trace_id: Optional[str] = None) -> None:
    log_event(
        session_id=session_id,
        level="ERROR",
        event_type="error",
        data={"error_type": error_type, "error_message": error_message},
        trace_id=trace_id
    )

def log_user_action(session_id: str, action: str, data: Dict[str, Any]) -> None:
    log_event(
        session_id=session_id,
        level="INFO",
        event_type="user_action",
        data={"action": action, **data}
    )

