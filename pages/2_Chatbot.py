import streamlit as st 
import requests
from utils import *
import os
import json

apply_sidebar_style()
mostrar_sidebar_con_logo()


if os.environ['USER'] == "appuser":
    # En Streamlit Community Cloud
    WEBHOOK_URL = st.secrets["n8n"]["webhook_private_url"]
else:
    json_path = os.path.join(os.path.dirname(__file__), "..", "secrets", "n8n_urls.json")
    json_path = os.path.abspath(json_path)
    with open(json_path) as f:
        secrets = json.load(f)
    WEBHOOK_URL = secrets["chatbot_properties"]
    

# Darle un session ID de la corrida actual
session_id = st.session_state.get("session_id")
if not session_id:
    import uuid
    session_id = str(uuid.uuid4())
    st.session_state["session_id"] = session_id


st.set_page_config(
    page_title="Chat con Asistente",
    page_icon="QuAI",
    layout="wide", # "wide" para más espacio, "centered" para un look más compacto
    initial_sidebar_state="expanded"
)

st.set_page_config(page_title="Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Chat con Asistente")


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