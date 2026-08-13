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
    page_title="Plataforma Metalúrgica DiRoPS",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado inspirado en la interfaz de referencia (Limpia y Corporativa)
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 40px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 10px;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        color: #cfd8dc;
        margin-bottom: 25px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
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
        "circuito": "1. Rougher – Scavenger (Con Recirculación a Cabeza)",
        "modo_entrada": "Ley Elemental (%Cu Cabeza)"
    }

# ---------------------------------------------------------
# BASE DE DATOS DE SULFUROS Y PROPIEDADES
# ---------------------------------------------------------
ESPECIES_BASE = {
    "Calcopirita (CuFeS2)": 34.63,
    "Bornita (Cu5FeS4)": 63.31,
    "Calcosina (Cu2S)": 79.85,
    "Covelina (CuS)": 66.47
}

INFO_MINERALES = {
    "Calcopirita": {
        "formula": "CuFeS2",
        "ley_cu": 34.63,
        "tipo": "Sulfuro Primario",
        "imagen_nombres": ["Calcopirita.jpg", "calcopirita.jpg", "Calcopirita.png", "calcopirita.png"],
        "desc": "El sulfuro de cobre más abundante en yacimientos porfídicos. Presenta respuesta óptima a la flotación colectiva con xantatos."
    },
    "Bornita": {
        "formula": "Cu5FeS4",
        "ley_cu": 63.31,
        "tipo": "Sulfuro Secundario/Primario",
        "imagen_nombres": ["Bornita.jpg", "bornita.jpg", "Bornita.png", "bornita.png"],
        "desc": "Conocida como 'peacock ore' por sus pátinas iridiscentes. Posee un elevado contenido metálico de Cobre."
    },
    "Calcosina": {
        "formula": "Cu2S",
        "ley_cu": 79.85,
        "tipo": "Sulfuro Secundario",
        "imagen_nombres": ["Calcosina.jpg", "calcosina.jpg", "Calcosina.png", "calcosina.png"],
        "desc": "Clave en zonas de enriquecimiento supergeno. Es el sulfuro con mayor porcentaje teórico de Cobre."
    },
    "Covelina": {
        "formula": "CuS",
        "ley_cu": 66.47,
        "tipo": "Sulfuro Secundario",
        "imagen_nombres": ["Covelina.jpg", "covelina.jpg", "Covelina.png", "covelina.png"],
        "desc": "De color azul índigo característico. Flota con alta cinética en circuitos de flotación selectiva."
    }
}

OPCIONES_CIRCUITO = {
    "1. Rougher – Scavenger (Con Recirculación a Cabeza)": {
        "imagen": "Assets/Diagrama_Rougher_Scavenger1.png",
        "etapas": ["Rougher", "Scavenger"]
    },
    "2. Rougher – Scavenger (Abierto / En Serie)": {
        "imagen": "Assets/Diagrama_Rougher_Scavenger2.png",
        "etapas": ["Rougher", "Scavenger"]
    },
    "3. Rougher – Cleaner (Abierto / En Serie)": {
        "imagen": "Assets/Diagrama_Rougher_Cleaner1.png",
        "etapas": ["Rougher", "Cleaner"]
    },
    "4. Rougher – Cleaner (Cerrado a Cabeza)": {
        "imagen": "Assets/Diagrama_Rougher_Cleaner2.png",
        "etapas": ["Rougher", "Cleaner"]
    },
    "5. Rougher – Cleaner – Scavenger (Recirculación a Cleaner)": {
        "imagen": "Assets/Diagrama_Rougher_Cleaner_Scavenger1.png",
        "etapas": ["Rougher", "Cleaner", "Scavenger"]
    },
    "6. R – Cl1 – Cl2 – Sc (Doble Recirculación A)": {
        "imagen": "Assets/Diagrama_Rougher_Cleaner_Cleaner2_Scavenger1.png",
        "etapas": ["Rougher", "Cleaner1", "Cleaner2", "Scavenger"]
    },
    "7. R – Cl1 – Cl2 – Sc (Doble Recirculación B)": {
        "imagen": "Assets/Diagrama_Rougher_Cleaner_Cleaner2_Scavenger2.png",
        "etapas": ["Rougher", "Cleaner1", "Cleaner2", "Scavenger"]
    }
}

# ---------------------------------------------------------
# BARRA DE NAVEGACIÓN PRINCIPAL (SUPERIOR & LATERAL)
# ---------------------------------------------------------
st.sidebar.title("⚙️ Portal Metalúrgico")

# Menú Navegación
nav_opcion = st.sidebar.radio(
    "Navegación:",
    [
        "🏠 Inicio",
        "👥 Quienes Somos",
        "📊 Simuladores por Área",
        "🛠️ Diseñador de Flowsheets",
        "💎 Enciclopedia de Sulfuros"
    ]
)

st.sidebar.divider()

# Cargar/Guardar Proyectos en la barra lateral
with st.sidebar.expander("📁 Gestión de Archivos (.json)", expanded=False):
    archivo_subido_side = st.file_uploader("Cargar simulación (.json):", type=["json"], key="side_uploader")
    if archivo_subido_side:
        try:
            datos_cargados = json.load(archivo_subido_side)
            st.session_state["datos_simulacion"].update(datos_cargados)
            st.success("¡Simulación cargada exitosamente!")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

    # Descargar estado actual
    json_str = json.dumps(st.session_state["datos_simulacion"], indent=4)
    st.download_button(
        label="💾 Exportar Avance Actual (.json)",
        data=json_str,
        file_name="proyecto_dirops.json",
        mime="application/json"
    )

# =========================================================
# VISTA 1: INICIO / PANTALLA HERO CLEAN
# =========================================================
if nav_opcion == "🏠 Inicio":
    st.markdown("""
        <div class="main-header">
            <div class="hero-title">Plataforma de Simulación Metalúrgica</div>
            <div class="hero-subtitle">Modelamiento de Procesos, Balance de Masas Multi-Mineralógico y Asistencia IA</div>
        </div>
    """, unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        with st.container(border=True):
            st.subheader("➕ Crear Proyecto Desde Cero")
            st.write("Inicia una nueva simulación configurando los parámetros de alimentación, especies sulfuradas y arquitectura del circuito.")
            if st.button("🚀 Comenzar Nueva Simulación", use_container_width=True):
                st.session_state["seccion_activa"] = "Flotacion"
                st.rerun()

    with col_btn2:
        with st.container(border=True):
            st.subheader("📂 Cargar Avance Existente")
            st.write("Arrastra o selecciona un archivo de simulación (`.json`) para restaurar instantáneamente el flujo de trabajo.")
            
            archivo_droppeado = st.file_uploader("Arrastra aquí tu archivo (.json):", type=["json"], key="hero_uploader")
            if archivo_droppeado:
                try:
                    datos = json.load(archivo_droppeado)
                    st.session_state["datos_simulacion"].update(datos)
                    st.success("¡Proyecto cargado correctamente!")
                    if st.button("▶️ Abrir Simulación Cargada", use_container_width=True):
                        st.session_state["seccion_activa"] = "Flotacion"
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al procesar archivo: {e}")

    st.divider()
    st.markdown("### 🛠️ Módulos de la Plataforma")
    
    col_mod1, col_mod2, col_mod3 = st.columns(3)
    col_mod1.info("📊 **Simulador de Flotación:** Balance celda por celda y optimización.")
    col_mod2.info("🛠️ **Flowsheets Libre:** Diseñador de esquemas y matrices de recirculación.")
    col_mod3.info("💎 **Enciclopedia:** Caracterización estequiométrica de sulfuros.")

# =========================================================
# VISTA 2: QUIENES SOMOS (RESERVADO)
# =========================================================
elif nav_opcion == "👥 Quienes Somos":
    st.title("👥 Quiénes Somos")
    st.caption("Equipo de Desarrollo y Visión del Proyecto")
    st.divider()
    
    st.info("ℹ️ **Espacio Reservado:** Próximamente se incluirá aquí la información institucional, visión del equipo DiRoPS y colaboradores académicos/industriales.")

# =========================================================
# VISTA 3: SIMULADORES POR ÁREA/CATEGORÍA
# =========================================================
elif nav_opcion == "📊 Simuladores por Área":
    st.title("📊 Simuladores Específicos por Área Metalúrgica")
    st.caption("Selecciona la etapa de procesamiento que deseas modelar:")
    st.divider()

    # Selector de Área
    categoria_sel = st.selectbox(
        "Selecciona el Área del Proceso:",
        [
            "✨ Concentración / Flotación de Espumas (ACTIVO)",
            "🔒 Conminución y Molienda (Próximamente)",
            "🔒 Hidrometallurgia y Lixiviación (Próximamente)",
            "🔒 Manejo de Sólidos / Filtrado y Espesamiento (Próximamente)",
            "🔒 Pirometallurgia, Fundición y Refinación (Próximamente)"
        ]
    )

    if "Concentración / Flotación" in categoria_sel:
        st.success("✅ Módulo activo y listo para simular.")
        
        # ---------------------------------------------------------
        # LÓGICA DEL SIMULADOR DE FLOTACIÓN (MÓDULO DESARROLLADO)
        # ---------------------------------------------------------
        st.sidebar.header("📐 Configuración del Circuito")

        circuito_seleccionado = st.sidebar.selectbox(
            "Selecciona el Diagrama de Flujo:",
            list(OPCIONES_CIRCUITO.keys()),
            index=list(OPCIONES_CIRCUITO.keys()).index(st.session_state["datos_simulacion"].get("circuito", list(OPCIONES_CIRCUITO.keys())[0]))
        )

        info_circuito = OPCIONES_CIRCUITO[circuito_seleccionado]

        st.sidebar.header("📊 Datos de Alimentación Fresca (A)")
        tonelaje_A = st.sidebar.number_input(
            "Tonelaje Fresco Total A (TMSPH)", 
            min_value=1.0, 
            value=float(st.session_state["datos_simulacion"].get("tonelaje_A", 1000.0)), 
            step=10.0, 
            format="%.2f"
        )

        modo_entrada = st.sidebar.radio(
            "Modo de Ingreso de Datos de Cabeza:",
            ["Ley Elemental (%Cu Cabeza)", "Ley de Especie Mineral Directa (% Mineral)"]
        )

        especies_seleccionadas = []
        desglose_especies_A = []
        ley_cu_A = 0.0
        masa_cu_A = 0.0
        masa_min_A_tot = 0.0

        if modo_entrada == "Ley Elemental (%Cu Cabeza)":
            ley_cu_A = st.sidebar.number_input(
                "Ley de Cobre Cabeza (%Cu)", 
                min_value=0.01, 
                value=float(st.session_state["datos_simulacion"].get("ley_cu_A", 1.50)), 
                step=0.05, 
                format="%.2f"
            )
            masa_cu_A = tonelaje_A * (ley_cu_A / 100.0)
            
            with st.sidebar.expander("➕ Configurar Sulfuros Presentes", expanded=True):
                especies_seleccionadas = st.multiselect(
                    "Sulfuros de Cobre Presentes:",
                    options=list(ESPECIES_BASE.keys()),
                    default=["Calcopirita (CuFeS2)"]
                )
                
                distribucion_minera = {}
                if len(especies_seleccionadas) == 1:
                    distribucion_minera[especies_seleccionadas[0]] = 100.0
                elif len(especies_seleccionadas) > 1:
                    pct_acumulado = 0.0
                    for idx, esp in enumerate(especies_seleccionadas):
                        val_def = round(100.0 / len(especies_seleccionadas), 1)
                        p = st.number_input(f"% Cu de {esp}:", min_value=0.0, max_value=100.0, value=val_def, step=1.0, key=f"dist_{idx}")
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
                    default=["Calcopirita (CuFeS2)"]
                )
                
                for idx, esp in enumerate(especies_seleccionadas):
                    val_pct_roca = st.number_input(
                        f"% en Roca de {esp}:", 
                        min_value=0.00, 
                        max_value=100.00, 
                        value=4.00 if "Calcopirita" in esp else 1.00, 
                        step=0.10, 
                        format="%.2f",
                        key=f"direct_{idx}"
                    )
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

        st.sidebar.header("🔄 Recuperaciones por Etapa (%)")
        etapas_activas = info_circuito["etapas"]

        rec_R_min = st.sidebar.number_input("Recup. Mineral Rougher (%)", min_value=0.0, max_value=100.0, value=85.0, step=0.1) if "Rougher" in etapas_activas else 0.0
        rec_R_ganga = st.sidebar.number_input("Recup. Ganga Rougher (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.1) if "Rougher" in etapas_activas else 0.0

        rec_Cl_min = st.sidebar.number_input("Recup. Mineral Cleaner (%)", min_value=0.0, max_value=100.0, value=80.0, step=0.1) if "Cleaner" in etapas_activas else 0.0
        rec_Cl_ganga = st.sidebar.number_input("Recup. Ganga Cleaner (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1) if "Cleaner" in etapas_activas else 0.0

        rec_Cl1_min = st.sidebar.number_input("Recup. Mineral Cleaner 1 (%)", min_value=0.0, max_value=100.0, value=80.0, step=0.1) if "Cleaner1" in etapas_activas else 0.0
        rec_Cl1_ganga = st.sidebar.number_input("Recup. Ganga Cleaner 1 (%)", min_value=0.0, max_value=100.0, value=1.5, step=0.1) if "Cleaner1" in etapas_activas else 0.0

        rec_Cl2_min = st.sidebar.number_input("Recup. Mineral Cleaner 2 (%)", min_value=0.0, max_value=100.0, value=85.0, step=0.1) if "Cleaner2" in etapas_activas else 0.0
        rec_Cl2_ganga = st.sidebar.number_input("Recup. Ganga Cleaner 2 (%)", min_value=0.0, max_value=100.0, value=0.5, step=0.1) if "Cleaner2" in etapas_activas else 0.0

        rec_Sc_min = st.sidebar.number_input("Recup. Mineral Scavenger (%)", min_value=0.0, max_value=100.0, value=70.0, step=0.1) if "Scavenger" in etapas_activas else 0.0
        rec_Sc_ganga = st.sidebar.number_input("Recup. Ganga Scavenger (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1) if "Scavenger" in etapas_activas else 0.0

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

        # CÁLCULOS SEGÚN CIRCUITO
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
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            
                            historial_prompt = f"Contexto:\n{contexto_tecnico}\n\nPregunta: {prompt_usuario}"
                            response = model.generate_content(historial_prompt)
                            
                            st.markdown(response.text)
                            st.session_state["messages"].append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"Error al comunicar con la API de Gemini: {e}")

    else:
        st.warning("⚠️ Esta área de simulación aún se encuentra en desarrollo. Por favor selecciona el simulador de Flotación de Espumas.")

# =========================================================
# VISTA 4: DISEÑADOR DE FLOWSHEETS LIBRE
# =========================================================
elif nav_opcion == "🛠️ Diseñador de Flowsheets":
    st.title("🛠️ Diseñador de Flowsheets y Diagramas Libres")
    st.caption("Crea arquitecturas personalizadas interconectando unidades operacionales.")
    st.divider()

    col_b1, col_b2 = st.columns([1, 1])

    with col_b1:
        num_celdas = st.slider("Número de Unidades Operacionales:", min_value=1, max_value=6, value=3)
        nombres_celdas = [f"Celda_{i+1}" for i in range(num_celdas)]

    with col_b2:
        st.write("**Vista Previa del Diagrama Interconectado:**")
        graph_code = "graph TD;\n    Alimentacion --> " + nombres_celdas[0] + ";\n"
        for i in range(num_celdas - 1):
            graph_code += f"    {nombres_celdas[i]} -- Concentrado --> {nombres_celdas[i+1]};\n"
        graph_code += f"    {nombres_celdas[-1]} --> Concentrado_Final;\n"

        st.markdown(f"```mermaid\n{graph_code}\n```")

# =========================================================
# VISTA 5: ENCICLOPEDIA DE SULFUROS
# =========================================================
elif nav_opcion == "💎 Enciclopedia de Sulfuros":
    st.title("💎 Enciclopedia de Sulfuros de Cobre")
    st.caption("Propiedades químicas, leyes teóricas estequiométricas y muestras minerales.")
    st.divider()

    cols = st.columns(4)
    for idx, (nombre, datos) in enumerate(INFO_MINERALES.items()):
        col_target = cols[idx % 4]
        
        path_imagen_encontrada = None
        for pos_nombre in datos["imagen_nombres"]:
            pos_path = os.path.join("Assets", "Minerales", pos_nombre)
            if os.path.exists(pos_path):
                path_imagen_encontrada = pos_path
                break
                
        with col_target:
            with st.container(border=True):
                if path_imagen_encontrada:
                    st.image(path_imagen_encontrada, use_container_width=True)
                else:
                    st.markdown("🖼️ *(Foto no encontrada)*")
                    
                st.markdown(f"### {nombre}")
                st.caption(f"**Fórmula:** `{datos['formula']}`")
                st.markdown(f"**Tipo:** {datos['tipo']}")
                st.metric("Ley Cu Teórica", f"{datos['ley_cu']}%")
                st.caption(datos["desc"])

# ---------------------------------------------------------
# PIE DE PÁGINA
# ---------------------------------------------------------
st.divider()
st.markdown(
    """
    <div style="text-align: center; padding: 10px; color: #888888;">
        <h4 style="margin-bottom: 2px;">Creado por grupo DiRoPS</h4>
        <p style="font-size: 14px; margin-top: 0px;">Always</p>
    </div>
    """,
    unsafe_allow_html=True
)
