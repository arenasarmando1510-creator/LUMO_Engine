# orchestrator.py - LUMO Engine v0.9.3
# Parche de robustez implementado - Arquitectura FSM

import logging
import traceback
from typing import Dict, Any, Tuple
from datetime import datetime

# Configuración de logging
logger = logging.getLogger(__name__)

class PedagogicalOrchestrator:
    """
    Orquestador pedagógico LUMO v0.9.3
    Implementa FSM robusta con manejo de errores avanzado
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = "SELECCION_ENTRADA"
        self.memory = {
            "nivel": None,
            "grado": None,
            "xp": 0,
            "aciertos": 0,
            "errores": 0,
            "talentos": [],
            "ultimo_tema": None
        }
        self.onboarding_queue = []
        self.retry_count = 0
        self.max_retries = 3
        
        # Log de inicio
        self._log_event("orchestrator_init", {
            "session_id": session_id,
            "state": self.state
        })
    
    # ============================================================
    # SECCION I: Logging y Utilidades
    # ============================================================
    
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Registra eventos del orquestador"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
            "state": self.state,
            "data": data
        }
        logger.debug(f"ORCHESTRATOR_LOG: {log_entry}")
        
        # También guardar en memoria para debugging
        if not hasattr(self, 'logs'):
            self.logs = []
        self.logs.append(log_entry)
    
    def _log_error(self, error_type: str, error_message: str, trace: str = None):
        """Registra errores del orquestador"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "error_type": error_type,
            "error_message": error_message,
            "state": self.state,
            "trace": trace
        }
        logger.error(f"ORCHESTRATOR_ERROR: {error_entry}")
        
        if not hasattr(self, 'logs'):
            self.logs = []
        self.logs.append(error_entry)
    
    # ============================================================
    # SECCION II: Gestión de Estado FSM (Robustecida)
    # ============================================================
    
    def _safe_transition(self, new_state: str, force: bool = False) -> bool:
        """
        Transición segura entre estados con validación
        Args:
            new_state: Estado destino
            force: Forzar transición incluso si no está permitida
        Returns:
            bool: Éxito de la transición
        """
        # Estados válidos del sistema
        valid_states = [
            "SELECCION_ENTRADA",
            "ONBOARDING",
            "ESPERA_ADN",
            "APRENDIZAJE",
            "EVALUACION",
            "RETROALIMENTACION",
            "RECUPERACION"
        ]
        
        if new_state not in valid_states:
            self._log_error("invalid_state", f"Estado inválido: {new_state}")
            return False
        
        # Validar transiciones permitidas (FSM segura)
        allowed_transitions = {
            "SELECCION_ENTRADA": ["ONBOARDING", "ESPERA_ADN"],
            "ONBOARDING": ["ESPERA_ADN", "APRENDIZAJE"],
            "ESPERA_ADN": ["APRENDIZAJE", "SELECCION_ENTRADA"],
            "APRENDIZAJE": ["EVALUACION", "RETROALIMENTACION", "RECUPERACION"],
            "EVALUACION": ["RETROALIMENTACION", "APRENDIZAJE"],
            "RETROALIMENTACION": ["APRENDIZAJE", "SELECCION_ENTRADA"],
            "RECUPERACION": ["APRENDIZAJE", "SELECCION_ENTRADA"]
        }
        
        # Verificar transición permitida o forzada
        if force or new_state in allowed_transitions.get(self.state, []):
            old_state = self.state
            self.state = new_state
            self._log_event("state_transition", {
                "from": old_state,
                "to": new_state,
                "forced": force
            })
            return True
        else:
            self._log_error("invalid_transition", 
                f"Transición no permitida: {self.state} -> {new_state}")
            return False
    
    def _handle_unexpected_input(self, user_input: str) -> Tuple[str, str]:
        """
        Maneja entradas inesperadas en SELECCION_ENTRADA
        Args:
            user_input: Entrada del usuario
        Returns:
            Tuple: (respuesta_amigable, estado_siguiente)
        """
        self._log_event("unexpected_input", {
            "input": user_input[:100],
            "state": self.state
        })
        
        # Limpiar entrada
        cleaned = user_input.lower().strip()
        
        # Detectar intención
        if any(palabra in cleaned for palabra in ["hola", "hello", "hi", "buenas"]):
            return (
                "👋 ¡Hola! Para empezar, necesito que selecciones tu nivel educativo. "
                "Usa los botones de arriba para elegir.",
                "ONBOARDING"
            )
        elif any(palabra in cleaned for palabra in ["ayuda", "help", "?"]):
            return (
                "🤔 ¡Claro! Para usar LUMO:\n"
                "1. Selecciona tu nivel (Primaria/Secundaria/Preparatoria)\n"
                "2. Elige tu grado\n"
                "3. ¡Comienza a aprender!\n\n"
                "¿Qué nivel te gustaría explorar?",
                "ONBOARDING"
            )
        else:
            # Forzar onboarding si no reconoce
            return (
                "🌟 ¡Bienvenido a LUMO! Vamos a comenzar con tu configuración. "
                "Por favor, selecciona tu nivel educativo en los botones de arriba.",
                "ONBOARDING"
            )
    
    # ============================================================
    # SECCION III: Procesamiento de Entrada
    # ============================================================
    
    def procesar_entrada(self, user_input: str) -> Tuple[str, Dict, list, str]:
        """
        Punto de entrada principal para procesar mensajes del usuario
        Args:
            user_input: Texto del usuario
        Returns:
            Tuple: (state, memory, onboarding_queue, mensaje)
        """
        self._log_event("processing_input", {
            "input": user_input[:100],
            "state": self.state
        })
        
        # === SELECCION_ENTRADA: Manejo robusto ===
        if self.state == "SELECCION_ENTRADA":
            return self._handle_seleccion_entrada(user_input)
        
        # === ONBOARDING: Configuración inicial ===
        elif self.state == "ONBOARDING":
            return self._handle_onboarding(user_input)
        
        # === ESPERA_ADN: Adaptación inicial ===
        elif self.state == "ESPERA_ADN":
            return self._handle_espera_adn(user_input)
        
        # === APRENDIZAJE: Modo principal ===
        elif self.state == "APRENDIZAJE":
            return self._handle_aprendizaje(user_input)
        
        # === EVALUACION ===
        elif self.state == "EVALUACION":
            return self._handle_evaluacion(user_input)
        
        # === RETROALIMENTACION ===
        elif self.state == "RETROALIMENTACION":
            return self._handle_retroalimentacion(user_input)
        
        # === RECUPERACION ===
        elif self.state == "RECUPERACION":
            return self._handle_recuperacion(user_input)
        
        # Estado desconocido: reset seguro
        else:
            self._log_error("unknown_state", f"Estado desconocido: {self.state}")
            self._safe_transition("SELECCION_ENTRADA", force=True)
            return (
                self.state,
                self.memory,
                self.onboarding_queue,
                "🔄 Reiniciando experiencia... Selecciona tu nivel para comenzar."
            )
    
    # ============================================================
    # SECCION IV: Generación de Contenido (Robustecida)
    # ============================================================
    
    def _generar_contenido_pedagogico_seguro(self, user_input: str) -> str:
        """
        Wrapper seguro para generar contenido pedagógico
        Args:
            user_input: Entrada del usuario
        Returns:
            str: Mensaje de respuesta o recuperación
        """
        try:
            # Importación local para evitar dependencias circulares
            try:
                from logic.pedagogical_engine import PedagogicalEngine
            except ImportError:
                # Fallback si no existe el módulo
                self._log_error("import_error", "No se pudo importar PedagogicalEngine")
                return "🧠 Estoy aprendiendo a procesar eso. ¿Podrías intentarlo de nuevo?"
            
            # Inicializar motor pedagógico
            engine = PedagogicalEngine(
                nivel=self.memory.get("nivel", "primaria"),
                grado=self.memory.get("grado", "1"),
                session_id=self.session_id
            )
            
            # Generar contenido con timeout implícito
            contenido = engine.generar_contenido(user_input, self.memory)
            
            self._log_event("content_generated", {
                "length": len(contenido) if contenido else 0,
                "state": self.state
            })
            
            return contenido
            
        except Exception as e:
            # Capturar cualquier error y loguearlo
            error_msg = str(e)
            trace = traceback.format_exc()
            
            self._log_error("pedagogical_api_error", error_msg, trace)
            
            # Incrementar contador de reintentos
            self.retry_count += 1
            
            # Mensaje amigable según el contexto
            if self.retry_count >= self.max_retries:
                return (
                    "😅 ¡Vaya! He tenido varios tropiezos con este tema. "
                    "¿Te parece si cambiamos de tema o repasamos otro concepto? "
                    "Puedes preguntarme sobre matemáticas, español o ciencias."
                )
            else:
                return (
                    "😊 ¡Ups! He tenido un pequeño tropiezo pedagógico. "
                    "¿Podrías repetirme eso de otra manera? "
                    "A veces me ayuda cuando lo explicas con ejemplos. "
                    f"(Intento {self.retry_count} de {self.max_retries})"
                )
    
    # ============================================================
    # SECCION V: Manejadores de Estado (Implementación)
    # ============================================================
    
    def _handle_seleccion_entrada(self, user_input: str) -> Tuple[str, Dict, list, str]:
        """
        Manejador para SELECCION_ENTRADA con robustez
        """
        # Intentar parsear entrada como selección
        entrada_limpia = user_input.lower().strip()
        
        # Mapeo de palabras clave
        nivel_map = {
            "primaria": "primaria",
            "secundaria": "secundaria", 
            "preparatoria": "preparatoria",
            "bachillerato": "preparatoria",
            "1": "primaria",
            "2": "secundaria",
            "3": "preparatoria"
        }
        
        # Detectar nivel
        nivel_detectado = None
        for key, value in nivel_map.items():
            if key in entrada_limpia:
                nivel_detectado = value
                break
        
        if nivel_detectado:
            # Guardar selección
            self.memory["nivel"] = nivel_detectado
            self._log_event("nivel_seleccionado", {"nivel": nivel_detectado})
            
            # Transición segura a ONBOARDING
            if self._safe_transition("ONBOARDING"):
                return (
                    self.state,
                    self.memory,
                    self.onboarding_queue,
                    f"✅ ¡Excelente! Has seleccionado **{nivel_detectado.title()}**. "
                    f"Ahora, ¿podrías decirme tu grado? "
                    f"(Ej: 1° para Primaria, 1° para Secundaria o Preparatoria)"
                )
        
        # Manejar entrada inesperada
        respuesta, nuevo_estado = self._handle_unexpected_input(user_input)
        
        # Transición segura
        if self._safe_transition(nuevo_estado, force=True):
            return (
                self.state,
                self.memory,
                self.onboarding_queue,
                respuesta
            )
        
        # Fallback seguro
        return (
            self.state,
            self.memory,
            self.onboarding_queue,
            "🌟 ¡Hola! Por favor, selecciona tu nivel usando los botones o escribe el nombre del nivel que te interesa."
        )
    
    def _handle_onboarding(self, user_input: str) -> Tuple[str, Dict, list, str]:
        """Manejador para ONBOARDING"""
        entrada_limpia = user_input.lower().strip()
        
        # Detecta grado
        grados = {
            "1": "1°", "primero": "1°", "1er": "1°",
            "2": "2°", "segundo": "2°", "2do": "2°",
            "3": "3°", "tercero": "3°", "3er": "3°",
            "4": "4°", "cuarto": "4°", "4to": "4°",
            "5": "5°", "quinto": "5°", "5to": "5°",
            "6": "6°", "sexto": "6°", "6to": "6°"
        }
        
        grado_detectado = None
        for key, value in grados.items():
            if key in entrada_limpia:
                grado_detectado = value
                break
        
        if grado_detectado:
            self.memory["grado"] = grado_detectado
            self._log_event("grado_seleccionado", {"grado": grado_detectado})
            
            # Transición a ESPERA_ADN o APRENDIZAJE
            if self._safe_transition("APRENDIZAJE"):
                return (
                    self.state,
                    self.memory,
                    self.onboarding_queue,
                    f"🎉 ¡Perfecto! Grado {grado_detectado} configurado. "
                    f"Estoy listo para aprender contigo. ¿Qué te gustaría explorar hoy?"
                )
        
        # Manejo de entrada inesperada
        return (
            self.state,
            self.memory,
            self.onboarding_queue,
            "📚 Para continuar, necesito saber tu grado. "
            "Por ejemplo: '1°', '2°', '3°' o escribe el número (1, 2, 3...)."
        )
    
    def _handle_espera_adn(self, user_input: str) -> Tuple[str, Dict, list, str]:
        """Manejador para ESPERA_ADN"""
        # Transición directa a aprendizaje
        if self._safe_transition("APRENDIZAJE", force=True):
            return (
                self.state,
                self.memory,
                self.onboarding_queue,
                "🧠 ¡ADN configurado! Comencemos con tu aprendizaje personalizado."
            )
        return (
            self.state,
            self.memory,
            self.onboarding_queue,
            "🤔 Parece que hubo un problema. Reiniciando proceso de aprendizaje..."
        )
    
    def _handle_aprendizaje(self, user_input: str) -> Tuple[str, Dict, list, str]:
        """Manejador para APRENDIZAJE - USO DE SECCION_IV"""
        # Validar entrada
        if not user_input or len(user_input.strip()) < 2:
            return (
                self.state,
                self.memory,
                self.onboarding_queue,
                "🤔 ¿Podrías darme más detalles? Me encantaría ayudarte mejor."
            )
        
        # Incrementar contador de mensajes
        self.memory["mensajes_procesados"] = self.memory.get("mensajes_procesados", 0) + 1
        
        # === LLAMADA SEGURA A SECCION_IV ===
        # Log antes de la intervención
        self._log_event("pre_content_generation", {
            "state": self.state,
            "input_length": len(user_input),
            "retry_count": self.retry_count
        })
        
        # Generar contenido con el wrapper seguro
        respuesta = self._generar_contenido_pedagogico_seguro(user_input)
        
        # Log después de la intervención
        self._log_event("post_content_generation", {
            "state": self.state,
            "response_length": len(respuesta) if respuesta else 0,
            "retry_count": self.retry_count
        })
        
        # Resetear contador de reintentos si fue exitoso
        if "tropiezo" not in respuesta.lower() and "error" not in respuesta.lower():
            self.retry_count = 0
        
        # Verificar si necesita transición
        if any(palabra in respuesta.lower() for palabra in ["evaluar", "examen", "quiz"]):
            if self._safe_transition("EVALUACION"):
                pass
        
        return (
            self.state,
            self.memory,
            self.onboarding_queue,
            respuesta
        )
    
    def _handle_evaluacion(self, user_input: str) -> Tuple[str, Dict, list, str]:
        """Manejador para EVALUACION"""
        # Lógica de evaluación
        return (
            self.state,
            self.memory,
            self.onboarding_queue,
            "📝 ¡Excelente! Vamos a evaluar lo que has aprendido. ¿Listo para el reto?"
        )
    
    def _handle_retroalimentacion(self, user_input: str) -> Tuple[str, Dict, list, str]:
        """Manejador para RETROALIMENTACION"""
        return (
            self.state,
            self.memory,
            self.onboarding_queue,
            "💡 Buen trabajo. Aquí tienes retroalimentación sobre tu progreso..."
        )
    
    def _handle_recuperacion(self, user_input: str) -> Tuple[str, Dict, list, str]:
        """Manejador para RECUPERACION"""
        if self._safe_transition("APRENDIZAJE", force=True):
            return (
                self.state,
                self.memory,
                self.onboarding_queue,
                "🔄 ¡Recuperado! Continuemos con el aprendizaje. ¿Qué te gustaría repasar?"
            )
        return (
            self.state,
            self.memory,
            self.onboarding_queue,
            "🔄 Reiniciando... por favor, selecciona un tema para continuar."
        )
    
    # ============================================================
    # SECCION VI: Estado y Memoria
    # ============================================================
    
    def get_state(self) -> Dict[str, Any]:
        """Retorna el estado completo del orquestador"""
        return {
            "state": self.state,
            "memory": self.memory,
            "onboarding_queue": self.onboarding_queue,
            "retry_count": self.retry_count,
            "session_id": self.session_id
        }
    
    def reset(self) -> None:
        """Reset seguro del orquestador"""
        self.state = "SELECCION_ENTRADA"
        self.memory = {
            "nivel": None,
            "grado": None,
            "xp": 0,
            "aciertos": 0,
            "errores": 0,
            "talentos": [],
            "ultimo_tema": None
        }
        self.onboarding_queue = []
        self.retry_count = 0
        self._log_event("orchestrator_reset", {})
    
    def restore_from_dict(self, data: Dict[str, Any]) -> None:
        """Restaura estado desde diccionario (para persistencia)"""
        if "state" in data:
            self.state = data["state"]
        if "memory" in data:
            self.memory.update(data["memory"])
        if "onboarding_queue" in data:
            self.onboarding_queue = data["onboarding_queue"]
        self._log_event("orchestrator_restored", {"data": data})

# ============================================================
# FUNCION DE ENTRADA PARA INTERFAZ
# ============================================================

def procesar_mensaje(orchestrator: PedagogicalOrchestrator, 
                     user_input: str) -> Tuple[str, Dict, list, str]:
    """
    Función wrapper para procesar mensajes desde la interfaz
    Args:
        orchestrator: Instancia del orquestador
        user_input: Mensaje del usuario
    Returns:
        Tuple: (state, memory, onboarding_queue, mensaje)
    """
    # Log de entrada
    logger.debug(f"procesar_mensaje called: input='{user_input[:50]}'")
    
    # Procesar
    result = orchestrator.procesar_entrada(user_input)
    
    # Log de salida
    logger.debug(f"procesar_mensaje result: state={result[0]}, message='{result[3][:50]}'")
    
    return result                        return state, memory, onboarding_queue, UI_MAP["CAPTURA_FECHAS_REINTENTO"]
                    elif paso["id"] == "personaje":
                        return state, memory, onboarding_queue, UI_MAP["ESPERA_PERSONAJE"].format(nombre=state["nombre"])
                    elif paso["id"] == "mision":
                        if state["modo"] == "INTENSIVE":
                            return state, memory, onboarding_queue, UI_MAP["ESPERA_MISION_INTENSIVE"]
                        else:
                            return state, memory, onboarding_queue, UI_MAP["ESPERA_MISION_BASIC"]
            state["estado"] = "clase"
            tema_inicial = obtener_tema(state["grado_num"], state["semana_n"])
            state["cur_actual"] = {"tema": tema_inicial, "objetivo": f"Aprender sobre {tema_inicial}"}
            acc_config = calcular_acc_mejorado(state["error_count"], state["aciertos_tema"])
            from logic.pedagogical_api import seleccionar_pregunta
            state["pregunta_actual"] = seleccionar_pregunta(tema_inicial, acc_config["dificultad"], state.get("historial_preguntas", []))
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            if state["pregunta_actual"]:
                state["historial_preguntas"].append(state["pregunta_actual"]["id"])
            return state, memory, onboarding_queue, f"✅ Tema seleccionado.\n\n🔢 {state['pregunta_actual']['pregunta']}"
        
        elif mensaje:
            return state, memory, onboarding_queue, mensaje
    
    if estado_actual == "SELECCION_ENTRADA":
        if INPUT == "A":
            state["estado"] = "ONBOARDING"
            return state, memory, onboarding_queue, UI_MAP["CAPTURA_NOMBRE_BIENVENIDA"]
        else:
            state["estado"] = "ESPERA_ADN"
            return state, memory, onboarding_queue, UI_MAP["ESPERA_ADN"]
    
    if estado_actual == "ESPERA_ADN":
        state, memory, mensaje = GATEKEEPER(INPUT, state, memory)
        if state["estado"] == "clase":
            tema = state["cur_actual"].get("tema", obtener_tema(state["grado_num"], state.get("semana_n", 1)))
            acc_config = calcular_acc_mejorado(state["error_count"], state["aciertos_tema"])
            from logic.pedagogical_api import seleccionar_pregunta
            state["pregunta_actual"] = seleccionar_pregunta(tema, acc_config["dificultad"], state.get("historial_preguntas", []))
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            if state["pregunta_actual"]:
                state["historial_preguntas"].append(state["pregunta_actual"]["id"])
            return state, memory, onboarding_queue, f"{mensaje}\n\n🔢 {state['pregunta_actual']['pregunta']}"
        return state, memory, onboarding_queue, mensaje
    
    if estado_actual == "clase":
        state, memory, onboarding_queue, resultado = SECCION_IV(INPUT, state, memory, onboarding_queue)
        return state, memory, onboarding_queue, resultado
    
    return state, memory, onboarding_queue, "Continuando..."

# ============================================================
# SECCION_IV – MOTOR PEDAGÓGICO (CON GEMINI API)
# ============================================================

def SECCION_IV(INPUT, state, memory, onboarding_queue):
    tema = state["cur_actual"].get("tema", "Matemáticas")
    grado = state.get("grado_num", 1)
    personaje = state.get("personaje_elegido", "A")
    nivel_acc = calcular_acc(state.get("error_count", 0), state.get("aciertos_tema", 0))
    nombre = state.get("nombre", "Estudiante")
    historial = state.get("historial_preguntas", [])
    error_count = state.get("error_count", 0)
    aciertos_tema = state.get("aciertos_tema", 0)
    
    mapa_persona = {"A": "MAESTRO", "B": "DIVERTIDO", "C": "EXPLORADOR", "D": "PERSONALIZADO"}
    persona = mapa_persona.get(personaje, "MAESTRO")
    
    if state.get("gancho_usado", False) == False:
        goal = "explain_new_concept"
    elif error_count >= 3:
        goal = "reinforce_topic"
    elif aciertos_tema >= 3:
        goal = "evaluate_progress"
    else:
        goal = "reinforce_topic"
    
    contenido = generar_contenido_pedagogico(
        nombre=nombre,
        grado=grado,
        historia=historial,
        tema=tema,
        campo_formativo="Saberes y Pensamiento Científico",
        acc_level=nivel_acc,
        error_count=error_count,
        success_streak=aciertos_tema,
        persona=persona,
        goal=goal
    )
    
    state["pregunta_actual"] = {
        "pregunta": contenido.get("pregunta", ""),
        "respuesta": contenido.get("respuesta_esperada", ""),
        "tipo": "basica",
        "dificultad": 1,
        "pista": contenido.get("pista", "")
    }
    state["ultima_pregunta_id"] = contenido.get("pregunta", "unknown")
    
    mensaje = f"""
{contenido.get('visual_hook', '')}

📖 **{tema}**

{contenido.get('explicacion', '')}

💡 **Ejemplo:** {contenido.get('ejemplo', '')}

{contenido.get('emocion', '')}

🎯 **Ahora, tu turno:**

🔢 {contenido.get('pregunta', '')}
"""
    
    state["gancho_usado"] = True
    return state, memory, onboarding_queue, mensaje

# ============================================================
# SECCION_V – EXÁMENES
# ============================================================

def SECCION_V(INPUT, state, memory):
    nivel_acc = calcular_acc(state.get("error_count", 0), state.get("aciertos_tema", 0))
    dificultad = 1 if nivel_acc in ["ACC_1", "ACC_2"] else 2 if nivel_acc == "ACC_3" else 3
    
    if state.get("aciertos_tema", 0) == 0 and not state.get("tema_actual_completado", False):
        return state, memory, "😊 Primero repasemos juntos y después te evalúo."
    
    if state.get("errores_examen", 0) >= 2:
        return state, memory, "💛 Veo que esto se está poniendo difícil. ¿Quieres que hagamos una pausa y lo veamos juntos?\n\n🎮 A) Sí, ayúdame\n📝 B) Quiero seguir intentando"
    
    if INPUT == "A" and state["estado"] == "examen":
        state["estado"] = "clase"
        state = state_guard(state, "reinicio")
        return state, memory, "🌟 ¡Excelente decisión! Vamos a repasar juntos. No importa el examen, importa que aprendas."
    
    tema = state["cur_actual"].get("tema", obtener_tema(state["grado_num"], state.get("semana_n", 1)))
    
    if state.get("modo") == "BASIC":
        if state.get("pregunta_actual") is None:
            from logic.pedagogical_api import seleccionar_pregunta
            pregunta = seleccionar_pregunta(tema, dificultad, state.get("historial_preguntas", []))
            state["pregunta_actual"] = pregunta
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            state["historial_preguntas"].append(pregunta["id"])
            state["errores_examen"] = 0
        return state, memory, f"📝 EXAMEN BASIC:\n\n🔢 {state['pregunta_actual']['pregunta']}"
    
    elif state.get("modo") == "INTENSIVE":
        return state, memory, f"📝 EXAMEN INTENSIVE: 3 preguntas adaptadas a tu nivel."
    
    return state, memory, f"✨ RESULTADO: {state.get('aciertos_tema', 0)} aciertos\n📚 Tema: {state['cur_actual'].get('tema', 'N/A')}\n💡 Recomendación: ¡Sigue practicando! 💛"

# ============================================================
# SECCION_VI – ADN CON HMAC Y TALENTOS
# ============================================================

def SECCION_VI(state, memory):
    import json
    from core.adn_manager import generar_adn_seguro
    
    if state["cur_actual"] is None or state["cur_actual"].get("tema") in [None, ""]:
        return "⚠️ No hay tema activo para generar reporte."
    
    nombre = state.get("nombre", "Estudiante")
    xp = state.get("xp", 0)
    modo = state.get("modo", "BASIC")
    
    total_aciertos = state.get("aciertos_tema", 0)
    total_errores = state.get("error_count", 0)
    
    talento_texto = ""
    if state.get("talentos_detectados"):
        talento_texto = f"🌟 ¡Y algo increíble! Descubrimos que tienes talento para: {', '.join(state['talentos_detectados'])}. 💛"
    else:
        talento_texto = "🌟 Cada día descubres algo nuevo. ¡Sigue así!"
    
    mensaje_cierre = ""
    if total_aciertos > 0:
        mensaje_cierre += "Hoy aprendiste algo nuevo. 🌟 "
    if total_errores > 0 and total_aciertos > 0:
        mensaje_cierre += "No te rendiste, y eso es lo más importante. 💪 "
    if state.get("zoom_usado", False) or state.get("rescate_usado", False):
        mensaje_cierre += "Me encanta que pidieras ayuda. Eso es muy valiente. "
    mensaje_cierre += f"\n{talento_texto}\n"
    mensaje_cierre += "¿Vienes mañana? Te voy a estar esperando. 🧸"
    
    tcc_config = state.get("tcc_config", {})
    
    adn = {
        "name": nombre,
        "grado": state.get("grado_num", 0),
        "tema": state["cur_actual"].get("tema", ""),
        "progreso_estudiante": state.get("progreso_estudiante", []),
        "xp": xp,
        "mode": modo,
        "fecha_inicio": state.get("fecha_inicio_str", ""),
        "fecha_fin": state.get("fecha_fin_str", ""),
        "personaje": state.get("personaje_elegido", ""),
        "semana": state.get("semana_n", 1),
        "talentos_detectados": state.get("talentos_detectados", []),
        "mensaje_cierre": mensaje_cierre,
        "coord": state.get("cur_actual", {}),
        "aciertos_tema": state.get("aciertos_tema", 0),
        "error_count": state.get("error_count", 0),
        "zoom_usado": state.get("zoom_usado", False),
        "rescate_usado": state.get("rescate_usado", False),
        "nivel_dominio": state.get("nivel_dominio", "NOVATO"),
        "pregunta_actual": state.get("pregunta_actual", None),
        "tcc_config": {
            "activo": tcc_config.get("activo", False),
            "tipo": tcc_config.get("tipo"),
            "dias_totales": tcc_config.get("dias_totales", 0),
            "tasa_compresion": tcc_config.get("tasa_compresion", 1.0),
            "semanas_sep": tcc_config.get("semanas_sep", 0)
        }
    }
    
    adn_firmado = generar_adn_seguro(adn)
    return json.dumps(adn_firmado, ensure_ascii=False)

# ============================================================
# EJECUTAR (SIN GLOBALES)
# ============================================================

def EJECUTAR(INPUT, state, memory, onboarding_queue):
    state["turnos_totales"] = state.get("turnos_totales", 0) + 1
    state["ultimo_estado_valido"] = state.get("estado", "SELECCION_ENTRADA")
    
    if state["turnos_totales"] % 20 == 0:
        LUMOS_IDENTITY_REFRESH()
    
    if state["estado"] not in STATE_TABLE:
        return state, memory, onboarding_queue, RUTINA_RECUPERACION(state["estado"])
    
    side_quests, desviacion = VERIFICAR_ALINEACION(INPUT, state.get("side_quests", 0), {"tema": state.get("cur_actual", {}).get("tema", "")})
    state["side_quests"] = side_quests
    if desviacion:
        return state, memory, onboarding_queue, desviacion
    
    config = STATE_TABLE[state["estado"]]
    if "valid" in config and config["valid"] != ["*"]:
        if INPUT not in config["valid"]:
            return state, memory, onboarding_queue, UI_MAP["ERROR_SELECCION"]
    
    return SECCION_II(INPUT, state, memory, onboarding_queue)# ============================================================
# NOMBRE_ARCHIVO: /core/orchestrator.py
# ============================================================
# ============================================================
# orchestrator.py – ROUTER Y CONTROL FSM
# LUMO ENGINE v0.9.3– CONGELADO
# ============================================================

from core.fsm import STATE_TABLE, state_guard, UI_MAP, GATEKEEPER
from core.curriculum_engine import obtener_tema
from core.acc_controller import calcular_acc, calcular_acc_mejorado
# from core.session_manager import avanzar_onboarding  # <--- ELIMINADO (importación local dentro de funciones)
from logic.pedagogical_api import generar_contenido_pedagogico
from utils.logger import log_error

# ============================================================
# FUNCIONES DE SOPORTE
# ============================================================

def LUMOS_IDENTITY_REFRESH():
    return "✨ Recuerda: Soy LUMO, tu guía paciente, cariñoso y sabio. Estoy aquí para ayudarte a entender. 💛"

def RUTINA_RECUPERACION(estado_actual):
    return "🔄 ¡Ups! Perdí el hilo por un momento. ¡Aquí estamos de nuevo! ¿Por dónde íbamos? ✨"

def VERIFICAR_ALINEACION(INPUT, side_quests, ANCHOR):
    palabras_clave = ["batman", "spiderman", "desayuno", "comida", "juego", "youtube"]
    for palabra in palabras_clave:
        if palabra in INPUT.lower():
            side_quests += 1
            if side_quests > 3:
                side_quests = 0
                return side_quests, f"¡Qué pregunta tan divertida! 😊 Ahora, volvamos a nuestra misión: {ANCHOR['tema'] if ANCHOR['tema'] else 'aprender'}"
            else:
                return side_quests, None
    return side_quests, None

# ============================================================
# SECCIÓN_II – NAVEGACIÓN
# ============================================================

def SECCION_II(INPUT, state, memory, onboarding_queue):
    estado_actual = state["estado"]
    
    if estado_actual == "CIERRE_TEMA":
        if INPUT == "A":
            state = state_guard(state, "reinicio")
            state["zoom_usado"] = False
            state["rescate_usado"] = False
            state["humor_usado_en_tema"] = False
            state["ultima_respuesta"] = ""
            state["ultima_pregunta_id"] = ""
            state["tema_actual_completado"] = False
            state["pregunta_actual"] = None
            state["intentos_pregunta"] = 0
            
            state["semana_n"] = state.get("semana_n", 1) + 1
            tema_nuevo = obtener_tema(state["grado_num"], state["semana_n"])
            state["cur_actual"] = {"tema": tema_nuevo, "objetivo": f"Aprender sobre {tema_nuevo}"}
            
            acc_config = calcular_acc_mejorado(state["error_count"], state["aciertos_tema"])
            from logic.pedagogical_api import seleccionar_pregunta
            state["pregunta_actual"] = seleccionar_pregunta(tema_nuevo, acc_config["dificultad"], state.get("historial_preguntas", []))
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            state["historial_preguntas"].append(state["pregunta_actual"]["id"])
            
            return state, memory, onboarding_queue, UI_MAP["SELECCION_TEMA_EXITO"]
        elif INPUT == "B":
            state["estado"] = "clave"
            adn_texto = SECCION_VI(state, memory)
            return state, memory, onboarding_queue, f"✨ Sesión guardada. ¡Hasta pronto! 🧸🚀\n\n{adn_texto}"
        else:
            return state, memory, onboarding_queue, UI_MAP["CIERRE_TEMA_MENU"].format(tema=state["cur_actual"].get("tema", "tu tema"))
    
    if estado_actual == "ONBOARDING":
        # 🔥 IMPORTACIÓN LOCAL: Rompe el ciclo circular
        from core.session_manager import avanzar_onboarding
        state, memory, onboarding_queue, mensaje, estado_onboarding = avanzar_onboarding(INPUT, state, memory, onboarding_queue)
        
        if estado_onboarding == "COMPLETO":
            state["estado"] = "clase"
            state["semana_n"] = 1
            tema_inicial = obtener_tema(state["grado_num"], state["semana_n"])
            state["cur_actual"] = {"tema": tema_inicial, "objetivo": f"Aprender sobre {tema_inicial}"}
            
            acc_config = calcular_acc_mejorado(state["error_count"], state["aciertos_tema"])
            from logic.pedagogical_api import seleccionar_pregunta
            state["pregunta_actual"] = seleccionar_pregunta(tema_inicial, acc_config["dificultad"], state.get("historial_preguntas", []))
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            if state["pregunta_actual"]:
                state["historial_preguntas"].append(state["pregunta_actual"]["id"])
            
            return state, memory, onboarding_queue, f"✅ Tema seleccionado. Preparando clase...\n\n🔢 {state['pregunta_actual']['pregunta']}"
        
        elif estado_onboarding == True:
            for paso in onboarding_queue:
                if paso["val"] is None:
                    if paso["id"] == "nombre":
                        return state, memory, onboarding_queue, UI_MAP["CAPTURA_NOMBRE_BIENVENIDA"]
                    elif paso["id"] == "grado":
                        if state["modo"] == "INTENSIVE":
                            return state, memory, onboarding_queue, UI_MAP["CAPTURA_GRADO_RESPUESTA_A_INTENSIVE"].format(grado=state["grado_num"])
                        else:
                            return state, memory, onboarding_queue, UI_MAP["CAPTURA_GRADO_RESPUESTA_A_BASIC"].format(grado=state["grado_num"])
                    elif paso["id"] == "fecha_inicio":
                        if state["modo"] == "INTENSIVE":
                            return state, memory, onboarding_queue, UI_MAP["CAPTURA_FECHAS_ERROR"]
                        else:
                            continue
                    elif paso["id"] == "fecha_fin":
                        return state, memory, onboarding_queue, UI_MAP["CAPTURA_FECHAS_REINTENTO"]
                    elif paso["id"] == "personaje":
                        return state, memory, onboarding_queue, UI_MAP["ESPERA_PERSONAJE"].format(nombre=state["nombre"])
                    elif paso["id"] == "mision":
                        if state["modo"] == "INTENSIVE":
                            return state, memory, onboarding_queue, UI_MAP["ESPERA_MISION_INTENSIVE"]
                        else:
                            return state, memory, onboarding_queue, UI_MAP["ESPERA_MISION_BASIC"]
            state["estado"] = "clase"
            tema_inicial = obtener_tema(state["grado_num"], state["semana_n"])
            state["cur_actual"] = {"tema": tema_inicial, "objetivo": f"Aprender sobre {tema_inicial}"}
            acc_config = calcular_acc_mejorado(state["error_count"], state["aciertos_tema"])
            from logic.pedagogical_api import seleccionar_pregunta
            state["pregunta_actual"] = seleccionar_pregunta(tema_inicial, acc_config["dificultad"], state.get("historial_preguntas", []))
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            if state["pregunta_actual"]:
                state["historial_preguntas"].append(state["pregunta_actual"]["id"])
            return state, memory, onboarding_queue, f"✅ Tema seleccionado.\n\n🔢 {state['pregunta_actual']['pregunta']}"
        
        elif mensaje:
            return state, memory, onboarding_queue, mensaje
    
    if estado_actual == "SELECCION_ENTRADA":
        if INPUT == "A":
            state["estado"] = "ONBOARDING"
            return state, memory, onboarding_queue, UI_MAP["CAPTURA_NOMBRE_BIENVENIDA"]
        else:
            state["estado"] = "ESPERA_ADN"
            return state, memory, onboarding_queue, UI_MAP["ESPERA_ADN"]
    
    if estado_actual == "ESPERA_ADN":
        state, memory, mensaje = GATEKEEPER(INPUT, state, memory)
        if state["estado"] == "clase":
            tema = state["cur_actual"].get("tema", obtener_tema(state["grado_num"], state.get("semana_n", 1)))
            acc_config = calcular_acc_mejorado(state["error_count"], state["aciertos_tema"])
            from logic.pedagogical_api import seleccionar_pregunta
            state["pregunta_actual"] = seleccionar_pregunta(tema, acc_config["dificultad"], state.get("historial_preguntas", []))
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            if state["pregunta_actual"]:
                state["historial_preguntas"].append(state["pregunta_actual"]["id"])
            return state, memory, onboarding_queue, f"{mensaje}\n\n🔢 {state['pregunta_actual']['pregunta']}"
        return state, memory, onboarding_queue, mensaje
    
    if estado_actual == "clase":
        state, memory, onboarding_queue, resultado = SECCION_IV(INPUT, state, memory, onboarding_queue)
        return state, memory, onboarding_queue, resultado
    
    return state, memory, onboarding_queue, "Continuando..."

# ============================================================
# SECCION_IV – MOTOR PEDAGÓGICO (CON GEMINI API)
# ============================================================

def SECCION_IV(INPUT, state, memory, onboarding_queue):
    tema = state["cur_actual"].get("tema", "Matemáticas")
    grado = state.get("grado_num", 1)
    personaje = state.get("personaje_elegido", "A")
    nivel_acc = calcular_acc(state.get("error_count", 0), state.get("aciertos_tema", 0))
    nombre = state.get("nombre", "Estudiante")
    historial = state.get("historial_preguntas", [])
    error_count = state.get("error_count", 0)
    aciertos_tema = state.get("aciertos_tema", 0)
    
    mapa_persona = {"A": "MAESTRO", "B": "DIVERTIDO", "C": "EXPLORADOR", "D": "PERSONALIZADO"}
    persona = mapa_persona.get(personaje, "MAESTRO")
    
    if state.get("gancho_usado", False) == False:
        goal = "explain_new_concept"
    elif error_count >= 3:
        goal = "reinforce_topic"
    elif aciertos_tema >= 3:
        goal = "evaluate_progress"
    else:
        goal = "reinforce_topic"
    
    contenido = generar_contenido_pedagogico(
        nombre=nombre,
        grado=grado,
        historia=historial,
        tema=tema,
        campo_formativo="Saberes y Pensamiento Científico",
        acc_level=nivel_acc,
        error_count=error_count,
        success_streak=aciertos_tema,
        persona=persona,
        goal=goal
    )
    
    state["pregunta_actual"] = {
        "pregunta": contenido.get("pregunta", ""),
        "respuesta": contenido.get("respuesta_esperada", ""),
        "tipo": "basica",
        "dificultad": 1,
        "pista": contenido.get("pista", "")
    }
    state["ultima_pregunta_id"] = contenido.get("pregunta", "unknown")
    
    mensaje = f"""
{contenido.get('visual_hook', '')}

📖 **{tema}**

{contenido.get('explicacion', '')}

💡 **Ejemplo:** {contenido.get('ejemplo', '')}

{contenido.get('emocion', '')}

🎯 **Ahora, tu turno:**

🔢 {contenido.get('pregunta', '')}
"""
    
    state["gancho_usado"] = True
    return state, memory, onboarding_queue, mensaje

# ============================================================
# SECCION_V – EXÁMENES
# ============================================================

def SECCION_V(INPUT, state, memory):
    nivel_acc = calcular_acc(state.get("error_count", 0), state.get("aciertos_tema", 0))
    dificultad = 1 if nivel_acc in ["ACC_1", "ACC_2"] else 2 if nivel_acc == "ACC_3" else 3
    
    if state.get("aciertos_tema", 0) == 0 and not state.get("tema_actual_completado", False):
        return state, memory, "😊 Primero repasemos juntos y después te evalúo."
    
    if state.get("errores_examen", 0) >= 2:
        return state, memory, "💛 Veo que esto se está poniendo difícil. ¿Quieres que hagamos una pausa y lo veamos juntos?\n\n🎮 A) Sí, ayúdame\n📝 B) Quiero seguir intentando"
    
    if INPUT == "A" and state["estado"] == "examen":
        state["estado"] = "clase"
        state = state_guard(state, "reinicio")
        return state, memory, "🌟 ¡Excelente decisión! Vamos a repasar juntos. No importa el examen, importa que aprendas."
    
    tema = state["cur_actual"].get("tema", obtener_tema(state["grado_num"], state.get("semana_n", 1)))
    
    if state.get("modo") == "BASIC":
        if state.get("pregunta_actual") is None:
            from logic.pedagogical_api import seleccionar_pregunta
            pregunta = seleccionar_pregunta(tema, dificultad, state.get("historial_preguntas", []))
            state["pregunta_actual"] = pregunta
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            state["historial_preguntas"].append(pregunta["id"])
            state["errores_examen"] = 0
        return state, memory, f"📝 EXAMEN BASIC:\n\n🔢 {state['pregunta_actual']['pregunta']}"
    
    elif state.get("modo") == "INTENSIVE":
        return state, memory, f"📝 EXAMEN INTENSIVE: 3 preguntas adaptadas a tu nivel."
    
    return state, memory, f"✨ RESULTADO: {state.get('aciertos_tema', 0)} aciertos\n📚 Tema: {state['cur_actual'].get('tema', 'N/A')}\n💡 Recomendación: ¡Sigue practicando! 💛"

# ============================================================
# SECCION_VI – ADN CON HMAC Y TALENTOS
# ============================================================

def SECCION_VI(state, memory):
    import json
    from core.adn_manager import generar_adn_seguro
    
    if state["cur_actual"] is None or state["cur_actual"].get("tema") in [None, ""]:
        return "⚠️ No hay tema activo para generar reporte."
    
    nombre = state.get("nombre", "Estudiante")
    xp = state.get("xp", 0)
    modo = state.get("modo", "BASIC")
    
    total_aciertos = state.get("aciertos_tema", 0)
    total_errores = state.get("error_count", 0)
    
    talento_texto = ""
    if state.get("talentos_detectados"):
        talento_texto = f"🌟 ¡Y algo increíble! Descubrimos que tienes talento para: {', '.join(state['talentos_detectados'])}. 💛"
    else:
        talento_texto = "🌟 Cada día descubres algo nuevo. ¡Sigue así!"
    
    mensaje_cierre = ""
    if total_aciertos > 0:
        mensaje_cierre += "Hoy aprendiste algo nuevo. 🌟 "
    if total_errores > 0 and total_aciertos > 0:
        mensaje_cierre += "No te rendiste, y eso es lo más importante. 💪 "
    if state.get("zoom_usado", False) or state.get("rescate_usado", False):
        mensaje_cierre += "Me encanta que pidieras ayuda. Eso es muy valiente. "
    mensaje_cierre += f"\n{talento_texto}\n"
    mensaje_cierre += "¿Vienes mañana? Te voy a estar esperando. 🧸"
    
    tcc_config = state.get("tcc_config", {})
    
    adn = {
        "name": nombre,
        "grado": state.get("grado_num", 0),
        "tema": state["cur_actual"].get("tema", ""),
        "progreso_estudiante": state.get("progreso_estudiante", []),
        "xp": xp,
        "mode": modo,
        "fecha_inicio": state.get("fecha_inicio_str", ""),
        "fecha_fin": state.get("fecha_fin_str", ""),
        "personaje": state.get("personaje_elegido", ""),
        "semana": state.get("semana_n", 1),
        "talentos_detectados": state.get("talentos_detectados", []),
        "mensaje_cierre": mensaje_cierre,
        "coord": state.get("cur_actual", {}),
        "aciertos_tema": state.get("aciertos_tema", 0),
        "error_count": state.get("error_count", 0),
        "zoom_usado": state.get("zoom_usado", False),
        "rescate_usado": state.get("rescate_usado", False),
        "nivel_dominio": state.get("nivel_dominio", "NOVATO"),
        "pregunta_actual": state.get("pregunta_actual", None),
        "tcc_config": {
            "activo": tcc_config.get("activo", False),
            "tipo": tcc_config.get("tipo"),
            "dias_totales": tcc_config.get("dias_totales", 0),
            "tasa_compresion": tcc_config.get("tasa_compresion", 1.0),
            "semanas_sep": tcc_config.get("semanas_sep", 0)
        }
    }
    
    adn_firmado = generar_adn_seguro(adn)
    return json.dumps(adn_firmado, ensure_ascii=False)

# ============================================================
# EJECUTAR (SIN GLOBALES)
# ============================================================

def EJECUTAR(INPUT, state, memory, onboarding_queue):
    state["turnos_totales"] = state.get("turnos_totales", 0) + 1
    state["ultimo_estado_valido"] = state.get("estado", "SELECCION_ENTRADA")
    
    if state["turnos_totales"] % 20 == 0:
        LUMOS_IDENTITY_REFRESH()
    
    if state["estado"] not in STATE_TABLE:
        return state, memory, onboarding_queue, RUTINA_RECUPERACION(state["estado"])
    
    side_quests, desviacion = VERIFICAR_ALINEACION(INPUT, state.get("side_quests", 0), {"tema": state.get("cur_actual", {}).get("tema", "")})
    state["side_quests"] = side_quests
    if desviacion:
        return state, memory, onboarding_queue, desviacion
    
    config = STATE_TABLE[state["estado"]]
    if "valid" in config and config["valid"] != ["*"]:
        if INPUT not in config["valid"]:
            return state, memory, onboarding_queue, UI_MAP["ERROR_SELECCION"]
    
    return SECCION_II(INPUT, state, memory, onboarding_queue)                        return state, memory, onboarding_queue, UI_MAP["ESPERA_PERSONAJE"].format(nombre=state["nombre"])
                    elif paso["id"] == "mision":
                        if state["modo"] == "INTENSIVE":
                            return state, memory, onboarding_queue, UI_MAP["ESPERA_MISION_INTENSIVE"]
                        else:
                            return state, memory, onboarding_queue, UI_MAP["ESPERA_MISION_BASIC"]
            state["estado"] = "clase"
            tema_inicial = obtener_tema(state["grado_num"], state["semana_n"])
            state["cur_actual"] = {"tema": tema_inicial, "objetivo": f"Aprender sobre {tema_inicial}"}
            acc_config = calcular_acc_mejorado(state["error_count"], state["aciertos_tema"])
            from logic.pedagogical_api import seleccionar_pregunta
            state["pregunta_actual"] = seleccionar_pregunta(tema_inicial, acc_config["dificultad"], state.get("historial_preguntas", []))
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            if state["pregunta_actual"]:
                state["historial_preguntas"].append(state["pregunta_actual"]["id"])
            return state, memory, onboarding_queue, f"✅ Tema seleccionado.\n\n🔢 {state['pregunta_actual']['pregunta']}"
        
        elif mensaje:
            return state, memory, onboarding_queue, mensaje
    
    if estado_actual == "SELECCION_ENTRADA":
        if INPUT == "A":
            state["estado"] = "ONBOARDING"
            return state, memory, onboarding_queue, UI_MAP["CAPTURA_NOMBRE_BIENVENIDA"]
        else:
            state["estado"] = "ESPERA_ADN"
            return state, memory, onboarding_queue, UI_MAP["ESPERA_ADN"]
    
    if estado_actual == "ESPERA_ADN":
        state, memory, mensaje = GATEKEEPER(INPUT, state, memory)
        if state["estado"] == "clase":
            tema = state["cur_actual"].get("tema", obtener_tema(state["grado_num"], state.get("semana_n", 1)))
            acc_config = calcular_acc_mejorado(state["error_count"], state["aciertos_tema"])
            from logic.pedagogical_api import seleccionar_pregunta
            state["pregunta_actual"] = seleccionar_pregunta(tema, acc_config["dificultad"], state.get("historial_preguntas", []))
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            if state["pregunta_actual"]:
                state["historial_preguntas"].append(state["pregunta_actual"]["id"])
            return state, memory, onboarding_queue, f"{mensaje}\n\n🔢 {state['pregunta_actual']['pregunta']}"
        return state, memory, onboarding_queue, mensaje
    
    if estado_actual == "clase":
        state, memory, onboarding_queue, resultado = SECCION_IV(INPUT, state, memory, onboarding_queue)
        return state, memory, onboarding_queue, resultado
    
    return state, memory, onboarding_queue, "Continuando..."

# ============================================================
# SECCION_IV – MOTOR PEDAGÓGICO (CON GEMINI API)
# ============================================================

def SECCION_IV(INPUT, state, memory, onboarding_queue):
    tema = state["cur_actual"].get("tema", "Matemáticas")
    grado = state.get("grado_num", 1)
    personaje = state.get("personaje_elegido", "A")
    nivel_acc = calcular_acc(state.get("error_count", 0), state.get("aciertos_tema", 0))
    nombre = state.get("nombre", "Estudiante")
    historial = state.get("historial_preguntas", [])
    error_count = state.get("error_count", 0)
    aciertos_tema = state.get("aciertos_tema", 0)
    
    mapa_persona = {"A": "MAESTRO", "B": "DIVERTIDO", "C": "EXPLORADOR", "D": "PERSONALIZADO"}
    persona = mapa_persona.get(personaje, "MAESTRO")
    
    if state.get("gancho_usado", False) == False:
        goal = "explain_new_concept"
    elif error_count >= 3:
        goal = "reinforce_topic"
    elif aciertos_tema >= 3:
        goal = "evaluate_progress"
    else:
        goal = "reinforce_topic"
    
    contenido = generar_contenido_pedagogico(
        nombre=nombre,
        grado=grado,
        historia=historial,
        tema=tema,
        campo_formativo="Saberes y Pensamiento Científico",
        acc_level=nivel_acc,
        error_count=error_count,
        success_streak=aciertos_tema,
        persona=persona,
        goal=goal
    )
    
    state["pregunta_actual"] = {
        "pregunta": contenido.get("pregunta", ""),
        "respuesta": contenido.get("respuesta_esperada", ""),
        "tipo": "basica",
        "dificultad": 1,
        "pista": contenido.get("pista", "")
    }
    state["ultima_pregunta_id"] = contenido.get("pregunta", "unknown")
    
    mensaje = f"""
{contenido.get('visual_hook', '')}

📖 **{tema}**

{contenido.get('explicacion', '')}

💡 **Ejemplo:** {contenido.get('ejemplo', '')}

{contenido.get('emocion', '')}

🎯 **Ahora, tu turno:**

🔢 {contenido.get('pregunta', '')}
"""
    
    state["gancho_usado"] = True
    return state, memory, onboarding_queue, mensaje

# ============================================================
# SECCION_V – EXÁMENES
# ============================================================

def SECCION_V(INPUT, state, memory):
    nivel_acc = calcular_acc(state.get("error_count", 0), state.get("aciertos_tema", 0))
    dificultad = 1 if nivel_acc in ["ACC_1", "ACC_2"] else 2 if nivel_acc == "ACC_3" else 3
    
    if state.get("aciertos_tema", 0) == 0 and not state.get("tema_actual_completado", False):
        return state, memory, "😊 Primero repasemos juntos y después te evalúo."
    
    if state.get("errores_examen", 0) >= 2:
        return state, memory, "💛 Veo que esto se está poniendo difícil. ¿Quieres que hagamos una pausa y lo veamos juntos?\n\n🎮 A) Sí, ayúdame\n📝 B) Quiero seguir intentando"
    
    if INPUT == "A" and state["estado"] == "examen":
        state["estado"] = "clase"
        state = state_guard(state, "reinicio")
        return state, memory, "🌟 ¡Excelente decisión! Vamos a repasar juntos. No importa el examen, importa que aprendas."
    
    tema = state["cur_actual"].get("tema", obtener_tema(state["grado_num"], state.get("semana_n", 1)))
    
    if state.get("modo") == "BASIC":
        if state.get("pregunta_actual") is None:
            from logic.pedagogical_api import seleccionar_pregunta
            pregunta = seleccionar_pregunta(tema, dificultad, state.get("historial_preguntas", []))
            state["pregunta_actual"] = pregunta
            if "historial_preguntas" not in state:
                state["historial_preguntas"] = []
            state["historial_preguntas"].append(pregunta["id"])
            state["errores_examen"] = 0
        return state, memory, f"📝 EXAMEN BASIC:\n\n🔢 {state['pregunta_actual']['pregunta']}"
    
    elif state.get("modo") == "INTENSIVE":
        return state, memory, f"📝 EXAMEN INTENSIVE: 3 preguntas adaptadas a tu nivel."
    
    return state, memory, f"✨ RESULTADO: {state.get('aciertos_tema', 0)} aciertos\n📚 Tema: {state['cur_actual'].get('tema', 'N/A')}\n💡 Recomendación: ¡Sigue practicando! 💛"

# ============================================================
# SECCION_VI – ADN CON HMAC Y TALENTOS
# ============================================================

def SECCION_VI(state, memory):
    import json
    from core.adn_manager import generar_adn_seguro
    
    if state["cur_actual"] is None or state["cur_actual"].get("tema") in [None, ""]:
        return "⚠️ No hay tema activo para generar reporte."
    
    nombre = state.get("nombre", "Estudiante")
    xp = state.get("xp", 0)
    modo = state.get("modo", "BASIC")
    
    total_aciertos = state.get("aciertos_tema", 0)
    total_errores = state.get("error_count", 0)
    
    talento_texto = ""
    if state.get("talentos_detectados"):
        talento_texto = f"🌟 ¡Y algo increíble! Descubrimos que tienes talento para: {', '.join(state['talentos_detectados'])}. 💛"
    else:
        talento_texto = "🌟 Cada día descubres algo nuevo. ¡Sigue así!"
    
    mensaje_cierre = ""
    if total_aciertos > 0:
        mensaje_cierre += "Hoy aprendiste algo nuevo. 🌟 "
    if total_errores > 0 and total_aciertos > 0:
        mensaje_cierre += "No te rendiste, y eso es lo más importante. 💪 "
    if state.get("zoom_usado", False) or state.get("rescate_usado", False):
        mensaje_cierre += "Me encanta que pidieras ayuda. Eso es muy valiente. "
    mensaje_cierre += f"\n{talento_texto}\n"
    mensaje_cierre += "¿Vienes mañana? Te voy a estar esperando. 🧸"
    
    tcc_config = state.get("tcc_config", {})
    
    adn = {
        "name": nombre,
        "grado": state.get("grado_num", 0),
        "tema": state["cur_actual"].get("tema", ""),
        "progreso_estudiante": state.get("progreso_estudiante", []),
        "xp": xp,
        "mode": modo,
        "fecha_inicio": state.get("fecha_inicio_str", ""),
        "fecha_fin": state.get("fecha_fin_str", ""),
        "personaje": state.get("personaje_elegido", ""),
        "semana": state.get("semana_n", 1),
        "talentos_detectados": state.get("talentos_detectados", []),
        "mensaje_cierre": mensaje_cierre,
        "coord": state.get("cur_actual", {}),
        "aciertos_tema": state.get("aciertos_tema", 0),
        "error_count": state.get("error_count", 0),
        "zoom_usado": state.get("zoom_usado", False),
        "rescate_usado": state.get("rescate_usado", False),
        "nivel_dominio": state.get("nivel_dominio", "NOVATO"),
        "pregunta_actual": state.get("pregunta_actual", None),
        "tcc_config": {
            "activo": tcc_config.get("activo", False),
            "tipo": tcc_config.get("tipo"),
            "dias_totales": tcc_config.get("dias_totales", 0),
            "tasa_compresion": tcc_config.get("tasa_compresion", 1.0),
            "semanas_sep": tcc_config.get("semanas_sep", 0)
        }
    }
    
    adn_firmado = generar_adn_seguro(adn)
    return json.dumps(adn_firmado, ensure_ascii=False)

# ============================================================
# EJECUTAR (SIN GLOBALES)
# ============================================================

def EJECUTAR(INPUT, state, memory, onboarding_queue):
    state["turnos_totales"] = state.get("turnos_totales", 0) + 1
    state["ultimo_estado_valido"] = state.get("estado", "SELECCION_ENTRADA")
    
    if state["turnos_totales"] % 20 == 0:
        LUMOS_IDENTITY_REFRESH()
    
    if state["estado"] not in STATE_TABLE:
        return state, memory, onboarding_queue, RUTINA_RECUPERACION(state["estado"])
    
    side_quests, desviacion = VERIFICAR_ALINEACION(INPUT, state.get("side_quests", 0), {"tema": state.get("cur_actual", {}).get("tema", "")})
    state["side_quests"] = side_quests
    if desviacion:
        return state, memory, onboarding_queue, desviacion
    
    config = STATE_TABLE[state["estado"]]
    if "valid" in config and config["valid"] != ["*"]:
        if INPUT not in config["valid"]:
            return state, memory, onboarding_queue, UI_MAP["ERROR_SELECCION"]
    
    return SECCION_II(INPUT, state, memory, onboarding_queue)

