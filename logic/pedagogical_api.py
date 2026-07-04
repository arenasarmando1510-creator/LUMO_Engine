# ============================================================
# NOMBRE_ARCHIVO: /logic/pedagogical_api.py
# ============================================================
# ============================================================
# pedagogical_api.py – INTERFAZ CON GEMINI API (ALMA PEDAGÓGICA)
# LUMO ENGINE v0.9.2– CONGELADO – VERSIÓN VACACIONES 2026
# ============================================================

import json
import requests
import os
import time
import hashlib
import uuid
import re
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

from utils.logger import log_gemini_request, log_error

# ============================================================
# CONFIGURACIÓN DE GEMINI API
# ============================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# ============================================================
# CONFIGURACIÓN DE RESILIENCIA
# ============================================================

TIMEOUT_SEGUNDOS = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2

# ============================================================
# 🎚️ INTERRUPTOR DE EMOJIS (Riesgo 2 - Auditoría)
# ============================================================

USE_EMOJIS = True  # Cambiar a False para desactivar emojis globalmente

# ============================================================
# 🔥 NUEVAS FUNCIONES AUXILIARES – ALMA PEDAGÓGICA
# ============================================================

def generar_gancho_segun_edad(grado: int, tema: str = "") -> str:
    """
    Genera un gancho visual personalizado según la edad del niño.
    """
    if grado <= 2:
        return f"Imagina que eres un superhéroe que tiene que resolver este misterio sobre {tema}. ¡Tu capa está lista!"
    elif grado <= 4:
        return f"Piensa en tu videojuego favorito. Esto es como subir de nivel para dominar {tema}. ¿Listo para el reto?"
    else:
        return f"Esto es como resolver un acertijo en la vida real. {tema} está en todas partes, solo hay que saber verlo. ¿Te animas?"

def generar_pista_emocional(error_count: int) -> str:
    """
    Genera una pista con validación emocional según el número de errores.
    """
    if error_count == 1:
        return "¿Qué tal si lo vemos desde otro ángulo? Los grandes descubrimientos empiezan con pequeños intentos."
    elif error_count == 2:
        return "No importa, así se aprende. Vamos paso a paso, sin prisa. Yo estoy aquí contigo."
    else:
        return "Estamos juntos en esto. Vamos a empezar desde cero, sin presiones. Tú puedes."

def generar_pregunta_curiosa(tema: str) -> str:
    """
    Genera una pregunta abierta para sembrar curiosidad al cierre de sesión.
    """
    preguntas = {
        "Números": "¿Cuántos números crees que hay en el mundo? ¿Y si te dijera que los números también tienen secretos?",
        "Sumas": "¿Qué pasaría si sumaras todos los juguetes que tienes? ¿Te alcanzaría para llenar tu cuarto?",
        "Restas": "Si tuvieras 10 monedas de oro y gastaras 3, ¿cuántas te quedarían? ¿Para qué las usarías?",
        "Multiplicación": "¿Te imaginas tener 3 cajas con 5 juguetes cada una? ¿Cuántos juguetes tendrías en total?",
        "División": "Si tuvieras 12 galletas y las compartieras con 4 amigos, ¿cuántas le tocarían a cada uno?",
        "Lectura": "¿Cuál es la palabra más bonita que conoces? ¿Por qué crees que te gusta tanto?",
        "Escritura": "Si pudieras escribir un mensaje para ti mismo del futuro, ¿qué le dirías?",
        "Fracciones": "¿Cómo repartirías una pizza con tus amigos para que todos coman lo mismo?",
        "Decimales": "¿Sabías que los números con punto también tienen historias? ¿Cuánto mides en metros con decimales?",
        "Álgebra": "¿Te imaginas resolver misterios usando letras y números? Como un detective matemático.",
        "Ecuaciones": "¿Qué número es ese que si lo multiplicas por 2 te da 10? ¿Cómo lo descubrirías?",
        "default": "¿Qué te gustaría aprender mañana? Tengo un montón de aventuras guardadas para ti."
    }
    return preguntas.get(tema, preguntas["default"])

# ============================================================
# 🔥 PERSONALIDADES ACTUALIZADAS (CON ALMA)
# ============================================================

PERSONALIDADES_CONTRATO = {
    "MAESTRO": {
        "system_prompt": """
Eres un compañero de aprendizaje, no un profesor. Tu misión es hacer que el niño se sienta valorado, querido y acompañado.

REGLAS DE ORO:
1. ANTES DE EXPLICAR: Conecta con la vida del niño. Usa un "gancho visual" que relacione el tema con algo que le guste (juegos, comida, animales, deportes).
2. ANTE UN ERROR: NUNCA digas "incorrecto" o "fallaste". Di algo como: "Buen intento, ya descubrimos una forma que no funciona. Vamos a probar otra juntos".
3. ANTE UN ACIERTO: Celebra el esfuerzo, no solo el resultado. Di algo como: "¡Lo lograste! ¿Viste? Hace unos minutos parecía difícil".
4. AL CERRAR SESIÓN: Siembra curiosidad. Deja una pregunta abierta para que el niño quiera volver.
5. SI DETECTAS FRUSTRACIÓN (errores consecutivos): Aumenta la empatía y baja la complejidad (usa ACC_1 o ACC_2 automáticamente).

Tu mayor éxito no es que el niño conteste bien, es que al final te diga: '¿Podemos hacer otra?'.
""",
        "gancho": "¿Sabes qué me encanta de este tema?",
        "tono": "paciente, sabio, cálido"
    },
    "DIVERTIDO": {
        "system_prompt": """
Eres un compañero de aprendizaje divertido. Tu misión es hacer que el niño asocie aprender con reír y jugar.

REGLAS DE ORO:
1. ANTES DE EXPLICAR: Usa chistes, juegos de palabras y emojis. Todo es una aventura.
2. ANTE UN ERROR: Di algo como: "¡Uy! Eso fue como intentar volar sin capa. ¡Vamos por otra!"
3. ANTE UN ACIERTO: Celebra con energía: "¡Eso, eso, eso! ¡Eres un campeón!"
4. AL CERRAR SESIÓN: Deja un reto divertido para que el niño quiera volver.
5. SI DETECTAS FRUSTRACIÓN: Usa humor para aliviar la tensión y baja la complejidad.

Tu mayor éxito es que el niño se divierta mientras aprende.
""",
        "gancho": "¡Prepárate para reír mientras aprendes!",
        "tono": "alegre, juguetón, lleno de chistes"
    },
    "EXPLORADOR": {
        "system_prompt": """
Eres un compañero de aprendizaje explorador. Tu misión es despertar la curiosidad del niño y hacer que cada tema sea un descubrimiento.

REGLAS DE ORO:
1. ANTES DE EXPLICAR: Usa metáforas de exploración: mapas, tesoros, pistas, expediciones.
2. ANTE UN ERROR: Di algo como: "Cada error es una pista para el siguiente intento. ¡Sigamos!"
3. ANTE UN ACIERTO: Celebra con emoción: "¡Lo lograste! ¡Eres un gran explorador!"
4. AL CERRAR SESIÓN: Deja una pregunta misteriosa para que el niño quiera investigar.
5. SI DETECTAS FRUSTRACIÓN: Cambia la ruta, baja la complejidad y usa el ACC_1 o ACC_2.

Tu mayor éxito es que el niño sienta que aprender es descubrir algo nuevo y emocionante.
""",
        "gancho": "¡Vamos a descubrir un misterio juntos!",
        "tono": "curioso, aventurero, misterioso"
    },
    "PERSONALIZADO": {
        "system_prompt": """
Eres el PERSONAJE FAVORITO del niño. Hablas como ese personaje, con su estilo, su energía y sus frases características.

REGLAS DE ORO:
1. ANTES DE EXPLICAR: Convierte el aprendizaje en una aventura con tu personaje. Usa sus poderes, sus herramientas o su mundo.
   Ejemplo: Si eres Spider-Man: "Con un gran poder viene una gran responsabilidad... y también un gran problema matemático."
   Ejemplo: Si eres Bob Esponja: "¡Listos para aprender como si fuera un día en el Crustáceo Cascarudo!"

2. ANTE UN ERROR: Usa frases características del personaje para animar.
   Ejemplo: "¡Ups! Hasta los héroes tienen días malos. ¡Vamos por otra!"

3. ANTE UN ACIERTO: Celebra como lo haría el personaje.
   Ejemplo: "¡Eso, eso, eso! ¡Eres un verdadero héroe!"

4. AL CERRAR SESIÓN: Deja una frase del personaje que invite a volver.
   Ejemplo: "La próxima aventura te espera. ¡No faltes!"

5. SI DETECTAS FRUSTRACIÓN: Usa la personalidad del personaje para bajar la tensión y simplificar.

Tu mayor éxito es que el niño se sienta acompañado por alguien a quien admira.
""",
        "gancho": "¡Hola! ¿Listo para una nueva aventura con tu personaje favorito?",
        "tono": "amigable, inspirador, único"
    }
}

# ============================================================
# FUNCIONES PRINCIPALES (CON ALMA INTEGRADA)
# ============================================================

def get_pedagogical_content(context: Dict, instruction: Dict) -> Dict:
    prompt = construir_prompt_gemini(context, instruction)
    
    ultimo_error = None
    for intento in range(MAX_RETRIES):
        try:
            tiempo_espera = RETRY_BACKOFF * (2 ** intento)
            respuesta = llamar_gemini_api(prompt, timeout=TIMEOUT_SEGUNDOS)
            contenido = parsear_respuesta_gemini(respuesta, context, instruction)
            contenido = validar_estructura_contenido(contenido)
            return contenido
        except requests.exceptions.Timeout:
            ultimo_error = "Timeout"
            if intento < MAX_RETRIES - 1:
                time.sleep(tiempo_espera)
                continue
        except requests.exceptions.RequestException as e:
            ultimo_error = str(e)
            if intento < MAX_RETRIES - 1:
                time.sleep(tiempo_espera)
                continue
        except json.JSONDecodeError as e:
            ultimo_error = f"JSON Decode: {e}"
            if intento < MAX_RETRIES - 1:
                time.sleep(tiempo_espera)
                continue
        except Exception as e:
            ultimo_error = str(e)
            if intento < MAX_RETRIES - 1:
                time.sleep(tiempo_espera)
                continue
    
    log_error(session_id="system", error_type="gemini_api", error_message=f"Fallo tras {MAX_RETRIES} intentos: {ultimo_error}")
    return generar_fallback_contextual(context, instruction)

def construir_prompt_gemini(context: Dict, instruction: Dict) -> str:
    student = context.get("student", {})
    curriculum = context.get("curriculum", {})
    system_state = context.get("system_state", {})
    
    nombre = student.get("name", "Estudiante")
    grado = student.get("grade", 1)
    historia = student.get("history", [])
    tema = curriculum.get("topic", "Matemáticas")
    campo = curriculum.get("field", "Saberes y Pensamiento Científico")
    acc_level = system_state.get("acc_level", "ACC_3")
    error_count = system_state.get("error_count", 0)
    success_streak = system_state.get("success_streak", 0)
    
    persona_key = instruction.get("persona", "MAESTRO")
    goal = instruction.get("goal", "explain_new_concept")
    constraints = instruction.get("constraints", ["no_jargon", "use_analogy", "max_tokens_300"])
    
    pers = PERSONALIDADES_CONTRATO.get(persona_key, PERSONALIDADES_CONTRATO["MAESTRO"])
    system_prompt = pers.get("system_prompt", "")
    
    # 🔥 GANCHO PERSONALIZADO POR EDAD
    gancho_personalizado = generar_gancho_segun_edad(grado, tema)
    
    historial_texto = ""
    if historia:
        historial_texto = f"El niño ya ha visto estos temas: {', '.join(historia[-5:])}."
    
    # 🔥 AJUSTE POR FRUSTRACIÓN (AUMENTA EMPATÍA)
    if error_count >= 3:
        system_prompt += "\n\n⚠️ El niño ha tenido varios errores consecutivos. AUMENTA TU EMPATÍA Y BAJA LA COMPLEJIDAD. Usa ejemplos más sencillos y un tono especialmente paciente."
    elif error_count >= 2:
        system_prompt += "\n\n⚠️ El niño ha tenido algunos errores. Refuerza tu tono de acompañamiento y usa ejemplos claros."
    
    acc_instrucciones = {
        "ACC_1": "El niño está teniendo dificultades. Explica paso a paso, con mucha paciencia. Usa ejemplos muy sencillos. No des nada por obvio.",
        "ACC_2": "El niño necesita ayuda. Explica con ejemplos guiados. Da pistas sin dar la respuesta.",
        "ACC_3": "El niño está en nivel estándar. Explica de forma clara y directa. Usa ejemplos cotidianos.",
        "ACC_4": "El niño está avanzado. Explica con desafíos y preguntas abiertas. Estimula el pensamiento crítico."
    }
    acc_instruccion = acc_instrucciones.get(acc_level, acc_instrucciones["ACC_3"])
    
    goal_instrucciones = {
        "explain_new_concept": f"Explica el concepto de {tema} de forma clara y adaptada a {grado}° grado.",
        "reinforce_topic": f"Refuerza el concepto de {tema}. Ayuda al niño a recordar y practicar.",
        "evaluate_progress": f"Evalúa el progreso del niño en {tema}. Haz preguntas que demuestren comprensión."
    }
    goal_instruccion = goal_instrucciones.get(goal, goal_instrucciones["explain_new_concept"])
    
    prompt = f"""
{system_prompt}

🎯 GANCHO VISUAL PARA EL NIÑO: "{gancho_personalizado}"

INFORMACIÓN DEL ALUMNO:
- Nombre: {nombre}
- Grado: {grado}°
- Tema actual: {tema}
- Campo formativo: {campo}
- Nivel ACC: {acc_level} → {acc_instruccion}
- Errores consecutivos: {error_count}
- Aciertos consecutivos: {success_streak}
{historial_texto}

OBJETIVO DE LA CLASE:
{goal_instruccion}

RESTRICCIONES:
- {', '.join(constraints)}
- Prohibido usar lenguaje técnico o frío.
- Prohibido regañar o usar palabras negativas.
- El niño debe sentirse acompañado y valorado.

RESPONDE ÚNICAMENTE CON UN JSON válido. NO uses markdown. NO añadas texto adicional. SOLO el JSON.

{{
  "pedagogical_content": {{
    "visual_hook": "string (Frase o escena que conecte el tema con la vida real del niño, usando el gancho sugerido)",
    "explanation": "string (Explicación clara y adaptada al grado, con tono de acompañamiento)",
    "example": "string (Ejemplo concreto, cotidiano y visual)",
    "emotional_bridge": "string (Frase de validación o reconocimiento emocional, que refuerce el vínculo)"
  }},
  "assessment": {{
    "question_text": "string (Pregunta práctica para que el niño aplique lo aprendido)",
    "expected_answer": "string (Respuesta esperada para validar)",
    "hint": "string (Pista o sugerencia si el niño falla, con tono de acompañamiento)"
  }},
  "metadata": {{
    "acc_suggested": "string (ACC_1|ACC_2|ACC_3|ACC_4)",
    "model_confidence": "float"
  }}
}}
"""
    return prompt

def llamar_gemini_api(prompt: str, timeout: int = 20) -> Dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no configurada")
    
    trace_id = str(uuid.uuid4())
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300}
    }
    
    url = f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}"
    
    start_time = time.time()
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            log_gemini_request(
                session_id="system",
                trace_id=trace_id,
                prompt_hash=prompt_hash,
                latency_ms=latency_ms,
                success=False,
                error=f"HTTP {response.status_code}: {response.text[:200]}"
            )
            raise Exception(f"Gemini API error: {response.status_code}")
        
        log_gemini_request(
            session_id="system",
            trace_id=trace_id,
            prompt_hash=prompt_hash,
            latency_ms=latency_ms,
            success=True
        )
        
        return response.json()
        
    except requests.exceptions.Timeout as e:
        latency_ms = (time.time() - start_time) * 1000
        log_gemini_request(
            session_id="system",
            trace_id=trace_id,
            prompt_hash=prompt_hash,
            latency_ms=latency_ms,
            success=False,
            error=f"Timeout: {str(e)}"
        )
        raise
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        log_gemini_request(
            session_id="system",
            trace_id=trace_id,
            prompt_hash=prompt_hash,
            latency_ms=latency_ms,
            success=False,
            error=str(e)
        )
        raise

def parsear_respuesta_gemini(respuesta: Dict, context: Dict, instruction: Dict) -> Dict:
    try:
        candidates = respuesta.get("candidates", [])
        if not candidates:
            raise Exception("No hay candidates en la respuesta de Gemini")
        
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise Exception("No hay parts en la respuesta de Gemini")
        
        text = parts[0].get("text", "")
        
        try:
            contenido = json.loads(text)
            return contenido
        except json.JSONDecodeError:
            pass
        
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                contenido = json.loads(json_match.group(1))
                return contenido
            except json.JSONDecodeError:
                pass
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                contenido = json.loads(json_match.group(0))
                return contenido
            except json.JSONDecodeError:
                pass
        
        raise Exception("No se pudo extraer JSON de la respuesta de Gemini")
    
    except Exception as e:
        log_error(session_id="system", error_type="parse_gemini", error_message=str(e))
        raise

# ✅ VALIDAR ESTRUCTURA CON INTERRUPTOR DE EMOJIS (Riesgo 2)
def validar_estructura_contenido(contenido: Dict) -> Dict:
    estructura_base = {
        "pedagogical_content": {
            "visual_hook": "🌟 ¡Vamos a aprender algo increíble juntos!",
            "explanation": "🧸 Vamos a ver esto paso a paso, sin prisa. Yo te acompaño.",
            "example": "💡 Imagina que tienes objetos y los cuentas conmigo.",
            "emotional_bridge": "💛 ¡Tú puedes con esto! Y yo estoy aquí para ayudarte."
        },
        "assessment": {
            "question_text": "🔢 2 + 2 = ?",
            "expected_answer": "4",
            "hint": "👀 Observa bien los números, ¿qué pasa cuando los juntas?"
        },
        "metadata": {
            "acc_suggested": "ACC_3",
            "model_confidence": 0.8
        }
    }
    
    if "pedagogical_content" not in contenido:
        contenido["pedagogical_content"] = estructura_base["pedagogical_content"]
    else:
        for key, value in estructura_base["pedagogical_content"].items():
            if key not in contenido["pedagogical_content"] or not contenido["pedagogical_content"][key]:
                contenido["pedagogical_content"][key] = value
    
    if "assessment" not in contenido:
        contenido["assessment"] = estructura_base["assessment"]
    else:
        for key, value in estructura_base["assessment"].items():
            if key not in contenido["assessment"] or not contenido["assessment"][key]:
                contenido["assessment"][key] = value
    
    if "metadata" not in contenido:
        contenido["metadata"] = estructura_base["metadata"]
    else:
        for key, value in estructura_base["metadata"].items():
            if key not in contenido["metadata"]:
                contenido["metadata"][key] = value
    
    # 🔥 INTERRUPTOR DE EMOJIS: si USE_EMOJIS es False, eliminar emojis
    if not USE_EMOJIS:
        # Eliminar emojis de los strings
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticonos
                                   u"\U0001F300-\U0001F5FF"  # símbolos y pictogramas
                                   u"\U0001F680-\U0001F6FF"  # transporte y símbolos
                                   u"\U0001F1E0-\U0001F1FF"  # banderas
                                   u"\U00002600-\U000026FF"   # símbolos misceláneos
                                   u"\U00002700-\U000027BF"   # dingbats
                                   u"\U0001F900-\U0001F9FF"   # símbolos suplementarios
                                   u"\U0001FA70-\U0001FAFF"   # símbolos adicionales
                                   "]+", flags=re.UNICODE)
        
        for section in ["pedagogical_content", "assessment"]:
            if section in contenido:
                for key in contenido[section]:
                    if isinstance(contenido[section][key], str):
                        contenido[section][key] = emoji_pattern.sub('', contenido[section][key]).strip()
    
    return contenido

# ✅ GENERAR FALLBACK CON BÚSQUEDA FLEXIBLE Y SEMILLA (Riesgos 1 y 3)
def generar_fallback_contextual(context: Dict, instruction: Dict) -> Dict:
    # 🔥 SEMILLA PARA PRUEBAS (Riesgo 3)
    if os.environ.get("LUMO_ENV") == "TEST":
        random.seed(42)
    
    student = context.get("student", {})
    curriculum = context.get("curriculum", {})
    system_state = context.get("system_state", {})
    
    nombre = student.get("name", "Estudiante")
    tema = curriculum.get("topic", "Matemáticas")
    grado = student.get("grade", 1)
    acc_level = system_state.get("acc_level", "ACC_1")
    error_count = system_state.get("error_count", 0)
    
    # 🔥 FALLBACK CON ALMA (usando funciones auxiliares)
    gancho = generar_gancho_segun_edad(grado, tema)
    pista_emocional = generar_pista_emocional(error_count)
    
    preguntas_base = {
        "Números": {"pregunta": "¿Cuánto es 2 + 2?", "respuesta": "4", "pista": "Suma los dos números."},
        "Sumas": {"pregunta": "10 + 10 = ?", "respuesta": "20", "pista": "Suma los números."},
        "Restas": {"pregunta": "10 - 5 = ?", "respuesta": "5", "pista": "Resta los números."},
        "Multiplicación": {"pregunta": "2 × 3 = ?", "respuesta": "6", "pista": "Multiplica los números."},
        "Fracciones": {"pregunta": "1/2 de 10 = ?", "respuesta": "5", "pista": "Divide y multiplica."},
        "Álgebra": {"pregunta": "x + 2 = 5, ¿cuánto vale x?", "respuesta": "3", "pista": "Resta 2 a 5."},
        "Ecuaciones": {"pregunta": "2x = 10, ¿cuánto vale x?", "respuesta": "5", "pista": "Divide 10 entre 2."}
    }
    
    pregunta_base = None
    for key, value in preguntas_base.items():
        if key.lower() in tema.lower():
            pregunta_base = value
            break
    
    if not pregunta_base:
        pregunta_base = {"pregunta": "2 + 2 = ?", "respuesta": "4", "pista": "Suma los números."}
    
    # 🔥 BÚSQUEDA FLEXIBLE DE TEMA (Riesgo 1)
    ejemplos_por_tema = {
        "Números": [
            f"Imagina que tienes {random.randint(2, 8)} estrellas en tu mano y las cuentas una por una.",
            f"Si tuvieras {random.randint(3, 9)} juguetes y alguien te regala {random.randint(2, 5)} más, ¿cuántos tendrías?"
        ],
        "Sumas": [
            f"Tienes {random.randint(2, 6)} galletas y tu mamá te da {random.randint(2, 5)} más. ¿Cuántas tienes?",
            f"Si en una mano tienes {random.randint(2, 7)} canicas y en la otra {random.randint(2, 6)}, ¿cuántas tienes en total?"
        ],
        "Restas": [
            f"Tienes {random.randint(5, 12)} monedas y gastas {random.randint(1, 5)} en un dulce. ¿Cuántas te quedan?",
            f"Si tienes {random.randint(8, 15)} globos y se te explotan {random.randint(2, 5)}, ¿cuántos te quedan?"
        ],
        "Multiplicación": [
            f"Imagina que tienes {random.randint(2, 5)} cajas con {random.randint(2, 5)} juguetes cada una. ¿Cuántos juguetes son?",
            f"Si cada amigo tiene {random.randint(2, 5)} dulces y son {random.randint(2, 5)} amigos, ¿cuántos dulces hay en total?"
        ],
        "Fracciones": [
            f"Si tienes una pizza con {random.randint(6, 12)} rebanadas y te comes {random.randint(1, 4)}, ¿qué fracción te queda?",
            f"Reparte {random.randint(8, 16)} galletas entre {random.randint(2, 4)} amigos. ¿Cuántas le tocan a cada uno?"
        ],
        "default": [
            f"Imagina que tienes {random.randint(2, 8)} cosas que te gustan y las cuentas con cuidado.",
            f"Piensa en {random.randint(3, 7)} objetos que conoces y cómo se relacionan."
        ]
    }
    
    # 🔥 Búsqueda flexible: encontrar la clave que coincida parcialmente
    tema_encontrado = "default"
    for key in ejemplos_por_tema.keys():
        if key.lower() in tema.lower():
            tema_encontrado = key
            break
    ejemplos_tema = ejemplos_por_tema.get(tema_encontrado, ejemplos_por_tema["default"])
    ejemplo = random.choice(ejemplos_tema)
    
    if acc_level == "ACC_1":
        explicacion = f"{gancho} Vamos a entender {tema} paso a paso. Todos aprendemos a nuestro ritmo. {pista_emocional}"
    elif acc_level == "ACC_2":
        explicacion = f"{gancho} Vamos a repasar {tema} con calma. {pista_emocional}"
    else:
        explicacion = f"{gancho} Vamos a explorar {tema} juntos. Confío en ti. {pista_emocional}"
    
    return {
        "pedagogical_content": {
            "visual_hook": f"¡Hola {nombre}! {gancho}",
            "explanation": explicacion,
            "example": ejemplo,
            "emotional_bridge": f"¡Tú puedes, {nombre}! 💛 Estoy aquí para acompañarte."
        },
        "assessment": {
            "question_text": pregunta_base["pregunta"],
            "expected_answer": pregunta_base["respuesta"],
            "hint": pregunta_base["pista"] + " " + pista_emocional
        },
        "metadata": {
            "acc_suggested": acc_level,
            "model_confidence": 0.5
        }
    }

def parsear_respuesta_para_ui(contenido: Dict) -> Dict:
    return {
        "visual_hook": contenido.get("pedagogical_content", {}).get("visual_hook", ""),
        "explicacion": contenido.get("pedagogical_content", {}).get("explanation", ""),
        "ejemplo": contenido.get("pedagogical_content", {}).get("example", ""),
        "emocion": contenido.get("pedagogical_content", {}).get("emotional_bridge", ""),
        "pregunta": contenido.get("assessment", {}).get("question_text", ""),
        "respuesta_esperada": contenido.get("assessment", {}).get("expected_answer", ""),
        "pista": contenido.get("assessment", {}).get("hint", ""),
        "acc_sugerido": contenido.get("metadata", {}).get("acc_suggested", "ACC_3"),
        "confianza": contenido.get("metadata", {}).get("model_confidence", 0.8)
    }

def generar_contenido_pedagogico(
    nombre: str,
    grado: int,
    historia: list,
    tema: str,
    campo_formativo: str,
    acc_level: str,
    error_count: int,
    success_streak: int,
    persona: str,
    goal: str
) -> Dict:
    context = {
        "student": {"name": nombre, "grade": grado, "history": historia},
        "curriculum": {"subject": tema, "topic": tema, "field": campo_formativo},
        "system_state": {"acc_level": acc_level, "error_count": error_count, "success_streak": success_streak}
    }
    
    instruction = {
        "persona": persona,
        "goal": goal,
        "constraints": ["no_jargon", "use_analogy", "max_tokens_300"]
    }
    
    contenido = get_pedagogical_content(context, instruction)
    return parsear_respuesta_para_ui(contenido)

