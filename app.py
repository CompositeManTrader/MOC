import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dtime
import pytz
import time as time_module

# ─── Page Config ───
st.set_page_config(
    page_title="MOC TWAP Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=DM+Sans:wght@400;500;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'DM Sans', sans-serif;
}

code, .stDataFrame, [data-testid="stMetric"] {
    font-family: 'JetBrains Mono', monospace !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1c 0%, #111827 100%);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
.main-header h1 {
    color: #f8fafc;
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #94a3b8;
    font-size: 0.95rem;
    margin: 0.3rem 0 0 0;
}

.clock-box {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    margin-bottom: 1rem;
}
.clock-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.8rem;
    font-weight: 700;
    color: #38bdf8;
    letter-spacing: 2px;
    line-height: 1;
}
.clock-label {
    color: #64748b;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 0.3rem;
}

.metric-card {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.1;
}
.metric-label {
    color: #64748b;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 0.25rem;
}
.text-green { color: #4ade80; }
.text-red { color: #f87171; }
.text-blue { color: #38bdf8; }
.text-amber { color: #fbbf24; }
.text-white { color: #f1f5f9; }

.status-active {
    display: inline-block;
    background: #065f4620;
    border: 1px solid #4ade80;
    color: #4ade80;
    padding: 0.2rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    animation: pulse-border 2s ease-in-out infinite;
}
.status-waiting {
    display: inline-block;
    background: #78350f20;
    border: 1px solid #fbbf24;
    color: #fbbf24;
    padding: 0.2rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.status-finished {
    display: inline-block;
    background: #1e1b4b20;
    border: 1px solid #818cf8;
    color: #818cf8;
    padding: 0.2rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
@keyframes pulse-border {
    0%, 100% { box-shadow: 0 0 0 0 rgba(74,222,128,0.4); }
    50% { box-shadow: 0 0 0 6px rgba(74,222,128,0); }
}

div[data-testid="stDataFrame"] table {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem;
}

.progress-container {
    background: #1e293b;
    border-radius: 8px;
    height: 10px;
    overflow: hidden;
    margin: 0.5rem 0;
}
.progress-bar {
    height: 100%;
    border-radius: 8px;
    transition: width 1s linear;
}
</style>
""", unsafe_allow_html=True)

# ─── Timezone ───
CDMX_TZ = pytz.timezone("America/Mexico_City")

def now_cdmx():
    return datetime.now(CDMX_TZ)

# ─── Session State Defaults ───
if "emisoras" not in st.session_state:
    st.session_state.emisoras = {}

if "twap_minutes" not in st.session_state:
    st.session_state.twap_minutes = 20

if "hora_inicio" not in st.session_state:
    st.session_state.hora_inicio = dtime(14, 40)

if "hora_fin" not in st.session_state:
    st.session_state.hora_fin = dtime(15, 0)

# ─── Sidebar ───
with st.sidebar:
    st.markdown("## ⚙️ Configuración")

    st.markdown("### ⏱️ Ventana de Ejecución")
    mins_option = st.radio(
        "Duración TWAP",
        [20, 30],
        index=0 if st.session_state.twap_minutes == 20 else 1,
        horizontal=True,
        help="20 min = operación normal · 30 min = situación especial"
    )
    st.session_state.twap_minutes = mins_option

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        hora_inicio = st.time_input(
            "Hora inicio",
            value=st.session_state.hora_inicio,
            step=timedelta(minutes=1),
        )
        st.session_state.hora_inicio = hora_inicio
    with col_h2:
        hora_fin = st.time_input(
            "Hora fin",
            value=st.session_state.hora_fin,
            step=timedelta(minutes=1),
        )
        st.session_state.hora_fin = hora_fin

    # Validate times
    inicio_dt = datetime.combine(datetime.today(), hora_inicio)
    fin_dt = datetime.combine(datetime.today(), hora_fin)
    diff_mins = (fin_dt - inicio_dt).total_seconds() / 60
    if diff_mins <= 0:
        st.error("La hora de fin debe ser posterior a la de inicio.")
    elif diff_mins != st.session_state.twap_minutes:
        st.warning(f"La ventana es de {int(diff_mins)} min, pero seleccionaste {st.session_state.twap_minutes} min. Se usará la duración real de {int(diff_mins)} min.")

    st.markdown("---")
    st.markdown("### ➕ Agregar Emisora")

    with st.form("add_emisora", clear_on_submit=True):
        new_ticker = st.text_input("Emisora (ticker)", placeholder="Ej: AMX").strip().upper()
        col_c, col_v = st.columns(2)
        with col_c:
            new_compra = st.number_input("Compras ($)", min_value=0, value=0, step=1000, help="Monto total comprado a precio de cierre")
        with col_v:
            new_venta = st.number_input("Ventas ($)", min_value=0, value=0, step=1000, help="Monto total vendido a precio de cierre")
        submitted = st.form_submit_button("Agregar", use_container_width=True)
        if submitted and new_ticker:
            if new_ticker in st.session_state.emisoras:
                prev = st.session_state.emisoras[new_ticker]
                st.session_state.emisoras[new_ticker] = {
                    "compra": prev["compra"] + new_compra,
                    "venta": prev["venta"] + new_venta,
                }
            else:
                st.session_state.emisoras[new_ticker] = {
                    "compra": new_compra,
                    "venta": new_venta,
                }
            st.rerun()

    if st.session_state.emisoras:
        st.markdown("### 🗑️ Eliminar Emisora")
        del_ticker = st.selectbox("Selecciona", list(st.session_state.emisoras.keys()), label_visibility="collapsed")
        if st.button("Eliminar", use_container_width=True):
            del st.session_state.emisoras[del_ticker]
            st.rerun()

        if st.button("🔄 Limpiar Todo", use_container_width=True, type="secondary"):
            st.session_state.emisoras = {}
            st.rerun()

# ─── Calculations ───
def compute_dashboard(emisoras: dict, twap_minutes: int, hora_inicio: dtime, hora_fin: dtime):
    ahora = now_cdmx()
    today = ahora.date()

    dt_inicio = CDMX_TZ.localize(datetime.combine(today, hora_inicio))
    dt_fin = CDMX_TZ.localize(datetime.combine(today, hora_fin))

    total_seconds = (dt_fin - dt_inicio).total_seconds()
    if total_seconds <= 0:
        total_seconds = twap_minutes * 60

    elapsed_seconds = (ahora - dt_inicio).total_seconds()
    elapsed_seconds = max(0, min(elapsed_seconds, total_seconds))
    remaining_seconds = total_seconds - elapsed_seconds

    # Progress
    progress = elapsed_seconds / total_seconds if total_seconds > 0 else 0
    progress = max(0.0, min(1.0, progress))

    # Status
    if ahora < dt_inicio:
        status = "waiting"
    elif ahora >= dt_fin:
        status = "finished"
    else:
        status = "active"

    # Remaining minutes (for TWAP calc, we use seconds-based precision)
    remaining_minutes = remaining_seconds / 60.0

    # Per-second slice for live countdown
    rows = []
    for ticker, data in emisoras.items():
        compra = data["compra"]
        venta = data["venta"]
        neta = compra - venta  # positive = largo
        posicion = abs(neta)
        direccion = "LARGO" if neta > 0 else ("CORTO" if neta < 0 else "FLAT")

        # TWAP: lotes por minuto = posicion / total_minutes
        total_minutes = total_seconds / 60.0
        lotes_por_minuto = posicion / total_minutes if total_minutes > 0 else 0

        # Saldo = remaining_minutes * lotes_por_minuto
        if status == "finished":
            saldo = 0
        elif status == "waiting":
            saldo = posicion  # todo pendiente
        else:
            saldo = remaining_minutes * lotes_por_minuto

        # Round saldo to nearest integer
        saldo = round(saldo)

        # Executed
        ejecutado = posicion - abs(saldo)

        rows.append({
            "Emisora": ticker,
            "Dirección": direccion,
            "Posición": posicion,
            "Lotes/min": round(lotes_por_minuto),
            "Ejecutado": ejecutado,
            "Saldo": saldo,
            "% Avance": f"{progress*100:.1f}%",
        })

    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Emisora","Dirección","Posición","Lotes/min","Ejecutado","Saldo","% Avance"])

    return df, progress, status, remaining_seconds, ahora, dt_inicio, dt_fin


# ─── Main Layout ───
st.markdown("""
<div class="main-header">
    <h1>📊 MOC TWAP Dashboard</h1>
    <p>Market On Close · Time-Weighted Average Price · Mesa de Capitales</p>
</div>
""", unsafe_allow_html=True)

df, progress, status, remaining_secs, ahora, dt_inicio, dt_fin = compute_dashboard(
    st.session_state.emisoras,
    st.session_state.twap_minutes,
    st.session_state.hora_inicio,
    st.session_state.hora_fin,
)

# ─── Clock & Status Row ───
col_clock, col_status, col_remain, col_progress = st.columns([2, 1.5, 1.5, 2])

with col_clock:
    st.markdown(f"""
    <div class="clock-box">
        <div class="clock-time">{ahora.strftime("%H:%M:%S")}</div>
        <div class="clock-label">Ciudad de México</div>
    </div>
    """, unsafe_allow_html=True)

with col_status:
    status_map = {
        "waiting": '<span class="status-waiting">⏳ EN ESPERA</span>',
        "active": '<span class="status-active">🔴 EN VIVO</span>',
        "finished": '<span class="status-finished">✅ FINALIZADO</span>',
    }
    ventana_label = f"{st.session_state.hora_inicio.strftime('%H:%M')} → {st.session_state.hora_fin.strftime('%H:%M')}"
    st.markdown(f"""
    <div class="clock-box">
        <div style="margin-bottom:0.5rem;">{status_map[status]}</div>
        <div class="clock-label">{ventana_label}</div>
    </div>
    """, unsafe_allow_html=True)

with col_remain:
    r_min = int(remaining_secs // 60)
    r_sec = int(remaining_secs % 60)
    time_color = "text-green" if remaining_secs > 300 else ("text-amber" if remaining_secs > 60 else "text-red")
    st.markdown(f"""
    <div class="clock-box">
        <div class="clock-time {time_color}" style="font-size:2rem;">{r_min:02d}:{r_sec:02d}</div>
        <div class="clock-label">Tiempo Restante</div>
    </div>
    """, unsafe_allow_html=True)

with col_progress:
    pct = progress * 100
    bar_color = "#4ade80" if pct < 80 else ("#fbbf24" if pct < 95 else "#f87171")
    st.markdown(f"""
    <div class="clock-box">
        <div class="metric-value text-white" style="font-size:1.8rem;">{pct:.1f}%</div>
        <div class="progress-container">
            <div class="progress-bar" style="width:{pct}%;background:{bar_color};"></div>
        </div>
        <div class="clock-label">Progreso Ejecución</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Summary Metrics ───
if not df.empty:
    total_pos = df["Posición"].sum()
    total_ejec = df["Ejecutado"].sum()
    total_saldo = df["Saldo"].sum()
    n_emisoras = len(df)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value text-blue">{n_emisoras}</div>
            <div class="metric-label">Emisoras</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value text-white">${total_pos:,.0f}</div>
            <div class="metric-label">Posición Total</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value text-green">${total_ejec:,.0f}</div>
            <div class="metric-label">Ejecutado</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value text-red">${total_saldo:,.0f}</div>
            <div class="metric-label">Saldo Pendiente</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

# ─── Main Table ───
if not df.empty:
    st.markdown("### 📋 Detalle por Emisora")

    def color_direccion(val):
        if val == "LARGO":
            return "color: #4ade80; font-weight: 700;"
        elif val == "CORTO":
            return "color: #f87171; font-weight: 700;"
        return ""

    def color_saldo(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return "color: #fbbf24; font-weight: 600;"
            return "color: #4ade80;"
        return ""

    styled = df.style.applymap(color_direccion, subset=["Dirección"]) \
                     .applymap(color_saldo, subset=["Saldo"]) \
                     .format({
                         "Posición": "${:,.0f}",
                         "Lotes/min": "${:,.0f}",
                         "Ejecutado": "${:,.0f}",
                         "Saldo": "${:,.0f}",
                     })

    st.dataframe(styled, use_container_width=True, hide_index=True, height=min(400, 60 + len(df)*40))

    # ─── Per-emisora cards ───
    st.markdown("### 📊 Detalle Individual")
    cols_per_row = 3
    emisora_list = list(st.session_state.emisoras.keys())
    for i in range(0, len(emisora_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(emisora_list):
                ticker = emisora_list[idx]
                row = df[df["Emisora"] == ticker].iloc[0]
                dir_color = "text-green" if row["Dirección"] == "LARGO" else "text-red"
                with col:
                    st.markdown(f"""
                    <div class="metric-card" style="margin-bottom:1rem;">
                        <div style="font-size:1.1rem;font-weight:700;color:#f1f5f9;margin-bottom:0.6rem;">{ticker}</div>
                        <div style="font-size:0.8rem;" class="{dir_color}">{row["Dirección"]}</div>
                        <div style="display:flex;justify-content:space-between;margin-top:0.6rem;">
                            <div>
                                <div class="metric-label">Posición</div>
                                <div style="color:#e2e8f0;font-family:'JetBrains Mono';font-size:0.9rem;">${row["Posición"]:,.0f}</div>
                            </div>
                            <div>
                                <div class="metric-label">Lotes/min</div>
                                <div style="color:#38bdf8;font-family:'JetBrains Mono';font-size:0.9rem;">${row["Lotes/min"]:,.0f}</div>
                            </div>
                            <div>
                                <div class="metric-label">Saldo</div>
                                <div style="color:#fbbf24;font-family:'JetBrains Mono';font-size:0.9rem;">${row["Saldo"]:,.0f}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

else:
    st.info("👈 Agrega emisoras en el panel lateral para comenzar.")

# ─── TWAP Explanation ───
with st.expander("ℹ️ Metodología TWAP"):
    st.markdown("""
    **Time-Weighted Average Price (TWAP)**

    La estrategia MOC consiste en:

    1. **Posición neta** = Σ Compras − Σ Ventas (por emisora)
    2. **Dirección** = Largo si posición > 0, Corto si < 0
    3. **Lotes por minuto** = Posición neta ÷ Minutos totales de la ventana
    4. **Saldo** = Lotes/min × Minutos restantes
    5. **Ejecutado** = Posición − |Saldo|

    El TWAP distribuye la ejecución uniformemente en el tiempo para minimizar impacto de mercado.
    La actualización es cada segundo para tracking preciso.
    """)

# ─── Auto-refresh every 1 second ───
time_module.sleep(1)
st.rerun()
