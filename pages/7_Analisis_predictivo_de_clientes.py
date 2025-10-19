# Importación de librerías
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import os
import sys
import plotly.express as px

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import *

apply_sidebar_style()
mostrar_sidebar_con_logo()

# Título de la aplicación
st.title('Prueba de Concepto de Clustering de Clientes 🇵🇦')
st.write("---")

# Barra lateral para configuración
st.sidebar.header('Configuración del Análisis')
num_clientes = st.sidebar.slider('Número de Clientes (Simulados)', 100, 5000, 500)
num_transacciones = st.sidebar.slider('Número de Transacciones (Simuladas)', 1000, 50000, 5000)
num_clusters = st.sidebar.slider('Número de Clusters (K)', 2, 10, 4)

# Función para simular datos
@st.cache_data
def simular_datos(n_clientes, n_transacciones):
    """Genera datos de transacciones de clientes de manera aleatoria."""
    cliente_ids = [f'C{i:03}' for i in range(1, n_clientes + 1)]
    transacciones = []
    fechas_base = datetime.now() - timedelta(days=365)
    
    for _ in range(n_transacciones):
        cliente_id = np.random.choice(cliente_ids)
        dias_desde_compra = np.random.randint(1, 365)
        fecha_compra = fechas_base + timedelta(days=dias_desde_compra)
        monto = round(np.random.uniform(5.0, 500.0), 2)
        transacciones.append([cliente_id, fecha_compra, monto])
    
    df = pd.DataFrame(transacciones, columns=['ID_Cliente', 'Fecha_Compra', 'Monto_Compra'])
    df['Fecha_Compra'] = pd.to_datetime(df['Fecha_Compra'])
    return df

# Generar datos y calcular RFM
with st.spinner('Generando datos y calculando métricas RFM...'):
    df_transacciones = simular_datos(num_clientes, num_transacciones)

    # Calcular RFM
    fecha_hoy = df_transacciones['Fecha_Compra'].max() + timedelta(days=1)
    df_rfm = df_transacciones.groupby('ID_Cliente').agg({
        'Fecha_Compra': lambda fecha: (fecha_hoy - fecha.max()).days,
        'ID_Cliente': 'count',
        'Monto_Compra': 'sum'
    }).rename(columns={'Fecha_Compra': 'Recencia', 'ID_Cliente': 'Frecuencia', 'Monto_Compra': 'Monetario'})
    df_rfm = df_rfm.reset_index()

st.subheader('1. Datos RFM (Recencia, Frecuencia, Monetario)')
st.write("Estas métricas se calculan a partir de las transacciones de cada cliente para describir su comportamiento de compra.")
st.dataframe(df_rfm.head())

# Escalar los datos
scaler = StandardScaler()
df_rfm_escalado = scaler.fit_transform(df_rfm[['Recencia', 'Frecuencia', 'Monetario']])
df_rfm_escalado = pd.DataFrame(df_rfm_escalado, columns=['Recencia', 'Frecuencia', 'Monetario'])

# Método del codo para el número de clusters
st.subheader('2. Método del Codo para Encontrar K')
st.write("El método del codo ayuda a encontrar el número óptimo de clusters. Buscamos el punto de inflexión en el gráfico.")

# Crear un placeholder para el gráfico del codo
elbow_chart_placeholder = st.empty()

if st.checkbox('Mostrar gráfico del método del codo'):
    inercia = []
    rango_clusters = range(1, 11)
    for k in rango_clusters:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto') # Usar 'auto' para evitar FutureWarning
        kmeans.fit(df_rfm_escalado)
        inercia.append(kmeans.inertia_)
    
    fig, ax = plt.subplots()
    ax.plot(rango_clusters, inercia, marker='o')
    ax.set_title('Método del Codo')
    ax.set_xlabel('Número de Clusters (K)')
    ax.set_ylabel('Inercia')
    elbow_chart_placeholder.pyplot(fig, use_container_width=True)
    plt.close(fig) # Liberar memoria
else:
    elbow_chart_placeholder.empty() # Limpiar el placeholder si la casilla no está marcada
    

# Aplicar K-Means con el K seleccionado por el usuario
st.subheader(f'3. Clustering con K-Means (K = {num_clusters})')
kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
df_rfm['Cluster'] = kmeans.fit_predict(df_rfm_escalado)

st.write(f"Los clientes han sido agrupados en {num_clusters} segmentos distintos.")
st.dataframe(df_rfm.head())

# Análisis y visualización
st.subheader('4. Análisis de los Clusters')
st.write("A continuación, se muestran las características promedio de cada segmento de clientes.")

cluster_medias = df_rfm.groupby('Cluster').agg({
    'Recencia': 'mean',
    'Frecuencia': 'mean',
    'Monetario': 'mean'
}).reset_index()

st.dataframe(cluster_medias.style.background_gradient(cmap='YlGnBu'))

st.markdown("""
- **Recencia:** Días desde la última compra. A menor valor, más reciente.
- **Frecuencia:** Número de compras. A mayor valor, más compras.
- **Monetario:** Gasto total. A mayor valor, más dinero gastado.
""")

st.subheader('5. Visualización de los Clusters')
st.write("Observa la distribución de los clientes en el espacio 3D de RFM. Cada color representa un cluster.")

fig_3d = px.scatter_3d(df_rfm, x='Recencia', y='Frecuencia', z='Monetario',
                        color=df_rfm['Cluster'].astype(str),
                        title="Segmentación de Clientes (RFM)",
                        labels={'Recencia': 'Recencia', 'Frecuencia': 'Frecuencia', 'Monetario': 'Monetario'})
fig_3d.update_traces(marker=dict(size=4, opacity=0.8), selector=dict(mode='markers'))
st.plotly_chart(fig_3d, use_container_width=True)

st.write("---")
st.subheader('Próximos Pasos para tu Portafolio')
st.info("""
**1. Explica los Hallazgos:** Analiza las medias de los clusters y dales un nombre descriptivo (ej. 'Clientes de Alto Valor', 'Clientes en Riesgo', 'Clientes Nuevos').

**2. Propón Acciones:** Sugiere estrategias de negocio concretas para una PYME en Panamá, como:
- **Campañas de email marketing** dirigidas a cada segmento.
- **Programas de fidelización** para los clientes de alto valor.
- **Ofertas de reactivación** para los clientes en riesgo.

**3. Despliega la Aplicación:** Una vez que tengas tu código en un repositorio de GitHub, puedes desplegarlo de manera gratuita en la [Comunidad de Streamlit Cloud](https://streamlit.io/cloud).
""")