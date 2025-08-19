import streamlit as st 
import requests
from utils import *

apply_sidebar_style()
mostrar_sidebar_con_logo()


WEBHOOK_URL = st.secrets["n8n"]["webhook_url"]

# Darle un session ID de la corrida actual
session_id = st.session_state.get("session_id")
if not session_id:
    import uuid
    session_id = str(uuid.uuid4())
    st.session_state["session_id"] = session_id


st.set_page_config(
    page_title="Chat con Asistente para Citas",
    page_icon="QuAI",
    layout="wide", # "wide" para más espacio, "centered" para un look más compacto
    initial_sidebar_state="expanded"
)

st.set_page_config(page_title="Asistente", page_icon="🤖", layout="wide")
st.title("🤖 Chat con Asistente para Citas")

st.set_page_config(page_title="Chatbot Inmobiliario", page_icon="🤖", layout="wide")
st.title("🤖 Chat con Asistente Inmobiliario")

# Texto institucional compacto
st.sidebar.markdown("""
    <div style='font-size: 0.85em; line-height: 1.3em; margin-top: -20px; margin-bottom: 10px; color: white;'>
        <strong>Asistente IA Virtual Inmobiliario Inteligente</strong><br>
        Prueba de concepto que utiliza inteligencia artificial para responder consultas sobre bienes raíces en Panamá. Conversa con nuestro chatbot y recibe asesoría inmediata sobre precios, zonas, procesos de compra o alquiler y más, todo en lenguaje natural.
        </div>
        
""", unsafe_allow_html=True)

mostrar_sidebar_footer()

# --- Diseño en dos columnas ---
col1, col2 = st.columns([2, 1])  # Chat más ancho que el calendario


with col1:
    st.subheader("💬 Chatbot")

    # Historial de conversación
    if "chat_history_schedule" not in st.session_state:
        st.session_state.chat_history_schedule = []

    for entry in st.session_state.chat_history_schedule:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])

    # Input del usuario
    if prompt := st.chat_input("Escribe tu pregunta..."):
        # Guarda el mensaje del usuario
        st.session_state.chat_history_schedule.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Muestra loading de respuesta
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    # Enviar a n8n
                    response = requests.post(
                        WEBHOOK_URL,
                        json={"chatInput": prompt,"sessionId": session_id},
                        timeout=30
                    )
                    reply = response.json().get("output", "Lo siento, no pude procesar tu solicitud.")
                except Exception as e:
                    reply = f"Error al contactar al agente IA: {str(e)}"

                st.markdown(reply)
                st.session_state.chat_history_schedule.append({"role": "assistant", "content": reply})

st.markdown(
    """
    <style>
    .calendar-container iframe {
        width: 100%;
        height: 80vh; /* scale with viewport */
        border: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with col2:
    st.subheader("📅 Google Calendar")
    st.markdown(
        """
        <iframe src="https://calendar.google.com/calendar/embed?src=ricardo.alvarez%40quaianalytics.com&ctz=America%2FPanamaa" style="border: 0" width="800" height="600" frameborder="0" scrolling="no"></iframe>
        """,
        unsafe_allow_html=True,
    )
