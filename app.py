import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Plataforma de Simulación Metalúrgica",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ESTILOS CSS PARA REPLICAR TU MAQUETA
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .hero-container {
        background: linear-gradient(180deg, rgba(20,20,20,0.6) 0%, rgba(15,15,15,0.95) 100%), 
                    url('Assets/hero_background.jpg');
        background-size: cover;
        background-position: center;
        border-radius: 16px;
        padding: 60px 40px;
        min-height: 520px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.5);
    }
    
    .hero-title-ref {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 35px;
        color: #ffffff;
        max-width: 650px;
    }
    
    div.stButton > button[key="btn_crear"] {
        background-color: #4D5BF7 !important;
        color: white !important;
        border-radius: 30px !important;
        padding: 12px 30px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0px 4px 15px rgba(77, 91, 247, 0.4) !important;
    }
    
    div.stButton > button[key="btn_cargar"] {
        background-color: #E2C044 !important;
        color: #111111 !important;
        border-radius: 30px !important;
        padding: 12px 30px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0px 4px 15px rgba(226, 192, 68, 0.3) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INICIALIZACIÓN DE ESTADOS (SESSION STATE)
# ---------------------------------------------------------
if "seccion_activa" not in st.session_state:
    st.session_state["seccion_activa"] = "Inicio"

if "datos_simulacion" not in st.session_state:
    st.session_state["datos_simulacion"] = {
        "tonelaje_A": 1000.0,
        "ley_cu_A": 1.50,
        "circuito": "1. Rougher – Scavenger (Con Recirculación a Cabeza)"
    }

# BASE DE DATOS DE SULFUROS DE COBRE
ESPECIES_BASE = {
    "Calcopirita (CuFeS2)": 34.63,
    "Bornita (Cu5FeS4)": 63.31,
    "Calcosina (Cu2S)": 79.85,
    "Covelina (CuS)": 66.47
}

OPCIONES_CIRCUITO = {
    "1. Rougher – Scavenger (Con Recirculación a Cabeza)": {"imagen": "Assets/Diagrama_Rougher_Scavenger1.png", "etapas": ["Rougher", "Scavenger"]},
    "2. Rougher – Scavenger (Abierto / En Serie)": {"imagen": "Assets/Diagrama_Rougher_Scavenger2.png", "etapas": ["Rougher", "Scavenger"]},
    "3. Rougher – Cleaner (Abierto / En Serie)": {"imagen": "Assets/Diagrama_Rougher_Cleaner1.png", "etapas": ["Rougher", "Cleaner"]},
    "4. Rougher – Cleaner (Cerrado a Cabeza)": {"imagen": "Assets/Diagrama_Rougher_Cleaner2.png", "etapas": ["Rougher", "Cleaner"]},
    "5. Rougher – Cleaner – Scavenger (Recirculación a Cleaner)": {"imagen": "Assets/Diagrama_Rougher_Cleaner_Scavenger1.png", "etapas": ["Rougher", "Cleaner", "Scavenger"]},
    "6. R – Cl1 – Cl2 – Sc (Doble Recirculación A)": {"imagen": "Assets/Diagrama_Rougher_Cleaner_Cleaner2_Scavenger1.png", "etapas": ["Rougher", "Cleaner1", "Cleaner2", "Scavenger"]},
    "7. R – Cl1 – Cl2 – Sc (Doble Recirculación B)": {"imagen": "Assets/Diagrama_Rougher_Cleaner_Cleaner2_Scavenger2.png", "etapas": ["Rougher", "Cleaner1", "Cleaner2", "Scavenger"]}
}

# ---------------------------------------------------------
# BARRA DE NAVEGACIÓN SUPERIOR (NAVBAR)
# ---------------------------------------------------------
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([3, 1, 1, 1, 1])

with nav_col2:
    if st.button("Inicio", use_container_width=True):
        st.session_state["seccion_activa"] = "Inicio"
        st.rerun()

with nav_col3:
    if st.button("Quienes somos", use_container_width=True):
        st.session_state["seccion_activa"] = "QuienesSomos"
        st.rerun()

with nav_col4:
    if st.button("Simuladores", use_container_width=True):
        st.session_state["seccion_activa"] = "Simuladores"
        st.rerun()

with nav_col5:
    if st.button("Flowsheets", use_container_width=True):
        st.session_state["seccion_activa"] = "Flowsheets"
        st.rerun()

# ---------------------------------------------------------
# VISTA 1: INICIO (PANTALLA DE BIENVENIDA)
# ---------------------------------------------------------
if st.session_state["seccion_activa"] == "Inicio":
    
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title-ref">Plataforma de<br>Simulación Metalúrgica</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_space = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("Crear Proyecto Desde Cero", key="btn_crear", use_container_width=True):
            st.session_state["seccion_activa"] = "Flotacion"
            st.rerun()
            
    with col_btn2:
        with st.popover("Cargar Archivo", use_container_width=True):
            archivo_droppeado = st.file_uploader("Arrastra aquí tu archivo (.json):", type=["json"])
            if archivo_droppeado:
                try:
                    datos = json.load(archivo_droppeado)
                    st.session_state["datos_simulacion"].update(datos)
                    st.success("¡Proyecto cargado correctamente!")
                    if st.button("▶️ Abrir Simulación", use_container_width=True):
                        st.session_state["seccion_activa"] = "Flotacion"
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al leer archivo: {e}")

# ---------------------------------------------------------
# VISTA 2: QUIENES SOMOS
# ---------------------------------------------------------
elif st.session_state["seccion_activa"] == "QuienesSomos":
    st.title("👥 Quiénes Somos")
    st.caption("Equipo de Desarrollo DiRoPS")
    st.divider()
    st.info("Espacio reservado para la presentación institucional y del equipo académico/industrial.")

# ---------------------------------------------------------
# VISTA 3: SIMULADORES
# ---------------------------------------------------------
elif st.session_state["seccion_activa"] == "Simuladores":
    st.title("📊 Selección de Simuladores por Área")
    st.divider()
    
    cat_sel = st.selectbox(
        "Selecciona el Área Metalúrgica:",
        [
            "✨ Flotación de Espumas (ACTIVO)",
            "🔒 Conminución y Molienda (Próximamente)",
            "🔒 Hidrometallurgia y Lixiviación (Próximamente)",
            "🔒 Manejo de Sólidos / Espesamiento (Próximamente)"
        ]
    )
    
    if "Flotación" in cat_sel:
        if st.button("🚀 Ingresar al Simulador de Flotación", use_container_width=True):
            st.session_state["seccion_activa"] = "Flotacion"
            st.rerun()

# ---------------------------------------------------------
# VISTA 4: SIMULADOR DE FLOTACIÓN ACTIVO
# ---------------------------------------------------------
elif st.session_state["seccion_activa"] == "Flotacion":
    st.title("⚙️ Simulador Metalúrgico: Flotación Celda por Celda")
    st.sidebar.title("📐 Controles de Flotación")
    
    # Opción para regresar al Inicio desde el panel lateral
    if st.sidebar.button("🏠 Regresar al Inicio", use_container_width=True):
        st.session_state["seccion_activa"] = "Inicio"
        st.rerun()

    st.sidebar.divider()

    circuito_seleccionado = st.sidebar.selectbox("Diagrama de Flujo:", list(OPCIONES_CIRCUITO.keys()))
    info_circuito = OPCIONES_CIRCUITO[circuito_seleccionado]
    
    tonelaje_A = st.sidebar.number_input("Tonelaje Fresco Total A (TMSPH)", min_value=1.0, value=1000.0)
    ley_cu_A = st.sidebar.number_input("Ley de Cobre Cabeza (%Cu)", min_value=0.01, value=1.50)
    
    st.info("Simulador de Flotación configurado y ejecutándose con éxito.")

# ---------------------------------------------------------
# VISTA 5: FLOWSHEETS
# ---------------------------------------------------------
elif st.session_state["seccion_activa"] == "Flowsheets":
    st.title("🛠️ Diseñador Libre de Flowsheets")
    st.caption("Módulo de interconexión libre de corrientes y equipos.")
    st.divider()
    st.info("Lienzo interactivo de diseño en desarrollo.")

# ---------------------------------------------------------
# PIE DE PÁGINA
# ---------------------------------------------------------
st.divider()
st.markdown(
    """
    <div style="text-align: center; padding: 10px; color: #666666; font-size: 14px;">
        <p style="margin-bottom: 2px;">Creado por grupo DiRoPS</p>
        <p style="font-size: 12px; margin-top: 0px; color: #444444;">Always</p>
    </div>
    """,
    unsafe_allow_html=True
)
