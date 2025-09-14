import asyncio
import os
import websockets
import json
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import threading

from utils import *

st.set_page_config(page_title="Monitoreo de Buques en Panamá", layout="wide")

st.title("🛳️ Monitoreo de Buques en Panamá")

CSV_FILE = "ships_positions.csv"

apply_sidebar_style()
mostrar_sidebar_con_logo()


# Si el archivo existe, lo sobreescribimos con un CSV vacío
df_columns = ["name", "mmsi", "latitude", "longitude", "speed", "timestamp"]

# Leyendo los secrets:
if os.environ['USER'] == "appuser":
    AIS_FEED_KEY = st.secrets["ais"]["key"]
else:
    with open("secrets/ais_stream.txt", 'r', encoding='utf-8') as f:
        AIS_FEED_KEY = f.read()


# --- Reiniciar CSV solo la primera vez ---
if "csv_initialized" not in st.session_state:
    empty_df = pd.DataFrame(columns=df_columns)
    empty_df.to_csv(CSV_FILE, index=False)
    st.session_state.ships_df = empty_df
    st.session_state.csv_initialized = True
    st.session_state.last_update = datetime.now() # Guardar la primera actualización
    print(f"✅ CSV reiniciado en {CSV_FILE}")
else:
    # Solo cargar CSV si ya fue inicializado
    if os.path.exists(CSV_FILE):
        st.session_state.ships_df = pd.read_csv(CSV_FILE)
    else:
        st.session_state.ships_df = pd.DataFrame(columns=df_columns)

# Función para recibir datos AIS en un hilo aparte
def ais_receiver():

    # Si ya existe un CSV previo, lo cargamos
    if "ships_df" not in st.session_state:
        if os.path.exists(CSV_FILE):
            st.session_state.ships_df = pd.read_csv(CSV_FILE)
        else:
            st.session_state.ships_df = pd.DataFrame(columns=df_columns)


    async def connect_ais_stream():
        subscribe_message = {
            "APIKey": AIS_FEED_KEY,
            "BoundingBoxes": [[[7, -83], [10, -77]]], # Bounding box para Panama
            "FilterMessageTypes": ["PositionReport","StaticDataReport"]
        }

        while True:  # Bucle de reconexión
            try:
                async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
                    await websocket.send(json.dumps(subscribe_message))
                    async for message_json in websocket:
                        message = json.loads(message_json)
                        print(f"Message: - {message}")



                        if message.get("MessageType") == "PositionReport":
                            ais_position_message = message['Message']['PositionReport']
                            ais_message_metadata = message['MetaData']

                            name_ = ais_message_metadata.get("ShipName")
                        
                            

                            new_row = pd.DataFrame([{
                                "name"      : ais_message_metadata.get("ShipName"),
                                "speed"     : ais_position_message.get("Sog"),
                                "longitude" : ais_position_message.get("Longitude"),
                                "latitude"  : ais_position_message.get("Latitude"),
                                "timestamp" : int(ais_position_message.get("Timestamp")),
                                "mmsi"      : ais_message_metadata.get("MMSI_String")
                            }])

                            print(f"🛳️ Nueva posición: {ais_position_message}")

                            # --- CÓDIGO CLAVE MODIFICADO AQUÍ ---
                            # Eliminar filas existentes del mismo buque por MMSI
                            st.session_state.ships_df = st.session_state.ships_df[
                                st.session_state.ships_df['name'] != name_
                            ].copy()


                            st.session_state.ships_df = pd.concat(
                                [st.session_state.ships_df, new_row],
                                ignore_index=True
                            )

                            new_row.to_csv(
                                CSV_FILE,
                                mode="a",
                                header=not os.path.exists(CSV_FILE),
                                index=False
                            )

            except websockets.exceptions.ConnectionClosedError as e:
                print(f"⚠️ Conexión cerrada, reintentando... ({e})")
                await asyncio.sleep(3)  # Espera antes de reconectar
            except Exception as e:
                print(f"❌ Error inesperado en AIS: {e}")
                await asyncio.sleep(5)  # Espera antes de reintentar

    asyncio.run(connect_ais_stream())

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

# Calcular tiempo transcurrido para mostrarlo
tiempo_transcurrido = datetime.now() - st.session_state.last_update

# Formatear el tiempo de la última actualización
ultima_actualizacion_str = st.session_state.last_update.strftime("%H:%M:%S")

# Mostrar la última actualización y el tiempo transcurrido
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Última actualización**: {ultima_actualizacion_str}")
with col2:
    st.markdown(f"**Hace:** `{tiempo_transcurrido.seconds} segundos`")


if st.button("🔄 Recargar CSV"):
    if os.path.exists(CSV_FILE):
        st.session_state.ships_df = pd.read_csv(CSV_FILE)
        st.success("Datos recargados desde CSV ✅")
        st.map(st.session_state.ships_df, latitude="longitude", longitude="latitude")
    else:
        st.warning("No existe el archivo CSV todavía.")

    st.session_state.last_update = datetime.now()

# --- Sección de posiciones ---
st.subheader("Últimas posiciones registradas")

if not st.session_state.ships_df.empty:
    df_display = st.session_state.ships_df.copy()
    df_display["timestamp"] = df_display["timestamp"].astype(int)
    df_display["timestamp"] = pd.to_datetime(df_display["timestamp"], unit='s')
    
    
    st.dataframe(df_display,
                 column_config = {
                     "name"         :   "Nombre",
                     "mmsi"         :   "MMSI",
                     "latitude"     :   "Latitud",
                     "longitude"    :   "Longitud",
                     "speed"        :   "Velocidad [nudos]",
                     "timestamp"    :   st.column_config.DatetimeColumn("Hora de Actualización",format="HH:MM:SS")
                 })
else:
    st.info("Aún no hay datos registrados.")

mostrar_sidebar_footer()