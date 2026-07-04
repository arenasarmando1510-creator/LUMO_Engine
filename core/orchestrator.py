# ============================================================
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

