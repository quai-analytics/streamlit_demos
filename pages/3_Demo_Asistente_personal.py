import streamlit as st 
import requests
from utils import *
import json
import uuid  # Importar la librería uuid
import os

apply_sidebar_style()
mostrar_sidebar_con_logo()

print(os.environ)
print("ST_ENV" in os.environ)
print(os.environ["ST_ENV"])

if "ST_ENV" in os.environ and os.environ["ST_ENV"] == "CLOUD":
    # En Streamlit Community Cloud
    WEBHOOK_URL = st.secrets["n8n"]["webhook_assistant_url"]
    GOOGLE_CALENDAR_IFRAME_URL = st.secrets["n8n"]["google_calendar_frame"]
else:
    json_path = os.path.join(os.path.dirname(__file__), "..", "secrets", "n8n_urls.json")
    json_path = os.path.abspath(json_path)
    with open(json_path) as f:
        secrets = json.load(f)
    
    WEBHOOK_URL = secrets["personal_assistant"]
    GOOGLE_CALENDAR_IFRAME_URL = secrets["google_calendar_frame"]


# Darle un session ID de la corrida actual
session_id = st.session_state.get("session_id")
if not session_id:
    session_id = str(uuid.uuid4())
    st.session_state["session_id"] = session_id


st.set_page_config(
    page_title="Chat con Asistente Personal",
    page_icon="QuAI",
    layout="wide", # "wide" para más espacio, "centered" para un look más compacto
    initial_sidebar_state="expanded"
)

st.set_page_config(page_title="Asistente Personal", page_icon="🤖", layout="wide")
st.title("🤖 Chat con Asistente para Citas")

# Texto institucional compacto
st.sidebar.markdown("""
    <strong>Asistente para Agendar Citas</strong><br>
    Prueba de asistente inteligente se conecta con Google Calendar para ayudarte a gestionar tus citas con facilidad. Conversa con él para crear, agendar, modificar o eliminar eventos y citas de tu calendario, todo usando lenguaje natural.
    </div>
        
""", unsafe_allow_html=True)

mostrar_sidebar_footer()

st.subheader("💬 Asistente Personal")
col1, col2 = st.columns([3, 7])

# Define una variable para la altura
container_height = 600

# Coloca contenido en la primera columna
with col1:

    # Usamos st.container() para crear el contenedor con scroll
    chat_container = st.container(height=container_height)

    # Historial de conversación
    if "chat_history_schedule" not in st.session_state:
        st.session_state.chat_history_schedule = []

    

    # Muestra los mensajes en el contenedor
    with chat_container:
        for entry in st.session_state.chat_history_schedule:
            with st.chat_message(entry["role"]):
                st.markdown(entry["content"])

    # Input del usuario
    if prompt := st.chat_input("..."):
        # Guarda el mensaje del usuario
        st.session_state.chat_history_schedule.append({"role": "user", "content": prompt})
        
        # Vuelve a mostrar el chat con el nuevo mensaje del usuario
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

        # Muestra loading de respuesta
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
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

# Columna 2: Calendario de Google incrustado
with col2:
    col_2_1, col_2_2 = st.columns(2)
    with col_2_1:
        st.markdown("### 🗓️ Tu Calendario de Citas")
    # Botón para recargar el calendario
    with col_2_2:
        if st.button("Actualizar Calendario"):
            # Esta es la lógica clave: al presionar el botón, se añade un parámetro
            # de consulta único al URL del iframe, forzando una recarga completa.
            st.session_state.iframe_key = str(uuid.uuid4())
    
    # Obtener la clave de recarga de la sesión, si no existe, crear una por defecto
    iframe_key = st.session_state.get("iframe_key", "default_key")

    # URL del iframe, ahora con el parámetro de recarga
    iframe_url = GOOGLE_CALENDAR_IFRAME_URL + f"={iframe_key}"


    # Mostrar el iframe con el URL dinámico y la altura ajustada
    st.markdown(f"""
        <iframe src="{iframe_url}" style="border: 0" width="100%" height="{container_height}" frameborder="0" scrolling="no"></iframe>
    """, unsafe_allow_html=True)