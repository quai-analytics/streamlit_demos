import streamlit as st
import pandas as pd
import joblib
from utils import *

apply_sidebar_style()
mostrar_sidebar_con_logo()


# -----------------------------
# 1. Cargar modelo
# -----------------------------
model_pipeline = joblib.load('churn_model.pkl')

# -----------------------------
# 2. Configuración de la app
# -----------------------------

st.set_page_config(
    page_title="Predictor de fidelización de Clientes",  # Título de la pestaña
    page_icon="📉",                                # Icono de la app
    layout="wide", # "wide" para más espacio, "centered" para un look más compacto
    initial_sidebar_state="expanded"
)

st.title("📉 Panel de Predicción de fidelización de Clientes")

st.markdown("""
            > ℹ️ **Esta aplicación inteligente evalúa la probabilidad de que un cliente se dé de baja. 
            Al ingresar datos clave como el tiempo que lleva con nosotros, cargos mensuales, tipo de contrato, 
            quejas y pagos atrasados, te ayudará a tomar decisiones estratégicas. Analiza los resultados para 
            contactar a los clientes en riesgo o fortalecer la relación con los más fieles.**
            """)

st.divider()
st.write("Ingrese la información del cliente para analizar si tiene alta probabilidad de darse de baja.")

# -----------------------------
# 3. Inputs del usuario
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    tenure = st.number_input("Tenure (meses como cliente)", min_value=1, max_value=60, value=12)
    monthly_charges = st.number_input("Cargos mensuales ($)", min_value=30, max_value=200, value=70)

with col2:
    contract = st.selectbox("Tipo de contrato", ["Month-to-Month", "1-year", "2-year"])
    complaints = st.slider("Número de quejas", min_value=0, max_value=10, value=0)
    payment_late = st.radio("¿Pagos atrasados?", ["No", "Sí"])

payment_late = 1 if payment_late == "Sí" else 0


# Crear dataframe con datos del cliente
new_customer = pd.DataFrame([{
    "Tenure": tenure,
    "MonthlyCharges": monthly_charges,
    "Contract": contract,
    "Complaints": complaints,
    "PaymentLate": payment_late
}])


# -----------------------------
# 4. Predicción
# -----------------------------
if st.button("Analizar cliente"):
    prediction = model_pipeline.predict(new_customer)[0]
    prob = model_pipeline.predict_proba(new_customer)[0][1]

    if prediction == 1:
        st.error(f"⚠️ El cliente TIENE ALTA PROBABILIDAD de darse de baja ({prob:.2%}), se recomienda contactar.")
    else:
        st.success(f"✅ El cliente probablemente SE MANTENDRA con nosotros: ({1-prob:.2%})")

    st.write("### Detalles de probabilidad")
    st.progress(prob)

mostrar_sidebar_footer()