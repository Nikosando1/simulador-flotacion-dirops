import os
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA WEB
# ---------------------------------------------------------
st.set_page_config(
    page_title="Simulador Metalúrgico IA Multi-Especie",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Simulador Metalúrgico: Balance Multi-Mineralógico Celda por Celda")
st.caption("Herramienta de Procesamiento de Minerales con Selección Flexible de Especies y Exportación a Power BI")

# Base de Datos de Especies Mineralógicas (% Cu teórico según composición estequiométrica)
ESPECIES_BASE = {
    "Calcopirita (CuFeS2)": 34.63,
    "Bornita (Cu5FeS4)": 63.31,
    "Calcosina (Cu2S)": 79.85,
    "Covelina (CuS)": 66.47,
    "Malaquita (Cu2CO3(OH)2)": 57.48,
    "Azurita (Cu3(CO3)2(OH)2)": 55.31,
    "Crisocola (CuSiO3·2H2O)": 36.16
}

# ---------------------------------------------------------
# 1. SELECCIÓN DE ARQUITECTURA DE CIRCUITO
# ---------------------------------------------------------
st.sidebar.header("📐 Configuración del Circuito")

opciones_circuito = {
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

circuito_seleccionado = st.sidebar.selectbox(
    "Selecciona el Diagrama de Flujo:",
    list(opciones_circuito.keys())
)

info_circuito = opciones_circuito[circuito_seleccionado]

# ---------------------------------------------------------
# 2. ENTRADA DE DATOS Y ENSAMBLE MINERALÓGICO FLEXIBLE
# ---------------------------------------------------------
st.sidebar.header("📊 Datos de Alimentación Fresca (A)")
tonelaje_A = st.sidebar.number_input("Tonelaje Fresco Total A (TMSPH)", min_value=1.0, value=1000.0, step=10.0, format="%.2f")
ley_cu_A = st.sidebar.number_input("Ley de Cobre Cabeza (%Cu)", min_value=0.01, value=1.50, step=0.05, format="%.2f")

with st.sidebar.expander("➕ Configurar Especies Mineralógicas (Multi-Selección)", expanded=True):
    st.caption("Selecciona una o más especies mineralógicas. Si no seleccionas ninguna, el balance se calculará puramente elemental (%Cu + Ganga).")
    especies_seleccionadas = st.multiselect(
        "Minerales de Cobre Presentes:",
        options=list(ESPECIES_BASE.keys()),
        default=["Calcopirita (CuFeS2)"]
    )
    
    distribucion_minera = {}
    if len(especies_seleccionadas) == 1:
        distribucion_minera[especies_seleccionadas[0]] = 100.0
        st.info(f"100% del Cobre asignado a {especies_seleccionadas[0]}")
    elif len(especies_seleccionadas) > 1:
        st.caption("Distribución del Cobre entre los minerales seleccionados (% sobre el Cobre total):")
        pct_acumulado = 0.0
        for idx, esp in enumerate(especies_seleccionadas):
            val_def = round(100.0 / len(especies_seleccionadas), 1)
            p = st.number_input(f"% del Cu aportado por {esp}:", min_value=0.0, max_value=100.0, value=val_def, step=1.0, key=f"dist_{idx}")
            distribucion_minera[esp] = p
            pct_acumulado += p
        
        if abs(pct_acumulado - 100.0) > 0.01:
            st.warning(f"⚠️ La suma de las distribuciones es {pct_acumulado:.1f}%. Debe sumar exactamente 100.0%.")

st.sidebar.header("🔄 Recuperaciones por Etapa (%)")
etapas_activas = info_circuito["etapas"]

rec_R_min = st.sidebar.number_input("Recup. Mineral Rougher (%)", min_value=0.0, max_value=100.0, value=85.0, step=0.1, format="%.2f") if "Rougher" in etapas_activas else 0.0
rec_R_ganga = st.sidebar.number_input("Recup. Ganga Rougher (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.1, format="%.2f") if "Rougher" in etapas_activas else 0.0

rec_Cl_min = st.sidebar.number_input("Recup. Mineral Cleaner (%)", min_value=0.0, max_value=100.0, value=80.0, step=0.1, format="%.2f") if "Cleaner" in etapas_activas else 0.0
rec_Cl_ganga = st.sidebar.number_input("Recup. Ganga Cleaner (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1, format="%.2f") if "Cleaner" in etapas_activas else 0.0

rec_Cl1_min = st.sidebar.number_input("Recup. Mineral Cleaner 1 (%)", min_value=0.0, max_value=100.0, value=80.0, step=0.1, format="%.2f") if "Cleaner1" in etapas_activas else 0.0
rec_Cl1_ganga = st.sidebar.number_input("Recup. Ganga Cleaner 1 (%)", min_value=0.0, max_value=100.0, value=1.5, step=0.1, format="%.2f") if "Cleaner1" in etapas_activas else 0.0

rec_Cl2_min = st.sidebar.number_input("Recup. Mineral Cleaner 2 (%)", min_value=0.0, max_value=100.0, value=85.0, step=0.1, format="%.2f") if "Cleaner2" in etapas_activas else 0.0
rec_Cl2_ganga = st.sidebar.number_input("Recup. Ganga Cleaner 2 (%)", min_value=0.0, max_value=100.0, value=0.5, step=0.1, format="%.2f") if "Cleaner2" in etapas_activas else 0.0

rec_Sc_min = st.sidebar.number_input("Recup. Mineral Scavenger (%)", min_value=0.0, max_value=100.0, value=70.0, step=0.1, format="%.2f") if "Scavenger" in etapas_activas else 0.0
rec_Sc_ganga = st.sidebar.number_input("Recup. Ganga Scavenger (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1, format="%.2f") if "Scavenger" in etapas_activas else 0.0

# ---------------------------------------------------------
# 3. DIAGRAMA Y MOTOR DE CÁLCULO MULTI-ESPECIE
# ---------------------------------------------------------
col_diag, col_res = st.columns([1, 1])

with col_diag:
    st.subheader("🖼️ Diagrama de Flujo Activo")
    path_img = info_circuito["imagen"]
    if os.path.exists(path_img):
        st.image(path_img, use_container_width=True)
    else:
        st.warning(f"No se encontró la imagen en '{path_img}'.")

# CÁLCULOS BASE EN ALIMENTACIÓN FRESCA (A)
masa_cu_A = tonelaje_A * (ley_cu_A / 100.0)

if especies_seleccionadas and sum(distribucion_minera.values()) > 0:
    pct_cu_promedio = sum([ESPECIES_BASE[esp] * (distribucion_minera[esp] / 100.0) for esp in especies_seleccionadas])
    masa_min_A = masa_cu_A / (pct_cu_promedio / 100.0)
    str_ensamble = ", ".join([f"{esp} ({distribucion_minera[esp]}%)" for esp in especies_seleccionadas])
else:
    pct_cu_promedio = 100.0
    masa_min_A = masa_cu_A
    str_ensamble = "Cobre Elemental Pureza Metal"

masa_ganga_A = max(0.0, tonelaje_A - masa_min_A)

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

# EJECUCIÓN DE BALANCES DIRECTOS
if "1. Rougher – Scavenger (Con Recirculación" in circuito_seleccionado:
    m_min_ER = masa_min_A / (1.0 - (1.0 - r_R_m) * r_Sc_m)
    m_g_ER = masa_ganga_A / (1.0 - (1.0 - r_R_g) * r_Sc_g)
    s1_R, s2_R = registrar_etapa("Etapa Rougher", m_min_ER, m_g_ER, r_R_m, r_R_g, "CF - Concentrado Final", "Relave Rougher (RR)")
    s1_Sc, s2_Sc = registrar_etapa("Etapa Scavenger", s2_R[0], s2_R[1], r_Sc_m, r_Sc_g, "Conc. Scavenger (CSc)", "Relave Final (RF)")

elif "2. Rougher – Scavenger (Abierto" in circuito_seleccionado:
    s1_R, s2_R = registrar_etapa("Etapa Rougher", masa_min_A, masa_ganga_A, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Rougher (RR)")
    s1_Sc, s2_Sc = registrar_etapa("Etapa Scavenger", s2_R[0], s2_R[1], r_Sc_m, r_Sc_g, "Conc. Scavenger (CSc)", "Relave Final (RF)")
    m_min_CF = s1_R[0] + s1_Sc[0]
    m_g_CF = s1_R[1] + s1_Sc[1]
    m_cu_CF = m_min_CF * (pct_cu_promedio / 100.0)
    m_tot_CF = m_min_CF + m_g_CF
    ley_CF = (m_cu_CF / m_tot_CF * 100.0) if m_tot_CF > 0 else 0.0
    detalle_celdas.append({"Unidad": "Mezcla Final", "Flujo": "SALIDA 1 (CF - Concentrado Final)", "Masa Total (t/h)": round(m_tot_CF, 2), "Masa Minerales (t/h)": round(m_min_CF, 2), "Cobre Fino (t/h)": round(m_cu_CF, 2), "Ganga (t/h)": round(m_g_CF, 2), "Ley %Cu": round(ley_CF, 2)})

elif "3. Rougher – Cleaner (Abierto" in circuito_seleccionado:
    s1_R, s2_R = registrar_etapa("Etapa Rougher", masa_min_A, masa_ganga_A, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Rougher (RR)")
    s1_Cl, s2_Cl = registrar_etapa("Etapa Cleaner", s1_R[0], s1_R[1], r_Cl_m, r_Cl_g, "CF - Concentrado Final", "Relave Cleaner (RCl)")

elif "4. Rougher – Cleaner (Cerrado" in circuito_seleccionado:
    m_min_ER = masa_min_A / (1.0 - r_R_m * (1.0 - r_Cl_m))
    m_g_ER = masa_ganga_A / (1.0 - r_R_g * (1.0 - r_Cl_g))
    s1_R, s2_R = registrar_etapa("Etapa Rougher", m_min_ER, m_g_ER, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Final (RF)")
    s1_Cl, s2_Cl = registrar_etapa("Etapa Cleaner", s1_R[0], s1_R[1], r_Cl_m, r_Cl_g, "CF - Concentrado Final", "Recirculación Cleaner (RCl)")

elif "5. Rougher – Cleaner – Scavenger" in circuito_seleccionado:
    m_min_CR = masa_min_A * r_R_m
    m_g_CR = masa_ganga_A * r_R_g
    denom_m = 1.0 - (1.0 - r_Cl_m) * r_Sc_m
    denom_g = 1.0 - (1.0 - r_Cl_g) * r_Sc_g
    s1_R, s2_R = registrar_etapa("Etapa Rougher", masa_min_A, masa_ganga_A, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Rougher (RR)")
    s1_Cl, s2_Cl = registrar_etapa("Etapa Cleaner", m_min_CR / denom_m, m_g_CR / denom_g, r_Cl_m, r_Cl_g, "CF - Concentrado Final", "Relave Cleaner (RCl)")
    s1_Sc, s2_Sc = registrar_etapa("Etapa Scavenger", s2_Cl[0], s2_Cl[1], r_Sc_m, r_Sc_g, "Conc. Scavenger (RSc)", "Relave Scavenger (RF)")

else: # Circuitos 6 y 7
    m_min_CR = masa_min_A * r_R_m
    m_g_CR = masa_ganga_A * r_R_g
    denom_m = 1.0 - ((1.0 - r_Cl1_m) * r_Sc_m + r_Cl1_m * (1.0 - r_Cl2_m))
    denom_g = 1.0 - ((1.0 - r_Cl1_g) * r_Sc_g + r_Cl1_g * (1.0 - r_Cl2_g))
    
    s1_R, s2_R = registrar_etapa("Etapa Rougher", masa_min_A, masa_ganga_A, r_R_m, r_R_g, "Conc. Rougher (CR)", "Relave Rougher (RR)")
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

# ---------------------------------------------------------
# 4. PESTAÑAS DETALLADAS TIPO EXCEL & EXPORTACIÓN
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 Balance Detallado Entrada/Salida por Celda", 
    "📈 Parámetros de Concentración (RC, RE, RP)", 
    "🔍 Comparativa Inter-Etapas"
])

with tab1:
    st.subheader("📋 Balance de Masa por Unidad Operacional (Vista Estilo Excel)")
    st.caption(f"Ensamble mineralógico activo: **{str_ensamble}** (%Cu Teórico Promedio: **{pct_cu_promedio:.2f}%**)")
    unidades = df_detalle["Unidad"].unique()
    for u in unidades:
        with st.expander(f"🔹 {u} — Detalle de Entradas y Salidas", expanded=True):
            df_u = df_detalle[df_detalle["Unidad"] == u].drop(columns=["Unidad"])
            st.dataframe(df_u, use_container_width=True)

with tab2:
    st.subheader("📐 Parámetros Metalúrgicos Calculados por Etapa")
    st.caption("Resumen de las razones de concentración (RC), enriquecimiento (RE) y peso (RP %) por cada unidad de proceso:")
    df_kpis_etapas = pd.DataFrame(resumen_etapas_kpis)
    st.dataframe(df_kpis_etapas, use_container_width=True)

with tab3:
    st.subheader("🔍 Comparación de Rendimiento Entre Celdas")
    df_entradas = df_detalle[df_detalle["Flujo"].str.contains("ENTRADA")]
    fig = px.bar(
        df_entradas, 
        x="Unidad", 
        y=["Masa Minerales (t/h)", "Ganga (t/h)"], 
        title="Carga de Alimentación Efectiva por Celda (TMSPH)",
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 5. EXPORTACIÓN DE DATOS PARA POWER BI
# ---------------------------------------------------------
st.divider()
st.subheader("📥 Exportar Datos para Power BI")

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

with col_exp1:
    st.download_button(
        label="📄 Descargar Datos en CSV para Power BI",
        data=csv_data,
        file_name="balance_metalurgico_powerbi.csv",
        mime="text/csv",
        help="Descarga el archivo CSV estructurado listo para importar en Power BI."
    )

with col_exp2:
    st.info("💡 Tip: Guarda este CSV en una carpeta local fija. Si conectas Power BI a esa carpeta o archivo, el reporte se actualizará automáticamente cada vez que exportes nuevos escenarios.")

# ---------------------------------------------------------
# 6. DIAGNÓSTICO CON IA (LM STUDIO)
# ---------------------------------------------------------
st.divider()
st.subheader("🤖 Diagnóstico e Interpretación Técnica con IA")

if st.button("🧠 Generar Diagnóstico con LM Studio"):
    with st.spinner("Conectando con LM Studio y evaluando los parámetros de concentración..."):
        try:
            client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
            modelos = client.models.list()
            modelo_activo = modelos.data[0].id if modelos.data else "local-model"
            
            prompt = f"""
            Actúa como un Ingeniero Metalúrgico Senior experto en plantas concentradoras.
            Analiza el circuito: {circuito_seleccionado} con ensamble mineralógico: {str_ensamble}.
            
            PARÁMETROS GLOBALES DEL CIRCUITO:
            - Alimentación Fresca (A): {tonelaje_A} TMSPH con ley de {ley_cu_A}% Cu.
            - Concentrado Final (CF): {masa_cf_tot:.2f} TMSPH con ley de {ley_cf:.2f}% Cu.
            - Recuperación Global (RG): {rec_global:.2f}%
            - Razón de Concentración Global (RC): {rc_global:.2f}
            - Razón de Enriquecimiento Global (RE): {re_global:.2f}
            - Razón en Peso Global (RP): {rp_global:.2f}%
            
            PARÁMETROS DE CONCENTRACIÓN POR ETAPA:
            {df_kpis_etapas.to_string(index=False)}
            
            DETALLE DE FLUIDOS POR CELDA:
            {df_detalle.to_string(index=False)}
            
            Por favor emite un informe técnico enfocado en:
            1. Evaluación del RC y RE global y por etapa.
            2. Impacto de la mezcla de especies mineralógicas en la selectividad del proceso.
            3. Diagnóstico de cuellos de botella según la distribución de ganga y mineral útil.
            4. Recomendaciones operacionales concretas para optimizar el circuito.
            """
            
            response = client.chat.completions.create(
                model=modelo_activo,
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en ingeniería de minerales y balances de masa en flotación."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            st.success(f"¡Diagnóstico completado con {modelo_activo}!")
            st.markdown(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"No se pudo conectar con LM Studio: {e}")

# ---------------------------------------------------------
# 7. PIE DE PÁGINA / CRÉDITOS
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
