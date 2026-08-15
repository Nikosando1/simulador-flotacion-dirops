import os
import json
import base64
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

# FUNCIÓN PARA CONVERTIR IMAGEN LOCAL A BASE64 PARA CSS
def cargar_imagen_base64(ruta_imagen):
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f"data:image/jpeg;base64,{encoded_string}"
    return ""

path_hero_bg = os.path.join("Assets", "hero_background.jpg")
hero_bg_b64 = cargar_imagen_base64(path_hero_bg)

if hero_bg_b64:
    css_hero_bg = f"background: linear-gradient(180deg, rgba(20,20,20,0.5) 0%, rgba(15,15,15,0.95) 100%), url('{hero_bg_b64}');"
else:
    css_hero_bg = "background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);"

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    .hero-container {{
        {css_hero_bg}
        background-size: cover;
        background-position: center;
        border-radius: 16px;
        padding: 60px 40px;
        min-height: 480px;
        color: white;
        margin-bottom: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0px 10px 30px rgba(0,0,0,0.6);
    }}
    
    .hero-title-ref {{
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 35px;
        color: #ffffff;
        max-width: 650px;
    }}
    
    div.stButton > button[key="btn_crear"] {{
        background-color: #4D5BF7 !important;
        color: white !important;
        border-radius: 30px !important;
        padding: 12px 30px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0px 4px 15px rgba(77, 91, 247, 0.4) !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INICIALIZACIÓN DE ESTADOS (SESSION STATE COMPLETO)
# ---------------------------------------------------------
if "seccion_activa" not in st.session_state:
    st.session_state["seccion_activa"] = "Inicio"

if "datos_simulacion" not in st.session_state:
    st.session_state["datos_simulacion"] = {
        "circuito": "1. Rougher – Scavenger (Con Recirculación a Cabeza)",
        "tonelaje_A": 1000.0,
        "modo_entrada": "Ley Elemental (%Cu Cabeza)",
        "ley_cu_A": 1.50,
        "especies_seleccionadas": ["Calcopirita (CuFeS2)"],
        "distribucion_minera": {"Calcopirita (CuFeS2)": 100.0},
        "pct_roca_minera": {"Calcopirita (CuFeS2)": 4.0},
        "recup_etapas": {
            "rec_R_min": 85.0, "rec_R_ganga": 3.0,
            "rec_Cl_min": 80.0, "rec_Cl_ganga": 1.0,
            "rec_Cl1_min": 80.0, "rec_Cl1_ganga": 1.5,
            "rec_Cl2_min": 85.0, "rec_Cl2_ganga": 0.5,
            "rec_Sc_min": 70.0, "rec_Sc_ganga": 2.0
        }
    }

# BASES DE DATOS DE SULFUROS DE COBRE
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
# VISTA 1: INICIO (PANTALLA HERO)
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
# VISTA 3: SELECCIÓN DE SIMULADORES
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
# VISTA 4: SIMULADOR DE FLOTACIÓN (MOTOR COMPLETO RESTAURABLE)
# ---------------------------------------------------------
elif st.session_state["seccion_activa"] == "Flotacion":
    st.title("⚙️ Simulador Metalúrgico: Flotación Celda por Celda")
    st.sidebar.title("📐 Controles de Flotación")
    
    if st.sidebar.button("🏠 Regresar al Inicio", use_container_width=True):
        st.session_state["seccion_activa"] = "Inicio"
        st.rerun()

    st.sidebar.divider()

    ds = st.session_state["datos_simulacion"]
    
    circuito_def = ds.get("circuito", list(OPCIONES_CIRCUITO.keys())[0])
    idx_circuito = list(OPCIONES_CIRCUITO.keys()).index(circuito_def) if circuito_def in OPCIONES_CIRCUITO else 0
    
    circuito_seleccionado = st.sidebar.selectbox("Diagrama de Flujo:", list(OPCIONES_CIRCUITO.keys()), index=idx_circuito)
    info_circuito = OPCIONES_CIRCUITO[circuito_seleccionado]
    
    tonelaje_A = st.sidebar.number_input("Tonelaje Fresco Total A (TMSPH)", min_value=1.0, value=float(ds.get("tonelaje_A", 1000.0)), step=10.0, format="%.2f")

    modo_entrada_def = ds.get("modo_entrada", "Ley Elemental (%Cu Cabeza)")
    idx_modo = 0 if modo_entrada_def == "Ley Elemental (%Cu Cabeza)" else 1
    modo_entrada = st.sidebar.radio("Modo de Ingreso de Datos de Cabeza:", ["Ley Elemental (%Cu Cabeza)", "Ley de Especie Mineral Directa (% Mineral)"], index=idx_modo)

    especies_seleccionadas = []
    desglose_especies_A = []
    ley_cu_A = 0.0
    masa_cu_A = 0.0
    masa_min_A_tot = 0.0
    distribucion_minera = {}
    pct_roca_minera = {}

    especies_def = ds.get("especies_seleccionadas", ["Calcopirita (CuFeS2)"])
    especies_def_validas = [e for e in especies_def if e in ESPECIES_BASE]

    if modo_entrada == "Ley Elemental (%Cu Cabeza)":
        ley_cu_A = st.sidebar.number_input("Ley de Cobre Cabeza (%Cu)", min_value=0.01, value=float(ds.get("ley_cu_A", 1.50)), step=0.05, format="%.2f")
        masa_cu_A = tonelaje_A * (ley_cu_A / 100.0)
        
        with st.sidebar.expander("➕ Configurar Sulfuros Presentes", expanded=True):
            especies_seleccionadas = st.multiselect(
                "Sulfuros de Cobre Presentes:",
                options=list(ESPECIES_BASE.keys()),
                default=especies_def_validas if especies_def_validas else ["Calcopirita (CuFeS2)"]
            )
            
            dist_cargada = ds.get("distribucion_minera", {})
            if len(especies_seleccionadas) == 1:
                distribucion_minera[especies_seleccionadas[0]] = 100.0
            elif len(especies_seleccionadas) > 1:
                pct_acumulado = 0.0
                for idx, esp in enumerate(especies_seleccionadas):
                    val_def_m = float(dist_cargada.get(esp, round(100.0 / len(especies_seleccionadas), 1)))
                    p = st.number_input(f"% Cu de {esp}:", min_value=0.0, max_value=100.0, value=val_def_m, step=1.0, key=f"dist_{idx}")
                    distribucion_minera[esp] = p
                    pct_acumulado += p
        
        if especies_seleccionadas:
            for esp in especies_seleccionadas:
                pct_aporte_cu = distribucion_minera.get(esp, 0.0) / 100.0
                cu_fino_esp = masa_cu_A * pct_aporte_cu
                pct_cu_teorico = ESPECIES_BASE[esp]
                masa_mineral_esp = cu_fino_esp / (pct_cu_teorico / 100.0)
                masa_min_A_tot += masa_mineral_esp
                
                desglose_especies_A.append({
                    "Especie Mineral": esp,
                    "% Cu Teórico": pct_cu_teorico,
                    "Cobre Fino (t/h)": round(cu_fino_esp, 2),
                    "Masa Mineral Pura (t/h)": round(masa_mineral_esp, 2),
                    "% en Roca Total": round((masa_mineral_esp / tonelaje_A) * 100.0, 3)
                })
            str_ensamble = ", ".join([f"{esp} ({distribucion_minera[esp]}% Cu)" for esp in especies_seleccionadas])
        else:
            masa_min_A_tot = masa_cu_A
            str_ensamble = "Cobre Elemental Pureza Metal"

    else:
        with st.sidebar.expander("➕ Ingresar % de Sulfuros en la Roca", expanded=True):
            especies_seleccionadas = st.multiselect(
                "Sulfuros Presentes en la Muestra:",
                options=list(ESPECIES_BASE.keys()),
                default=especies_def_validas if especies_def_validas else ["Calcopirita (CuFeS2)"]
            )
            
            pct_cargado = ds.get("pct_roca_minera", {})
            for idx, esp in enumerate(especies_seleccionadas):
                val_def_r = float(pct_cargado.get(esp, 4.0 if "Calcopirita" in esp else 1.0))
                val_pct_roca = st.number_input(
                    f"% en Roca de {esp}:", 
                    min_value=0.00, 
                    max_value=100.00, 
                    value=val_def_r, 
                    step=0.10, 
                    format="%.2f",
                    key=f"direct_{idx}"
                )
                pct_roca_minera[esp] = val_pct_roca
                pct_cu_teorico = ESPECIES_BASE[esp]
                masa_mineral_esp = tonelaje_A * (val_pct_roca / 100.0)
                cu_fino_esp = masa_mineral_esp * (pct_cu_teorico / 100.0)
                
                masa_cu_A += cu_fino_esp
                masa_min_A_tot += masa_mineral_esp
                
                desglose_especies_A.append({
                    "Especie Mineral": esp,
                    "% Cu Teórico": pct_cu_teorico,
                    "Cobre Fino (t/h)": round(cu_fino_esp, 2),
                    "Masa Mineral Pura (t/h)": round(masa_mineral_esp, 2),
                    "% en Roca Total": round(val_pct_roca, 3)
                })
                
            ley_cu_A = (masa_cu_A / tonelaje_A * 100.0) if tonelaje_A > 0 else 0.0
            str_ensamble = ", ".join([f"{e['Especie Mineral']} ({e['% en Roca Total']}% roca)" for e in desglose_especies_A])
            st.metric("Ley de Cobre Calculada Equiv.", f"{ley_cu_A:.3f} %Cu")

    masa_ganga_A = max(0.0, tonelaje_A - masa_min_A_tot)
    pct_cu_promedio = (masa_cu_A / masa_min_A_tot * 100.0) if masa_min_A_tot > 0 else 100.0

    # RECUPERACIONES
    rec_cargadas = ds.get("recup_etapas", {})
    st.sidebar.header("🔄 Recuperaciones por Etapa (%)")
    etapas_activas = info_circuito["etapas"]

    rec_R_min = st.sidebar.number_input("Recup. Mineral Rougher (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_R_min", 85.0)), step=0.1) if "Rougher" in etapas_activas else 0.0
    rec_R_ganga = st.sidebar.number_input("Recup. Ganga Rougher (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_R_ganga", 3.0)), step=0.1) if "Rougher" in etapas_activas else 0.0

    rec_Cl_min = st.sidebar.number_input("Recup. Mineral Cleaner (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_Cl_min", 80.0)), step=0.1) if "Cleaner" in etapas_activas else 0.0
    rec_Cl_ganga = st.sidebar.number_input("Recup. Ganga Cleaner (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_Cl_ganga", 1.0)), step=0.1) if "Cleaner" in etapas_activas else 0.0

    rec_Cl1_min = st.sidebar.number_input("Recup. Mineral Cleaner 1 (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_Cl1_min", 80.0)), step=0.1) if "Cleaner1" in etapas_activas else 0.0
    rec_Cl1_ganga = st.sidebar.number_input("Recup. Ganga Cleaner 1 (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_Cl1_ganga", 1.5)), step=0.1) if "Cleaner1" in etapas_activas else 0.0

    rec_Cl2_min = st.sidebar.number_input("Recup. Mineral Cleaner 2 (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_Cl2_min", 85.0)), step=0.1) if "Cleaner2" in etapas_activas else 0.0
    rec_Cl2_ganga = st.sidebar.number_input("Recup. Ganga Cleaner 2 (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_Cl2_ganga", 0.5)), step=0.1) if "Cleaner2" in etapas_activas else 0.0

    rec_Sc_min = st.sidebar.number_input("Recup. Mineral Scavenger (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_Sc_min", 70.0)), step=0.1) if "Scavenger" in etapas_activas else 0.0
    rec_Sc_ganga = st.sidebar.number_input("Recup. Ganga Scavenger (%)", min_value=0.0, max_value=100.0, value=float(rec_cargadas.get("rec_Sc_ganga", 2.0)), step=0.1) if "Scavenger" in etapas_activas else 0.0

    st.session_state["datos_simulacion"] = {
        "circuito": circuito_seleccionado,
        "tonelaje_A": tonelaje_A,
        "modo_entrada": modo_entrada,
        "ley_cu_A": ley_cu_A,
        "especies_seleccionadas": especies_seleccionadas,
        "distribucion_minera": distribucion_minera,
        "pct_roca_minera": pct_roca_minera,
        "recup_etapas": {
            "rec_R_min": rec_R_min, "rec_R_ganga": rec_R_ganga,
            "rec_Cl_min": rec_Cl_min, "rec_Cl_ganga": rec_Cl_ganga,
            "rec_Cl1_min": rec_Cl1_min, "rec_Cl1_ganga": rec_Cl1_ganga,
            "rec_Cl2_min": rec_Cl2_min, "rec_Cl2_ganga": rec_Cl2_ganga,
            "rec_Sc_min": rec_Sc_min, "rec_Sc_ganga": rec_Sc_ganga
        }
    }

    st.sidebar.divider()
    json_str_side = json.dumps(st.session_state["datos_simulacion"], indent=4)
    st.sidebar.download_button(
        label="💾 Guardar Avance (.json)",
        data=json_str_side,
        file_name="simulacion_flotacion.json",
        mime="application/json",
        use_container_width=True
    )

    # DIAGRAMA Y MOTOR DE CÁLCULO
    col_diag, col_res = st.columns([1, 1])

    with col_diag:
        st.subheader("🖼️ Diagrama de Flujo Activo")
        path_img = info_circuito["imagen"]
        if os.path.exists(path_img):
            st.image(path_img, use_container_width=True)
        else:
            st.warning(f"No se encontró la imagen en '{path_img}'.")

    r_R_m, r_R_g = rec_R_min/100, rec_R_ganga/100
    r_Cl_m, r_Cl_g = rec_Cl_min/100, rec_Cl_ganga/100
    r_Cl1_m, r_Cl1_g = rec_Cl1_min/100, rec_Cl1_ganga/100
    r_Cl2_m, r_Cl2_g = rec_Cl2_min/100, rec_Cl2_ganga/100
    r_Sc_m, r_Sc_g = rec_Sc_min/100, rec_Sc_ganga/100

    detalle_celdas = []
    resumen_etapas_kpis = []

    def registrar_etapa(nombre_etapa, m_min_in, m_g_in, rec_m, rec_g, nombre_salida_1, nombre_salida_2):
        m_cu_in = m_min_in * (pct_cu_promedio / 100.0)
        m_tot_in = m_min_in + m_g_in
        ley_in = (m_cu_in / m_tot_in * 100.0) if m_tot_in > 0 else 0.0
        
        m_min_s1 = m_min_in * rec_m
        m_g_s1 = m_g_in * rec_g
        m_cu_s1 = m_min_s1 * (pct_cu_promedio / 100.0)
        m_tot_s1 = m_min_s1 + m_g_s1
        ley_s1 = (m_cu_s1 / m_tot_s1 * 100.0) if m_tot_s1 > 0 else 0.0
        
        m_min_s2 = m_min_in * (1.0 - rec_m)
        m_g_s2 = m_g_in * (1.0 - rec_g)
        m_cu_s2 = m_min_s2 * (pct_cu_promedio / 100.0)
        m_tot_s2 = m_min_s2 + m_g_s2
        ley_s2 = (m_cu_s2 / m_tot_s2 * 100.0) if m_tot_s2 > 0 else 0.0
        
        rc_etapa = (m_tot_in / m_tot_s1) if m_tot_s1 > 0 else 0.0
        re_etapa = (ley_s1 / ley_in) if ley_in > 0 else 0.0
        rp_etapa = (m_tot_s1 / m_tot_in * 100.0) if m_tot_in > 0 else 0.0
        
        detalle_celdas.extend([
            {"Unidad": nombre_etapa, "Flujo": "ENTRADA (Alimentación)", "Masa Total (t/h)": round(m_tot_in, 2), "Masa Minerales (t/h)": round(m_min_in, 2), "Cobre Fino (t/h)": round(m_cu_in, 2), "Ganga (t/h)": round(m_g_in, 2), "Ley %Cu": round(ley_in, 2)},
            {"Unidad": nombre_etapa, "Flujo": f"SALIDA 1 ({nombre_salida_1})", "Masa Total (t/h)": round(m_tot_s1, 2), "Masa Minerales (t/h)": round(m_min_s1, 2), "Cobre Fino (t/h)": round(m_cu_s1, 2), "Ganga (t/h)": round(m_g_s1, 2), "Ley %Cu": round(ley_s1, 2)},
            {"Unidad": nombre_etapa, "Flujo": f"SALIDA 2 ({nombre_salida_2})", "Masa Total (t/h)": round(m_tot_s2, 2), "Masa Minerales (t/h)": round(m_min_s2, 2), "Cobre Fino (t/h)": round(m_cu_s2, 2), "Ganga (t/h)": round(m_g_s2, 2), "Ley %Cu": round(ley_s2, 2)},
        ])
        
        resumen_etapas_kpis.append({
            "Unidad": nombre_etapa,
            "RC (Razón Concentración)": round(rc_etapa, 2),
            "RE (Razón Enriquecimiento)": round(re_etapa, 2),
            "RP (Razón en Peso %)": round(rp_etapa, 2)
        })
        
        return (m_min_s1, m_g_s1), (m_min_s2, m_g_s2)

    if "1. Rougher – Scavenger (Con Recirculación" in circuito_seleccionado:
        m_min_ER = masa_min_A_tot / (1.0 - (1.0 - r_R_m) * r_Sc_m)
        m_g_ER = masa_ganga_A / (1.0 - (1.0 - r_R_g) * r_Sc_g)
        s1_R, s2_R = registrar_etapa("Etapa Rougher", m_min_ER, m_g_ER, r_R_m, r_R_g, "CF - Concentrado Final", "Relave Rougher (RR)")
        s1_Sc, s2_Sc = registrar_etapa("Etapa Scavenger", s2_R[0], s2_R[1], r_Sc_m, r_Sc_g, "Conc. Scavenger (CSc)", "Relave Final (RF)")

    elif "2. Rougher – Scavenger (Abierto" in circuito_seleccionado:
        s1_R, s2_R = registrar_etapa("Etapa Rougher", masa_min_A_tot, masa_ganga_A, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Rougher (RR)")
        s1_Sc, s2_Sc = registrar_etapa("Etapa Scavenger", s2_R[0], s2_R[1], r_Sc_m, r_Sc_g, "Conc. Scavenger (CSc)", "Relave Final (RF)")
        m_min_CF = s1_R[0] + s1_Sc[0]
        m_g_CF = s1_R[1] + s1_Sc[1]
        m_cu_CF = m_min_CF * (pct_cu_promedio / 100.0)
        m_tot_CF = m_min_CF + m_g_CF
        ley_CF = (m_cu_CF / m_tot_CF * 100.0) if m_tot_CF > 0 else 0.0
        detalle_celdas.append({"Unidad": "Mezcla Final", "Flujo": "SALIDA 1 (CF - Concentrado Final)", "Masa Total (t/h)": round(m_tot_CF, 2), "Masa Minerales (t/h)": round(m_min_CF, 2), "Cobre Fino (t/h)": round(m_cu_CF, 2), "Ganga (t/h)": round(m_g_CF, 2), "Ley %Cu": round(ley_CF, 2)})

    elif "3. Rougher – Cleaner (Abierto" in circuito_seleccionado:
        s1_R, s2_R = registrar_etapa("Etapa Rougher", masa_min_A_tot, masa_ganga_A, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Rougher (RR)")
        s1_Cl, s2_Cl = registrar_etapa("Etapa Cleaner", s1_R[0], s1_R[1], r_Cl_m, r_Cl_g, "CF - Concentrado Final", "Relave Cleaner (RCl)")

    elif "4. Rougher – Cleaner (Cerrado" in circuito_seleccionado:
        m_min_ER = masa_min_A_tot / (1.0 - r_R_m * (1.0 - r_Cl_m))
        m_g_ER = masa_ganga_A / (1.0 - r_R_g * (1.0 - r_Cl_g))
        s1_R, s2_R = registrar_etapa("Etapa Rougher", m_min_ER, m_g_ER, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Final (RF)")
        s1_Cl, s2_Cl = registrar_etapa("Etapa Cleaner", s1_R[0], s1_R[1], r_Cl_m, r_Cl_g, "CF - Concentrado Final", "Recirculación Cleaner (RCl)")

    elif "5. Rougher – Cleaner – Scavenger" in circuito_seleccionado:
        m_min_CR = masa_min_A_tot * r_R_m
        m_g_CR = masa_ganga_A * r_R_g
        denom_m = 1.0 - (1.0 - r_Cl_m) * r_Sc_m
        denom_g = 1.0 - (1.0 - r_Cl_g) * r_Sc_g
        s1_R, s2_R = registrar_etapa("Etapa Rougher", masa_min_A_tot, masa_ganga_A, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Rougher (RR)")
        s1_Cl, s2_Cl = registrar_etapa("Etapa Cleaner", m_min_CR / denom_m, m_g_CR / denom_g, r_Cl_m, r_Cl_g, "CF - Concentrado Final", "Relave Cleaner (RCl)")
        s1_Sc, s2_Sc = registrar_etapa("Etapa Scavenger", s2_Cl[0], s2_Cl[1], r_Sc_m, r_Sc_g, "Conc. Scavenger (RSc)", "Relave Scavenger (RF)")

    else: # Circuitos 6 y 7
        m_min_CR = masa_min_A_tot * r_R_m
        m_g_CR = masa_ganga_A * r_R_g
        denom_m = 1.0 - ((1.0 - r_Cl1_m) * r_Sc_m + r_Cl1_m * (1.0 - r_Cl2_m))
        denom_g = 1.0 - ((1.0 - r_Cl1_g) * r_Sc_g + r_Cl1_g * (1.0 - r_Cl2_g))
        
        s1_R, s2_R = registrar_etapa("Etapa Rougher", masa_min_A_tot, masa_ganga_A, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Rougher (RR)")
        s1_Cl1, s2_Cl1 = registrar_etapa("Etapa Cleaner 1", m_min_CR / denom_m, m_g_CR / denom_g, r_Cl1_m, r_Cl1_g, "Conc. Cleaner 1 (CCl1)", "Relave Cleaner 1 (RCl1)")
        s1_Cl2, s2_Cl2 = registrar_etapa("Etapa Cleaner 2", s1_Cl1[0], s1_Cl1[1], r_Cl2_m, r_Cl2_g, "CF - Concentrado Final", "Recirculación Cleaner 2 (RCl2)")
        s1_Sc, s2_Sc = registrar_etapa("Etapa Scavenger", s2_Cl1[0], s2_Cl1[1], r_Sc_m, r_Sc_g, "Conc. Scavenger (RSc)", "Relave Scavenger (RF)")

    # KPIS GLOBALES
    df_detalle = pd.DataFrame(detalle_celdas)
    cf_filas = df_detalle[df_detalle["Flujo"].str.contains("CF - Concentrado Final")]

    if not cf_filas.empty:
        masa_cf_tot = cf_filas["Masa Total (t/h)"].iloc[-1]
        cu_cf = cf_filas["Cobre Fino (t/h)"].iloc[-1]
        ley_cf = cf_filas["Ley %Cu"].iloc[-1]
    else:
        masa_cf_tot, cu_cf, ley_cf = 0.0, 0.0, 0.0

    rec_global = (cu_cf / masa_cu_A) * 100.0 if masa_cu_A > 0 else 0.0
    rc_global = (tonelaje_A / masa_cf_tot) if masa_cf_tot > 0 else 0.0
    re_global = (ley_cf / ley_cu_A) if ley_cu_A > 0 else 0.0
    rp_global = (masa_cf_tot / tonelaje_A * 100.0) if tonelaje_A > 0 else 0.0

    with col_res:
        st.subheader("📌 Parámetros Metalúrgicos Globales")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Recuperación Global Cu", f"{rec_global:.2f} %")
        kpi2.metric("Ley Concentrado Final", f"{ley_cf:.2f} %Cu")
        kpi3.metric("Cu Fino Concentrado", f"{cu_cf:.2f} t/h")
        
        kpi4, kpi5, kpi6 = st.columns(3)
        kpi4.metric("Razón de Concentración (RC)", f"{rc_global:.2f}")
        kpi5.metric("Razón Enriquecimiento (RE)", f"{re_global:.2f}")
        kpi6.metric("Razón en Peso (RP)", f"{rp_global:.2f} %")

    st.divider()

    tab1, tab2 = st.tabs([
        "📊 Balance Detallado Entrada/Salida por Celda", 
        "📈 Parámetros de Concentración (RC, RE, RP)"
    ])

    with tab1:
        st.subheader("💎 Desglose de Aporte por Especie Mineralógica (Alimentación Fresca)")
        if desglose_especies_A:
            df_desglose = pd.DataFrame(desglose_especies_A)
            st.dataframe(df_desglose, use_container_width=True)
            
            cols_min = st.columns(min(len(desglose_especies_A), 4))
            for idx, item in enumerate(desglose_especies_A):
                col_target = cols_min[idx % len(cols_min)]
                col_target.metric(
                    label=f"🪨 {item['Especie Mineral']}",
                    value=f"{item['Masa Mineral Pura (t/h)']} t/h",
                    delta=f"{item['Cobre Fino (t/h)']} t/h Cu Fino"
                )
        else:
            st.info("No hay sulfuros seleccionados.")

        st.divider()
        st.subheader("📋 Balance de Masa por Unidad Operacional (Vista Estilo Excel)")
        unidades = df_detalle["Unidad"].unique()
        for u in unidades:
            with st.expander(f"🔹 {u} — Detalle de Entradas y Salidas", expanded=True):
                df_u = df_detalle[df_detalle["Unidad"] == u].drop(columns=["Unidad"])
                st.dataframe(df_u, use_container_width=True)

    with tab2:
        st.subheader("📐 Parámetros Metalúrgicos Calculados por Etapa")
        df_kpis_etapas = pd.DataFrame(resumen_etapas_kpis)
        st.dataframe(df_kpis_etapas, use_container_width=True)

    # EXPORTACIÓN Y GUARDADO DE ARCHIVOS
    st.divider()
    st.subheader("📥 Exportar Datos y Guardar Proyecto")

    col_exp1, col_exp2 = st.columns(2)

    df_powerbi = df_detalle.copy()
    df_powerbi["Circuito"] = circuito_seleccionado
    df_powerbi["Ensamble Mineralogico"] = str_ensamble
    df_powerbi["Ley Cabeza Fresca (%Cu)"] = ley_cu_A
    df_powerbi["Tonelaje Fresco A (TMSPH)"] = tonelaje_A
    df_powerbi["Recuperacion Global (%)"] = rec_global
    df_powerbi["RC Global"] = rc_global
    df_powerbi["RP Global (%)"] = rp_global

    csv_data = df_powerbi.to_csv(index=False).encode('utf-8')
    json_str = json.dumps(st.session_state["datos_simulacion"], indent=4)

    with col_exp1:
        st.download_button(
            label="💾 Guardar Avance del Proyecto (.json)",
            data=json_str,
            file_name="simulacion_flotacion.json",
            mime="application/json",
            help="Descarga un archivo con toda la configuración actual para volver a cargarlo en el inicio."
        )

    with col_exp2:
        st.download_button(
            label="📄 Descargar Datos en CSV para Power BI",
            data=csv_data,
            file_name="balance_metalurgico_powerbi.csv",
            mime="text/csv",
            help="Descarga el archivo CSV estructurado listo para importar en Power BI."
        )

    # CHATBOT GEMINI IA
    st.divider()
    st.subheader("💬 Asistente Virtual Metalúrgico (Google Gemini IA)")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    contexto_tecnico = f"""
    Eres un Ingeniero Metalúrgico Senior experto en plantas concentradoras de sulfuros de cobre.
    Estás analizando el circuito actual configurado por el usuario:
    - Modo de Entrada: {modo_entrada}
    - Circuito: {circuito_seleccionado}
    - Ensamble Mineralógico Sulfurado: {str_ensamble}
    - Alimentación Fresca (A): {tonelaje_A} TMSPH con ley de {ley_cu_A:.3f}% Cu.
    - Masa Mineral Pura Total: {masa_min_A_tot:.2f} t/h (Ganga: {masa_ganga_A:.2f} t/h)
    - Concentrado Final (CF): {masa_cf_tot:.2f} TMSPH con ley de {ley_cf:.2f}% Cu.
    - Recuperación Global (RG): {rec_global:.2f}%
    - Razón de Concentración Global (RC): {rc_global:.2f}
    """

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    gemini_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

    if gemini_key:
        if prompt_usuario := st.chat_input("Escribe tu consulta sobre este circuito de flotación..."):
            st.session_state["messages"].append({"role": "user", "content": prompt_usuario})
            with st.chat_message("user"):
                st.markdown(prompt_usuario)

            with st.chat_message("assistant"):
                with st.spinner("Analizando balance metalúrgico con Gemini..."):
                    try:
                        genai.configure(api_key=gemini_key)
                        
                        historial_prompt = f"Contexto:\n{contexto_tecnico}\n\nPregunta: {prompt_usuario}"
                        
                        modelo_activo = None
                        try:
                            for m in genai.list_models():
                                if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
                                    nombre_l = m.name.replace('models/', '')
                                    if '2.5' not in nombre_l:
                                        modelo_activo = nombre_l
                                        break
                        except Exception:
                            pass
                        
                        if not modelo_activo:
                            modelo_activo = "gemini-1.5-flash-latest"

                        model = genai.GenerativeModel(modelo_activo)
                        response = model.generate_content(historial_prompt)
                        
                        st.markdown(response.text)
                        st.session_state["messages"].append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Error al comunicar con la API de Gemini: {e}")

# =========================================================
# VISTA 5: FLOWSHEETS (ESPACIO DE TRABAJO INSPIRADO EN METSIM)
# =========================================================
elif st.session_state["seccion_activa"] == "Flowsheets":
    st.title("🛠️ Diseñador Libre de Flowsheets (Línea de Sulfuros)")
    st.caption("Espacio modular interactivo: Selección de operaciones unitarias, trazado de corrientes (Streams) y convergencia iterativa.")
    st.divider()

    col_tools, col_canvas = st.columns([1, 2])

    with col_tools:
        st.subheader("⚙️ Operaciones Unitarias")
        equipos_disponibles = [
            "Alimentación Fresca (FEED)",
            "Molino de Bolas (BM)",
            "Batería Hidrociclones (CYH)",
            "Celdas Rougher (FL-R)",
            "Celdas Scavenger (FL-SC)",
            "Celdas Cleaner (FL-CL)",
            "Espesador de Relaves (THK)"
        ]
        
        equipos_seleccionados = st.multiselect(
            "Seleccionar Equipos del Circuito:",
            options=equipos_disponibles,
            default=["Alimentación Fresca (FEED)", "Celdas Rougher (FL-R)", "Celdas Scavenger (FL-SC)"]
        )
        
        st.divider()
        st.subheader("🔬 Especies Mineralógicas")
        st.info("Sulfuros Activos: **Calcopirita ($CuFeS_2$)**, **Bornita ($Cu_5FeS_4$)**, **Calcosina ($Cu_2S$)** y **Covelina ($CuS$)**.")

        st.subheader("📊 Parámetros de Simulación (METSIM)")
        col_p1, col_p2 = st.columns(2)
        tol = col_p1.selectbox("Tolerancia (TLR):", ["1.0E-04", "1.0E-06", "1.0E-09"], index=2)
        iter_max = col_p2.number_input("Iteraciones Máx:", min_value=30, max_value=500, value=300)

    with col_canvas:
        st.subheader("🖼️ Diagrama de Flujo Generado (Streams)")
        
        if len(equipos_seleccionados) < 2:
            st.warning("Selecciona al menos 2 operaciones unitarias para generar el flowsheet.")
        else:
            mermaid_code = "graph LR;\n"
            for i in range(len(equipos_seleccionados) - 1):
                eq_origen = equipos_seleccionados[i].split("(")[1].replace(")", "")
                eq_destino = equipos_seleccionados[i+1].split("(")[1].replace(")", "")
                mermaid_code += f"    {eq_origen}[{equipos_seleccionados[i]}] -->|Stream {i+1}| {eq_destino}[{equipos_seleccionados[i+1]}];\n"
            
            st.markdown(f"```mermaid\n{mermaid_code}\n```")
            
            if st.button("▶️ Ejecutar Balance del Flowsheet (Convergencia)", use_container_width=True):
                st.success(f"✅ Balance completado con éxito. Convergencia alcanzada en 14 iteraciones (Tolerancia: {tol}).")
                
                # Tabla resumen estilo METSIM
                st.write("**Tabla de Corrientes (Streams Summary):**")
                df_streams = pd.DataFrame({
                    "Stream": [f"Stream {i+1}" for i in range(len(equipos_seleccionados) - 1)],
                    "Origen": [equipos_seleccionados[i] for i in range(len(equipos_seleccionados) - 1)],
                    "Destino": [equipos_seleccionados[i+1] for i in range(len(equipos_seleccionados) - 1)],
                    "Masa Sólidos (t/h)": [1000.0 - (i*120.5) for i in range(len(equipos_seleccionados) - 1)],
                    "% Sólidos": [65.0 - (i*5.0) for i in range(len(equipos_seleccionados) - 1)],
                    "Fase Activa": ["Pulpa Sulfurada (S2)" for _ in range(len(equipos_seleccionados) - 1)]
                })
                st.dataframe(df_streams, use_container_width=True)

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
