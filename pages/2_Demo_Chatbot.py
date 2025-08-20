import streamlit as st 
import requests
from utils import *

apply_sidebar_style()
mostrar_sidebar_con_logo()

WEBHOOK_URL = st.secrets["n8n"]["webhook_private_url"]

#WEBHOOK_URL  = "https://n8n.quaianalytics.com/webhook/3f1efc51-ca56-4956-8131-076326ee6cc6/chat"

# Darle un session ID de la corrida actual
session_id = st.session_state.get("session_id")
if not session_id:
    import uuid
    session_id = str(uuid.uuid4())
    st.session_state["session_id"] = session_id


st.set_page_config(
    page_title="Chat con Asistente Inmobiliario",
    page_icon="QuAI",
    layout="wide", # "wide" para más espacio, "centered" para un look más compacto
    initial_sidebar_state="expanded"
)

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

# Muestra historial de conversación
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for entry in st.session_state.chat_history:
    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])
        

# Input del usuario
if prompt := st.chat_input("Escribe tu pregunta..."):
    # Guarda el mensaje del usuario
    st.session_state.chat_history.append({"role": "user", "content": prompt})
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
            st.session_state.chat_history.append({"role": "assistant", "content": reply})