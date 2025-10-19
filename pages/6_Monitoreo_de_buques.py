import asyncio
import os
import websockets
import json
from datetime import datetime
import streamlit as st
import pandas as pd
import threading
import time
import traceback

from utils import *

st.set_page_config(page_title="Monitoreo de Buques en Panamá", layout="wide")

st.title("🛳️ Monitoreo de Buques en Panamá")

CSV_FILE = "ships_positions.csv"

apply_sidebar_style()
mostrar_sidebar_con_logo()


# Si el archivo existe, lo sobreescribimos con un CSV vacío
DF_COLUMNS = ["name", "mmsi", "latitude", "longitude", "speed", "timestamp"]

# Leyendo los secrets:
if os.environ['USER'] == "appuser":
    AIS_FEED_KEY = st.secrets["ais"]["key"]
else:
    with open("secrets/ais_stream.txt", 'r', encoding='utf-8') as f:
        AIS_FEED_KEY = f.read()


# --- Initialize session state ---
if "ships_df" not in st.session_state:
    st.session_state.ships_df = pd.DataFrame(columns=DF_COLUMNS)
    st.session_state.last_update = None

# Función para recibir datos AIS en un hilo aparte
def ais_receiver():
    """
    Connects to the AIS stream and updates the ship data in st.session_state.
    This function is designed to be run in a separate thread.
    """
    async def connect_ais_stream():
        subscribe_message = {
            "APIKey": AIS_FEED_KEY,
            "BoundingBoxes": [[[7, -83], [10, -77]]], # Bounding box para Panama
            "FilterMessageTypes": ["PositionReport"] # Focus on position reports
        }

        while True:  # Bucle de reconexión
            try:
                async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
                    print("🔌 WebSocket connected. Sending subscription message...")
                    await websocket.send(json.dumps(subscribe_message))
                    
                    async for message_json in websocket:
                        message = json.loads(message_json)
                        
                        if message.get("MessageType") == "PositionReport":
                            ais_position_message = message['Message']['PositionReport']
                            ais_message_metadata = message['MetaData']

                            ship_name = ais_message_metadata.get("ShipName", "N/A").strip()
                            mmsi = ais_message_metadata.get("MMSI")

                            new_row = pd.DataFrame([{
                                "name"      : ship_name,
                                "mmsi"      : mmsi,
                                "speed"     : ais_position_message.get("Sog"),
                                "longitude" : ais_position_message.get("Longitude"),
                                "latitude"  : ais_position_message.get("Latitude"),
                                "timestamp" : ais_message_metadata.get("time_utc"),
                            }])

                            print(f"🛳️  Position received for: {ship_name} ({mmsi})")

                            # --- Thread-safe update of the DataFrame ---
                            # Get the current DataFrame
                            current_df = st.session_state.ships_df

                            # Remove existing entry for the ship
                            updated_df = current_df[current_df['mmsi'] != mmsi]

                            # Add the new entry
                            updated_df = pd.concat(
                                [updated_df, new_row],
                                ignore_index=True
                            )

                            # Atomically update the session state
                            st.session_state.ships_df = updated_df
                            st.session_state.last_update = datetime.now()

            except websockets.exceptions.ConnectionClosedError as e:
                print(f"⚠️ Conexión cerrada, reintentando... ({e})")
                await asyncio.sleep(5)  # Espera antes de reconectar
            except Exception as e:
                print(traceback.format_exc())
                print(f"❌ Error inesperado en AIS: {e}")
                await asyncio.sleep(10)  # Espera más tiempo antes de reintentar

    # Create and run the event loop in the current thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_ais_stream())

st.markdown("""
            > ℹ️ **Esta aplicación inteligente rastrea la ubicación de buques en la zona del Canal de Panamá. 
            Utiliza datos en tiempo real de un servicio AIS (Sistema de Identificación Automática) a través 
            de una conexión WebSocket. La información de los barcos (nombre, velocidad, latitud y longitud) 
            se almacena y visualiza en un mapa y en una tabla de datos interactiva.""")

# Lanzar el hilo solo una vez
if "ais_thread_started" not in st.session_state:
    thread = threading.Thread(target=ais_receiver, daemon=True)
    thread.start()
    st.session_state.ais_thread_started = True
    print("🚀 AIS receiver thread started.")

# --- UI Placeholders ---
header_placeholder = st.empty()
map_placeholder = st.empty()
data_placeholder = st.empty()

mostrar_sidebar_footer()

# --- Auto-refreshing UI loop ---
while True:
    df = st.session_state.ships_df

    with header_placeholder.container():
        if st.session_state.last_update:
            tiempo_transcurrido = datetime.now() - st.session_state.last_update
            ultima_actualizacion_str = st.session_state.last_update.strftime("%H:%M:%S")
            col1, col2 = st.columns(2)
            col1.metric("Buques Rastreados", len(df))
            col2.metric("Última Actualización", ultima_actualizacion_str, f"-{tiempo_transcurrido.seconds} s")
        else:
            st.info("📡 Esperando la primera señal de datos de buques...")

    if not df.empty:
        # Clean up data for display
        df_display = df.copy()
        df_display = df_display.dropna(subset=['latitude', 'longitude'])
        df_display["timestamp"] = pd.to_datetime(df_display["timestamp"])

        map_placeholder.map(df_display, latitude="latitude", longitude="longitude")

        with data_placeholder.container():
            st.subheader("Últimas posiciones registradas")
            st.dataframe(
                df_display.sort_values("timestamp", ascending=False),
                column_config={
                    "name": "Nombre",
                    "mmsi": "MMSI",
                    "latitude": "Latitud",
                    "longitude": "Longitud",
                    "speed": "Velocidad [nudos]",
                    "timestamp": st.column_config.DatetimeColumn("Hora de Actualización", format="HH:mm:ss")
                },
                use_container_width=True,
                hide_index=True
            )

    time.sleep(2) # Refresh interval in seconds