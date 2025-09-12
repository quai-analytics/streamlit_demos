import streamlit as st 
import os
import io
import json
import sys
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Importar librerías necesarias para BigQuery y pandas
from google.cloud import storage
from google.oauth2 import service_account
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import *

apply_sidebar_style()
mostrar_sidebar_con_logo()

BUCKET_NAME = "data_quai_dev" # Nombre del bucket

if os.environ['USER'] == "appuser":
    # En Streamlit Community Cloud
    Credentials = st.secrets["gcp_service_account"]
    print(Credentials)
else:
    service_account_path = os.path.join(
        os.path.dirname(__file__), "..", "secrets", "streamlit_bucket.json"
    )
    credentials = service_account.Credentials.from_service_account_file(service_account_path)

client = storage.Client(credentials=credentials, project=credentials.project_id)
bucket = client.bucket(BUCKET_NAME)

dataframes = {}

for file in ["vitalmedic_data_enriched.csv", "vitalmedic_sales_history.csv"]:
    blob = bucket.blob(file)

    # 5️⃣ Descargar contenido del CSV como texto
    csv_data = blob.download_as_text()

    # 6️⃣ Leer CSV en pandas
    dataframes[file] = pd.read_csv(io.StringIO(csv_data))  # para Python >=3.6 usar io.StringIO


st.set_page_config(
    page_title="Cuadro de Control de Inteligencia de Negocio",  # Título de la pestaña
    page_icon="📉",                                # Icono de la app
    layout="wide", # "wide" para más espacio, "centered" para un look más compacto
    initial_sidebar_state="expanded"
)

df_1 = dataframes["vitalmedic_sales_history.csv"]
df_2 = dataframes["vitalmedic_data_enriched.csv"]

#df_1 = pd.read_csv("data/vitalmedic_sales_history.csv")
#df_2 = pd.read_csv("data/vitalmedic_data_enriched.csv")

df = pd.merge(
    df_1, 
    df_2[["ProductID", "Brand", "Cost", "Price","StockLevel"]], 
    on="ProductID", 
    how="right")

st.title("📉 Cuadro de Control de Inteligencia de Negocio")

# Crear columna de fecha de ejemplo (puedes reemplazar con tu campo real)
df["Date"] = pd.to_datetime(df["Date"])

# Extraer el año
df["Year"] = df["Date"].dt.year

# Extraer Quarter
df["Quarter"] = df["Date"].dt.to_period("Q").astype(str)

# Calcular Revenue
df["RevenuePotential"] = df["Price"] * df["StockLevel"]


# Usa paletas pastel en tus gráficos
color_sequence = px.colors.qualitative.Pastel


# ==============================
# Contenedor para filtro por año
# ==============================
filter_1, filter_2 = st.columns([1, 3])
with filter_1:
    with st.container(border=True):
        anios = df["Year"].unique()
        anio_sel = st.selectbox("Seleccionar Año", sorted(anios))
        df_filtered = df[df["Year"] == anio_sel]

with filter_2:
    with st.container(border=True):
        # Selección múltiple de categorías
        categorias = df["Category"].unique()
        categorias_sel = st.multiselect(
            "Seleccionar Categorías",
            options=categorias,
            default=categorias  # todas seleccionadas por defecto
        )

# Aplicar filtros
df_filtered = df[(df["Year"] == anio_sel) & (df["Category"].isin(categorias_sel))]

# Calculando el margen
df_filtered["Margin"] = (df_filtered["Price"] - df_filtered["Cost"])/df_filtered["Price"] * 100

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.metric("Total de Productos", df_filtered["ProductID"].unique().shape[0], delta=5)
with metric_2:
    st.metric("Margen Promedio", f"{df_filtered["Margin"].mean():.1f}%", delta = -1.2)

with metric_3:    
# Producto más rentable
    prod_rent = df_filtered.loc[(df_filtered["Price"] - df_filtered["Cost"]).idxmax()]
    st.metric("Producto más rentable", prod_rent["ProductID"])

level1_1, level1_2, level1_3 = st.columns([1,3,2])

# ==============================
# Agregar gráfico de barras por Quarter
# ==============================
revenue_quarter = df_filtered.groupby("Quarter")["RevenuePotential"].sum().reset_index()

with level1_1:
    fig_bar1 = px.bar(
        revenue_quarter,
        x="Quarter",
        y="RevenuePotential",
        labels={"RevenuePotential": "Revenue Total ($)", "Quarter": "Trimestre"},
        title=f"Revenue Total por Quarter - {anio_sel}",
        template = "seaborn"
    )
    st.plotly_chart(fig_bar1, use_container_width=True)

# ==============================
# Agregar pie chart por categoría
# ==============================
revenue_category = df_filtered.groupby("Category")["RevenuePotential"].sum().reset_index()

with level1_2:
    count_category = df_filtered.groupby("Category")["ProductID"].count().reset_index(name="Cantidad")

    fig_pie = px.pie(
        count_category,
        values="Cantidad",
        names="Category",
        title="Cantidad de Artículos por Categoría",
        hole=0.3,
        template = "seaborn",
        labels={"Category":"Categoría"},
    )

    fig_pie.update_layout(
        legend_orientation="h",
        legend_y=-0.2,   # posición vertical de la leyenda
        legend_x=0.5,    # centrar horizontalmente
        legend_xanchor="center"
    )
    st.plotly_chart(fig_pie, use_container_width=True)\
    
    # ==============================
    # Barra horizontal: revenue por categoría
    # ==============================
    revenue_category = df_filtered.groupby("Category")["RevenuePotential"].sum().reset_index()
with level1_3:
    fig_bar2 = px.bar(
        revenue_category,
        x="RevenuePotential",
        y="Category",
        orientation="h",
        text_auto=".2s",
        title=f"Revenue Total por Categoría ({anio_sel})",
        labels={"RevenuePotential":"Revenue Total ($)", "Category":"Categoría"},
        template = "seaborn"
    )

    st.plotly_chart(fig_bar2, use_container_width=True)


top_products = df_filtered.groupby("ProductName")["RevenuePotential"].sum().sort_values(ascending=False).head(10).reset_index()
fig_top = px.bar(
    top_products, 
    x="RevenuePotential", 
    y="ProductName", 
    orientation="h", 
    title="Top 10 Productos por Revenue",
    labels={"RevenuePotential":"Revenue Total ($)", "ProductName":"Producto"},
    template = "seaborn")
st.plotly_chart(fig_top, use_container_width=True)

st.divider()

# Selecciona las columnas y aplica formato
df_display = df_filtered.copy()
df_display["RevenuePotential"] = df_display["RevenuePotential"].map("${:,.2f}".format)
df_display["Price"] = df_display["Price"].map("${:,.2f}".format)
df_display["Cost"] = df_display["Cost"].map("${:,.2f}".format)
df_display["Margin"] = df_display["Margin"].map("{:.1f}%".format)

# Opcional: selecciona solo las columnas más relevantes
cols = [
    "ProductID", "ProductName", "Brand", "Category", "Date", "Quarter",
    "StockLevel", "Price", "Cost", "RevenuePotential", "Margin"
]
df_display = df_display[cols]

# Aplica estilos con pandas Styler
styled_df = df_display.style\
    .highlight_max(subset=["RevenuePotential"], color="#b7e1cd")\
    .set_properties(**{"background-color": "#f1f3f4"}, subset=pd.IndexSlice[:, :])\
    .set_table_styles([{
        "selector": "th",
        "props": [("background-color", "#e3e6ea"), ("font-weight", "bold")]
    }])




st.dataframe(styled_df, use_container_width=True, hide_index=True)



mostrar_sidebar_footer()