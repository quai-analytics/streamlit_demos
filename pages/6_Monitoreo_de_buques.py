import asyncio
import os
import websockets
import json
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import threading
import time
import queue
import numpy as np
import traceback

from utils import *

st.set_page_config(page_title="Monitoreo de Buques en Panamá", layout="wide")

st.title("🛳️ Monitoreo de Buques en Panamá")

CSV_FILE = "ships_positions.csv"

apply_sidebar_style()
mostrar_sidebar_con_logo()


# Si el archivo existe, lo sobreescribimos con un CSV vacío
DF_COLUMNS = ["name", "mmsi", "latitude", "longitude", "speed", "timestamp", "ship_type", "destination", "eta"]

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
    st.session_state.data_queue = queue.Queue()

# Función para recibir datos AIS en un hilo aparte
def ais_receiver(q: queue.Queue):
    """
    Connects to the AIS stream and puts the ship data into a queue.
    This function is designed to be run in a separate thread.
    """
    async def connect_ais_stream():
        subscribe_message = {
            "APIKey": AIS_FEED_KEY,
            "BoundingBoxes": [[[-90, -180], [90, 180]]],# Bounding box por defecto
            # [[[7, -83], [10, -77]]], # Bounding box para Panama
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

                            # --- Simulación de datos de contexto adicionales ---
                            ship_types = ['Cargo', 'Tanker', 'Passenger', 'Tug', 'Fishing', 'Container Ship']
                            destinations = ['Balboa Port', 'Cristobal Port', 'Manzanillo Terminal', 'Rodman Port', 'En route']
                            
                            # Para mantener consistencia, basamos la elección en el MMSI
                            np.random.seed(mmsi % (2**32 - 1)) # Usar MMSI como semilla
                            ship_type = np.random.choice(ship_types)
                            destination = np.random.choice(destinations)
                            
                            # Simular un ETA entre 1 y 48 horas desde ahora
                            eta_hours = np.random.randint(1, 48)
                            eta = datetime.now() + timedelta(hours=eta_hours)

                            new_row = pd.DataFrame([{
                                "name"      : ship_name,
                                "mmsi"      : mmsi,
                                "speed"     : ais_position_message.get("Sog"),
                                "longitude" : ais_position_message.get("Longitude"),
                                "latitude"  : ais_position_message.get("Latitude"),
                                "timestamp" : datetime.now(),
                                "ship_type" : ship_type,
                                "destination": destination,
                                "eta"       : eta,
                            }])

                            print(f"🛳️  Position received for: {ship_name} ({mmsi})")

                            # Put the new data into the queue for the main thread to process
                            q.put(new_row)

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
    thread = threading.Thread(target=ais_receiver, args=(st.session_state.data_queue,), daemon=True)
    thread.start()
    st.session_state.ais_thread_started = True
    print("🚀 AIS receiver thread started.")

# --- Procesamiento de datos y renderizado de UI ---
# El procesamiento de la cola se ejecuta en cada recarga de la página
# para mantener los datos subyacentes actualizados.
def process_queue():
    while not st.session_state.data_queue.empty(): # Vaciar la cola
        new_row = st.session_state.data_queue.get()
        mmsi = new_row.iloc[0]['mmsi']

        current_df = st.session_state.ships_df

        # Remove existing entry for the ship
        updated_df = current_df[current_df['mmsi'] != mmsi]

        # Add the new, updated entry
        updated_df = pd.concat([updated_df, new_row], ignore_index=True)

        # Atomically update the session state
        st.session_state.ships_df = updated_df
        st.session_state.last_update = datetime.now()

process_queue()

# --- UI Layout ---
df = st.session_state.ships_df

if st.session_state.last_update:
    tiempo_transcurrido = datetime.now() - st.session_state.last_update
    ultima_actualizacion_str = st.session_state.last_update.strftime("%H:%M:%S")
    col1, col2, col3 = st.columns([1, 1, 2])
    col1.metric("Buques Rastreados", len(df))
    col2.metric("Última Actualización", ultima_actualizacion_str, f"-{tiempo_transcurrido.seconds} s")
    with col3:
        st.write("") # Espaciador
        st.button("🔄 Actualizar Mapa y Datos") # Al presionar, Streamlit recarga el script
else:
    st.info("📡 Esperando la primera señal de datos de buques...")
    st.button("🔄 Intentar Actualizar")

if not df.empty:
    # Clean up data for display
    df_display = df.copy()
    df_display = df_display.dropna(subset=['latitude', 'longitude'])
    # Convertir timestamp y eta a formato de fecha para la visualización
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

mostrar_sidebar_footer()