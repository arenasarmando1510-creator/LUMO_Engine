# ============================================================
# NOMBRE_ARCHIVO: /interface/app.py
# ============================================================
# ============================================================
# app.py – INTERFAZ STREAMLIT CON ESTADOS UX
# ITERACIÓN 6 – OBSERVABILIDAD
# LUMO ENGINE v0.9 – CONGELADO
# ============================================================
import sys
import os

# Esto le dice a Python que añada la carpeta raíz a su lista de búsqueda
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import time
import uuid
import hashlib
from core.session_manager import SessionManager

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(page_title="LUMO - AprendIA", page_icon="🌟", layout="wide")

# ============================================================
# INICIALIZACIÓN DE ESTADO
# ============================================================

if "manager" not in st.session_state:
    st.session_state.manager = SessionManager()
    st.session_state.session_id = st.session_state.manager.create_session()
    st.session_state.messages = []
    st.session_state.ux_status = "idle"
    st.session_state.retry_count = 0
    st.session_state.processed_inputs = set()
    st.session_state.debug_mode = False

# ============================================================
# TÍTULO
# ============================================================

st.title("🌟 LUMO - AprendIA")
st.markdown("*La sensación de que alguien está contigo mientras aprendes*")

# ============================================================
# ESTADOS UX
# ============================================================

if st.session_state.ux_status == "loading":
    st.info("⏳ LUMO está pensando... Un momento, por favor.")
elif st.session_state.ux_status == "retry":
    st.warning("🔄 Reintentando...")
elif st.session_state.ux_status == "degraded":
    st.warning("⚡ LUMO está en modo básico.")

# ============================================================
# CHAT
# ============================================================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ============================================================
# ENTRADA DEL USUARIO (CON IDEMPOTENCIA)
# ============================================================

if prompt := st.chat_input("Escribe tu respuesta aquí... 📝"):
    session_id = st.session_state.session_id
    input_id = hashlib.sha256((prompt + session_id).encode()).hexdigest()
    
    if input_id not in st.session_state.processed_inputs:
        st.session_state.processed_inputs.add(input_id)
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        st.session_state.ux_status = "loading"
        st.rerun()

# ============================================================
# PROCESAR RESPUESTA
# ============================================================

if st.session_state.ux_status == "loading":
    try:
        with st.spinner("LUMO está pensando..."):
            resultado = st.session_state.manager.process_input(
                st.session_state.session_id, 
                st.session_state.messages[-1]["content"]
            )
        
        if "error" in resultado or "falló" in resultado.get("display_text", "").lower():
            st.session_state.ux_status = "degraded"
        else:
            st.session_state.ux_status = "idle"
        
        st.session_state.messages.append({"role": "assistant", "content": resultado["display_text"]})
        st.session_state.retry_count = 0
        
    except Exception as e:
        if st.session_state.retry_count < 3:
            st.session_state.ux_status = "retry"
            time.sleep(2)
            st.rerun()
        else:
            st.session_state.ux_status = "degraded"
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "💛 Lo siento, estoy teniendo dificultades. Pero no te preocupes, podemos seguir practicando juntos."
            })
            st.session_state.retry_count = 0
    
    if st.session_state.ux_status != "retry":
        st.session_state.ux_status = "idle"
        st.rerun()

# ============================================================
# PANEL DE DEBUG
# ============================================================

if st.sidebar.checkbox("🔧 Mostrar Debug Panel", value=False):
    st.session_state.debug_mode = True
    
    with st.sidebar.expander("📊 DEBUG PANEL", expanded=True):
        session = st.session_state.manager.get_session(st.session_state.session_id)
        if session:
            s = session["state"]
            st.write("### 🔄 FSM Estado")
            st.write(f"**Estado actual:** `{s.get('estado', 'N/A')}`")
            st.write(f"**Nombre:** {s.get('nombre', '')}")
            st.write(f"**Grado:** {s.get('grado_num', 0)}")
            st.write(f"**XP:** {s.get('xp', 0)}")
            st.write(f"**Aciertos:** {s.get('aciertos_tema', 0)}")
            st.write(f"**Errores:** {s.get('error_count', 0)}")
            st.write(f"**Talentos:** {', '.join(s.get('talentos_detectados', [])) or 'Descubriendo...'}")
            st.write(f"**UX Status:** `{st.session_state.ux_status}`")
            st.write(f"**Retry Count:** {st.session_state.retry_count}")
            st.write(f"**Mensajes procesados:** {len(st.session_state.processed_inputs)}")
    
    with st.sidebar.expander("📋 Últimos logs (eventos)", expanded=False):
        st.write("(Los logs se muestran en consola)")
        st.code("Ver logs en la terminal donde corre Streamlit", language="bash")

