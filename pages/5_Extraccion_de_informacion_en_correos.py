import streamlit as st
import pandas as pd
import joblib
from utils import *

apply_sidebar_style()
mostrar_sidebar_con_logo()


st.set_page_config(
    page_title="Implementacion de IA en Correos",  # Título de la pestaña
    page_icon="📧",                                # Icono de la app
    layout="wide", # "wide" para más espacio, "centered" para un look más compacto
    initial_sidebar_state="expanded"
)


st.title("📧 Solución para leer correo y extraer información")
st.write("Conéctate a tu Gmail y deja que la IA extraiga información clave de los correos.")


# -----------------------------
# Scopes de Gmail API
# -----------------------------
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


# -----------------------------
# Autenticación Gmail
# -----------------------------
creds = None
token_path = "../secrets/token_gmail.pkl"
credentials_path = "../secrets/credentials_gmail.json"