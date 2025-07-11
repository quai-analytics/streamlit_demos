import streamlit as st

# 1. Función personalizada para convertir columnas a minúsculas
def to_lowercase(dataframe):
    return dataframe.apply(lambda x: x.str.lower() if x.dtype == "object" else x)

def mostrar_sidebar_con_logo():
    st.sidebar.image('image/quai_analytics_logo.png')
    st.sidebar.markdown("---")  # Separador visual

def mostrar_sidebar_footer():
    st.sidebar.markdown("""
        <style>
        /* Flex container en sidebar para forzar fondo fijo */
        section[data-testid="stSidebar"] > div:first-child {
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        /* Empuja el footer al fondo */
        .sidebar-spacer {
            flex-grow: 1;
        }

        /* Estilo del footer */
        .sidebar-footer {
            font-size: 0.75em;
            color: white;
            text-align: left;
            padding-top: 1rem;
            padding-bottom: 0.5rem;
            border-top: 0.5px solid rgba(255,255,255,0.2);
            margin-top: 1rem;
        }
        </style>

        <div class="sidebar-spacer"></div>
        <div class="sidebar-footer">
            <em>Junio 2025</em><br>
            <small>© 2025 QuAI Analytics</small>
        </div>
    """, unsafe_allow_html=True)

def apply_sidebar_style():
    st.markdown("""
        <style>
        /* Sidebar container */
        section[data-testid="stSidebar"] {
            background-color: #082038;
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