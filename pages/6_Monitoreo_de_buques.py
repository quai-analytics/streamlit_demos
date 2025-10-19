import asyncio
import os
import sys
import websockets
import json
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import numpy as np
import traceback

from utils import *

apply_sidebar_style()
mostrar_sidebar_con_logo()
mostrar_sidebar_footer()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Monitoreo de Buques en Tiempo Real", layout="wide")

st.title("🛳️ Monitoreo de Buques en Tiempo Real")

DF_COLUMNS = ["name", "mmsi", "latitude", "longitude", "speed", "timestamp", "ship_type", "destination", "eta"]

# Leyendo los secrets:
if os.environ['USER'] == "appuser":
    # En Streamlit Community Cloud
    AIS_FEED_KEY = st.secrets["ais_stream"]["key"]
else:
    # En local
    with open("secrets/ais_stream.txt", 'r', encoding='utf-8') as f: # Tu clave de AIS
        AIS_FEED_KEY = f.read()

# --- Initialize session state ---
if "ships_df" not in st.session_state:
    st.session_state.ships_df = pd.DataFrame(columns=DF_COLUMNS)


async def fetch_and_update_dataframe():
    """
    Connects to the AIS stream, fetches a single position report, and
    updates the DataFrame in st.session_state with 10 new reports.
    """
    # Usar el DataFrame del estado de la sesión para no perder datos previos
    local_df = st.session_state.ships_df.copy()
    if not local_df.empty:
        local_df = local_df.set_index("mmsi")

    subscribe_message = {
        "APIKey": AIS_FEED_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]],
        "FilterMessageTypes": ["PositionReport"]
    }
    
    try:
        async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
            st.toast("🔌 Conectando al stream de AIS...")
            await websocket.send(json.dumps(subscribe_message))
            
            vessels_captured = 0
            # Esperar hasta capturar 10 reportes de posición
            async for message_json in websocket:
                message = json.loads(message_json)
                if message.get("MessageType") == "PositionReport":
                    ais_position_message = message['Message']['PositionReport']
                    ais_message_metadata = message['MetaData']

                    ship_name = ais_message_metadata.get("ShipName", "N/A").strip()
                    mmsi = ais_message_metadata.get("MMSI")

                    # Simulación de datos de contexto
                    ship_types = ['Cargo', 'Tanker', 'Passenger', 'Tug', 'Fishing', 'Container Ship']
                    destinations = ['Balboa Port', 'Cristobal Port', 'Manzanillo Terminal', 'Rodman Port', 'En route']
                    np.random.seed(mmsi % (2**32 - 1))
                    ship_type = np.random.choice(ship_types)
                    destination = np.random.choice(destinations)
                    eta = datetime.now() + timedelta(hours=np.random.randint(1, 48))

                    # Actualizar o añadir la fila en el DataFrame local
                    # Usar un diccionario para asignar valores evita errores de orden de columnas
                    local_df.loc[mmsi] = {
                        "name": ship_name,
                        "speed": ais_position_message.get("Sog"),
                        "longitude": ais_position_message.get("Longitude"),
                        "latitude": ais_position_message.get("Latitude"),
                        "timestamp": datetime.now(),
                        "ship_type": ship_type,
                        "destination": destination,
                        "eta": eta
                    }
                    
                    vessels_captured += 1
                    st.toast(f"Buque {vessels_captured}/10: {ship_name}")

                    if vessels_captured >= 10:
                        break # Salir del bucle una vez que se capturan 10
            
            # Actualizar el DataFrame en el estado de la sesión una sola vez al final
            st.session_state.ships_df = local_df.reset_index()

    except Exception as e:
        st.error(f"❌ Error al conectar o recibir datos: {e}")
        print(traceback.format_exc())

# --- UI y Lógica Principal ---

st.markdown("""
            > ℹ️ **Esta aplicación inteligente rastrea la ubicación de buques. 
            Usa el botón para capturar un nuevo dato de posición desde la fuente en tiempo real y añadirlo a la vista.""")

# --- UI ---
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("📡 Capturar Nuevo Dato de Buque", type="primary", use_container_width=True):
        with st.spinner("Esperando un nuevo reporte de posición..."):
            asyncio.run(fetch_and_update_dataframe())
            st.rerun() # Forzar recarga para actualizar métricas y tabla

with col2:
    total_ships = len(st.session_state.ships_df)
    if total_ships > 0:
        last_update_time = pd.to_datetime(st.session_state.ships_df['timestamp']).max()
        m1, m2 = st.columns(2)
        m1.metric("Buques en Vista", total_ships)
        m2.metric("Último Dato Recibido", last_update_time.strftime("%H:%M:%S"))

if st.session_state.ships_df.empty:
    st.info("📡 Presiona el botón para capturar los datos de un buque por primera vez.")

# Mostrar datos si existen
if not st.session_state.ships_df.empty:
    df_display = st.session_state.ships_df.copy()
    df_display = df_display.dropna(subset=['latitude', 'longitude'])
    df_display["timestamp"] = pd.to_datetime(df_display["timestamp"])
    df_display["eta"] = pd.to_datetime(df_display["eta"])

    st.map(df_display, latitude="latitude", longitude="longitude")

    st.subheader("Últimas posiciones registradas")
    st.dataframe(
        df_display.sort_values("timestamp", ascending=False),
        column_config={
            "name": "Nombre",
            "mmsi": "MMSI",
            "latitude": "Latitud",
            "longitude": "Longitud",
            "speed": "Velocidad [nudos]",
            "timestamp": st.column_config.DatetimeColumn("Última Señal", format="HH:mm:ss"),
            "ship_type": "Tipo de Buque",
            "destination": "Destino",
            "eta": st.column_config.DatetimeColumn("ETA", format="YYYY-MM-DD HH:mm")
        },
        use_container_width=True,
        hide_index=True
    )
