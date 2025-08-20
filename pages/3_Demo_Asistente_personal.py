import streamlit as st 
import requests
from utils import *
import uuid  # Importar la librería uuid


apply_sidebar_style()
mostrar_sidebar_con_logo()


WEBHOOK_URL = st.secrets["n8n"]["webhook_assistant_url"]
#WEBHOOK_URL  =  "https://n8n.quaianalytics.com/webhook/7f7ad1c2-8711-43dc-be2b-4bf710d0daa2/chat"

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
    iframe_url = f"https://calendar.google.com/calendar/embed?src=alvarezycuadraconsulting%40gmail.com&ctz=America%2FPanama&reload_key={iframe_key}"


    # Mostrar el iframe con el URL dinámico y la altura ajustada
    st.markdown(f"""
        <iframe src="{iframe_url}" style="border: 0" width="100%" height="{container_height}" frameborder="0" scrolling="no"></iframe>
    """, unsafe_allow_html=True)