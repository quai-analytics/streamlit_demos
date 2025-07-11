import streamlit as st
import os
import json
import sys

# Agrega el directorio actual (dashboard) al path
sys.path.append(os.path.dirname(__file__))

from utils import *

st.set_page_config(
    page_title="QuAI Analytics - Pruebas de Concepto",
    page_icon="QuAI",
    layout="wide", # "wide" para más espacio, "centered" para un look más compacto
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Sidebar container */
    section[data-testid="stSidebar"] {
        background-color: #082038; /* tu color deseado */
    }

    /* Forzar texto blanco en todos los elementos del sidebar */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Enlaces (a) y listas (li) si quieres más precisión */
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] li {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
# 🤖 Panel de Pruebas de Concepto – QuAI Analytics

Bienvenido al espacio de demostración de **QuAI Analytics**. Este dashboard reúne una serie de **Pruebas de Concepto (PoC)** diseñadas para mostrar cómo la **Inteligencia Artificial** puede generar valor real en distintas áreas de negocio.

Aquí podrá explorar ejemplos funcionales que ilustran:

- Automatización de tareas repetitivas con IA
- Modelos predictivos aplicados a datos reales o simulados
- Análisis inteligente para descubrir patrones, riesgos y oportunidades
- Interfaces conversacionales (chatbots) y soluciones basadas en lenguaje natural

Cada módulo ha sido desarrollado como una muestra ágil y adaptable de lo que podemos construir juntos para su organización.

> ℹ️ **Este entorno es una maqueta interactiva** con fines ilustrativos. Los datos pueden ser ficticios y las interfaces están pensadas para inspirar ideas, no como productos finales.


""")

apply_sidebar_style()
mostrar_sidebar_con_logo()
mostrar_sidebar_footer()


