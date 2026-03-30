"""
MOC TWAP Dashboard v3 — Mesa de Capitales
Ejecución Market On Close con distribución TWAP por emisora.
Reloj en segundos, cálculos cada minuto, zona horaria CDMX.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time as dtime
import pytz
import time as time_module
import math

# ─── Page Config ───
st.set_page_config(
    page_title="MOC TWAP Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CDMX_TZ = pytz.timezone("America/Mexico_City")


def now_cdmx():
    """Hora actual en Ciudad de México."""
    return datetime.now(CDMX_TZ)


# ─── CSS (estilo visual v1 mejorado) ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

/* ── Base ── */
html, body, [class*="st-"] {
    font-family: 'DM Sans', sans-serif;
}
code, .stDataFrame, [data-testid="stMetric"] {
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070b14 0%, #0f172a 100%);
}
[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4 {
    color: #f1f5f9 !important;
}

/* ── Fix sidebar collapse button (punto 3) ── */
[data-testid="stSidebar"] button[kind="header"] {
    color: #64748b !important;
    background: transparent !important;
    border: none !important;
}
[data-testid="stSidebar"] button[kind="header"]:hover {
    color: #38bdf8 !important;
}
button[data-testid="stBaseButton-headerNoPadding"] {
    color: #64748b !important;
}
button[data-testid="stBaseButton-headerNoPadding"]:hover {
    color: #38bdf8 !important;
}
/* Hide ugly keyboard_double text, show clean arrow */
[data-testid="collapsedControl"] {
    color: #475569 !important;
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 0 8px 8px 0 !important;
}
[data-testid="collapsedControl"]:hover {
    color: #38bdf8 !important;
    border-color: #38bdf8 !important;
}

/* ── Main Header ── */
.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 1.4rem 2rem;
    margin-bottom: 1.2rem;
    text-align: center;
}
.main-header h1 {
    color: #f8fafc;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #94a3b8;
    font-size: 0.9rem;
    margin: 0.25rem 0 0 0;
}

/* ── Clock Boxes (v1 style) ── */
.clock-box {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.1rem 1rem;
    text-align: center;
    margin-bottom: 0.8rem;
}
.clock-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.6rem;
    font-weight: 700;
    color: #38bdf8;
    letter-spacing: 2px;
    line-height: 1;
}
.clock-label {
    color: #64748b;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 0.3rem;
}

/* ── Status Pills ── */
.status-active {
    display: inline-block;
    background: rgba(6,95,70,0.15);
    border: 1px solid #4ade80;
    color: #4ade80;
    padding: 0.2rem 0.85rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    animation: pulse-glow 2s ease-in-out infinite;
}
.status-waiting {
    display: inline-block;
    background: rgba(120,53,15,0.15);
    border: 1px solid #fbbf24;
    color: #fbbf24;
    padding: 0.2rem 0.85rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.status-finished {
    display: inline-block;
    background: rgba(30,27,75,0.15);
    border: 1px solid #818cf8;
    color: #818cf8;
    padding: 0.2rem 0.85rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(74,222,128,0.4); }
    50% { box-shadow: 0 0 0 6px rgba(74,222,128,0); }
}

/* ── Progress Bar ── */
.progress-container {
    background: #1e293b;
    border-radius: 8px;
    height: 10px;
    overflow: hidden;
    margin: 0.4rem 0;
}
.progress-bar {
    height: 100%;
    border-radius: 8px;
    transition: width 1s linear;
}

/* ── Color Helpers ── */
.text-green { color: #4ade80; }
.text-red { color: #f87171; }
.text-blue { color: #38bdf8; }
.text-amber { color: #fbbf24; }
.text-white { color: #f1f5f9; }

/* ── Table Styling ── */
.moc-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.92rem;
    margin-top: 0.5rem;
}
.moc-table thead th {
    background: #0f172a;
    color: #94a3b8;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 0.7rem 1rem;
    border-bottom: 2px solid #334155;
    text-align: right;
    white-space: nowrap;
}
.moc-table thead th:first-child {
    text-align: left;
    border-radius: 10px 0 0 0;
}
.moc-table thead th:last-child {
    border-radius: 0 10px 0 0;
}
.moc-table tbody td {
    padding: 0.65rem 1rem;
    border-bottom: 1px solid #1e293b;
    text-align: right;
    color: #e2e8f0;
    font-weight: 500;
}
.moc-table tbody td:first-child {
    text-align: left;
    font-weight: 700;
    color: #f8fafc;
    font-size: 0.95rem;
}
.moc-table tbody tr {
    background: #0f172a;
    transition: background 0.15s ease;
}
.moc-table tbody tr:hover {
    background: #1e293b;
}
.moc-table tbody tr:last-child td:first-child {
    border-radius: 0 0 0 10px;
}
.moc-table tbody tr:last-child td:last-child {
    border-radius: 0 0 10px 0;
}

/* ── Direction Tags ── */
.tag-compra {
    display: inline-block;
    background: rgba(74,222,128,0.12);
    border: 1px solid #4ade8060;
    color: #4ade80;
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-left: 0.4rem;
    vertical-align: middle;
}
.tag-venta {
    display: inline-block;
    background: rgba(248,113,113,0.12);
    border: 1px solid #f8717160;
    color: #f87171;
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-left: 0.4rem;
    vertical-align: middle;
}

/* ── Saldo Color Classes ── */
.saldo-ok { color: #4ade80; font-weight: 700; }
.saldo-warn { color: #fbbf24; font-weight: 700; }
.saldo-crit { color: #f87171; font-weight: 700; }

/* ── Ventana Info ── */
.ventana-info {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #94a3b8;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.55rem 0.9rem;
    margin-top: 0.5rem;
    text-align: center;
}

/* ── Sidebar Divider ── */
.sidebar-divider {
    border: none;
    border-top: 1px solid #1e293b;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State ───
if "emisoras" not in st.session_state:
    st.session_state.emisoras = {}  # {ticker: {"compra": int, "venta": int}}
if "twap_minutes" not in st.session_state:
    st.session_state.twap_minutes = 20
if "hora_fin" not in st.session_state:
    st.session_state.hora_fin = dtime(15, 0)
if "last_calc_minute" not in st.session_state:
    st.session_state.last_calc_minute = -1
if "cached_df" not in st.session_state:
    st.session_state.cached_df = None
if "cached_meta" not in st.session_state:
    st.session_state.cached_meta = {}

# ─── Sidebar ───
with st.sidebar:
    st.markdown("## ⚙️ Configuración")

    st.markdown("#### Duración TWAP")
    mins = st.radio(
        "Duración",
        [20, 30],
        index=0 if st.session_state.twap_minutes == 20 else 1,
        horizontal=True,
        label_visibility="collapsed",
        help="20 min = normal · 30 min = situación especial",
    )
    st.session_state.twap_minutes = mins

    st.markdown("#### Hora Fin")
    hora_fin = st.time_input(
        "Hora fin",
        value=st.session_state.hora_fin,
        step=timedelta(minutes=1),
        label_visibility="collapsed",
    )
    st.session_state.hora_fin = hora_fin

    # Auto-calc hora inicio
    fin_dt = datetime.combine(datetime.today(), hora_fin)
    inicio_dt = fin_dt - timedelta(minutes=st.session_state.twap_minutes)
    hora_inicio = inicio_dt.time()

    st.markdown(f"""
    <div class="ventana-info">
        {hora_inicio.strftime("%H:%M")} → {hora_fin.strftime("%H:%M")} &nbsp;·&nbsp; {st.session_state.twap_minutes} min
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # ── Agregar Emisora ──
    st.markdown("#### ➕ Agregar Emisora")

    with st.form("add_emisora", clear_on_submit=True):
        new_ticker = st.text_input("Emisora", placeholder="Ej: AMX").strip().upper()
        tipo = st.radio(
            "Tipo de operación",
            ["Compra", "Venta"],
            horizontal=True,
            label_visibility="collapsed",
        )
        new_titulos = st.number_input(
            "Títulos",
            min_value=0, value=0, step=100,
            help="Cantidad de títulos de la operación",
        )
        submitted = st.form_submit_button("Agregar", use_container_width=True)
        if submitted and new_ticker and new_titulos > 0:
            if new_ticker not in st.session_state.emisoras:
                st.session_state.emisoras[new_ticker] = {"compra": 0, "venta": 0}
            if tipo == "Compra":
                st.session_state.emisoras[new_ticker]["compra"] += new_titulos
            else:
                st.session_state.emisoras[new_ticker]["venta"] += new_titulos
            st.rerun()

    # ── Eliminar ──
    if st.session_state.emisoras:
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown("#### 🗑️ Eliminar")
        del_ticker = st.selectbox(
            "Emisora", list(st.session_state.emisoras.keys()),
            label_visibility="collapsed",
        )
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("Eliminar", use_container_width=True):
                del st.session_state.emisoras[del_ticker]
                st.rerun()
        with col_del2:
            if st.button("Limpiar", use_container_width=True, type="secondary"):
                st.session_state.emisoras = {}
                st.rerun()


# ─── TWAP Calculation ───
def compute_twap(emisoras: dict, twap_minutes: int, h_inicio: dtime, h_fin: dtime):
    """
    Calcula distribución TWAP por emisora.

    Posición neta = |compra - venta|
    Dirección = Compra si compra > venta, Venta si venta > compra
    Títulos/min = posición neta / minutos totales
    Deberías llevar = títulos/min × minutos transcurridos
    Faltan = posición neta - deberías llevar
    """
    ahora = now_cdmx()
    today = ahora.date()

    dt_inicio = CDMX_TZ.localize(datetime.combine(today, h_inicio))
    dt_fin = CDMX_TZ.localize(datetime.combine(today, h_fin))

    total_seconds = max((dt_fin - dt_inicio).total_seconds(), 1)
    elapsed = max(0.0, min((ahora - dt_inicio).total_seconds(), total_seconds))
    remaining = total_seconds - elapsed
    progress = elapsed / total_seconds

    if ahora < dt_inicio:
        status = "waiting"
    elif ahora >= dt_fin:
        status = "finished"
    else:
        status = "active"

    total_minutes = total_seconds / 60.0
    elapsed_minutes = elapsed / 60.0

    rows = []
    for ticker, ops in emisoras.items():
        compra = ops["compra"]
        venta = ops["venta"]
        neta = compra - venta
        posicion = abs(neta)
        es_compra = neta > 0  # net long → needs to sell; net short → needs to buy

        titulos_min = posicion / total_minutes if total_minutes > 0 else 0

        if status == "finished":
            deberias_llevar = posicion
            faltan = 0
        elif status == "waiting":
            deberias_llevar = 0
            faltan = posicion
        else:
            deberias_llevar = elapsed_minutes * titulos_min
            faltan = posicion - deberias_llevar

        rows.append({
            "ticker": ticker,
            "compra": compra,
            "venta": venta,
            "es_compra": es_compra,
            "posicion": posicion,
            "titulos_min": round(titulos_min),
            "deberias_llevar": round(deberias_llevar),
            "faltan": round(faltan),
        })

    return rows, progress, status, remaining, ahora, dt_inicio, dt_fin


# ─── Determine if we need to recalculate ───
ahora = now_cdmx()
current_minute = ahora.minute + ahora.hour * 60

needs_recalc = (
    current_minute != st.session_state.last_calc_minute
    or st.session_state.cached_df is None
)

if needs_recalc:
    rows, progress, status, remaining, ahora, dt_inicio, dt_fin = compute_twap(
        st.session_state.emisoras,
        st.session_state.twap_minutes,
        hora_inicio,
        hora_fin,
    )
    st.session_state.last_calc_minute = current_minute
    st.session_state.cached_df = rows
    st.session_state.cached_meta = {
        "progress": progress,
        "status": status,
        "remaining": remaining,
        "ahora": ahora,
    }
else:
    rows = st.session_state.cached_df
    progress = st.session_state.cached_meta["progress"]
    status = st.session_state.cached_meta["status"]
    remaining = st.session_state.cached_meta["remaining"]

# Always get fresh time for the clock display (seconds tick)
ahora = now_cdmx()

# ─── Header ───
st.markdown("""
<div class="main-header">
    <h1>📊 MOC TWAP Dashboard</h1>
    <p>Market On Close · Time-Weighted Average Price · Mesa de Capitales</p>
</div>
""", unsafe_allow_html=True)

# ─── Clock Row (4 boxes, v1 style) ───
col_clock, col_status, col_remain, col_progress = st.columns([2, 1.8, 1.5, 2])

with col_clock:
    st.markdown(f"""
    <div class="clock-box">
        <div class="clock-time">{ahora.strftime("%H:%M:%S")}</div>
        <div class="clock-label">Ciudad de México</div>
    </div>
    """, unsafe_allow_html=True)

with col_status:
    status_html = {
        "waiting": '<span class="status-waiting">⏳ EN ESPERA</span>',
        "active": '<span class="status-active">🟢 EN VIVO</span>',
        "finished": '<span class="status-finished">✅ FINALIZADO</span>',
    }[status]
    st.markdown(f"""
    <div class="clock-box">
        <div style="margin-bottom:0.4rem;">{status_html}</div>
        <div class="clock-label">{hora_inicio.strftime("%H:%M")} → {hora_fin.strftime("%H:%M")} · {st.session_state.twap_minutes} min</div>
    </div>
    """, unsafe_allow_html=True)

with col_remain:
    r_min = int(remaining // 60)
    r_sec = int(remaining % 60)
    tc = "text-green" if remaining > 300 else ("text-amber" if remaining > 60 else "text-red")
    st.markdown(f"""
    <div class="clock-box">
        <div class="clock-time {tc}" style="font-size:2.2rem;">{r_min:02d}:{r_sec:02d}</div>
        <div class="clock-label">Tiempo Restante</div>
    </div>
    """, unsafe_allow_html=True)

with col_progress:
    pct = progress * 100
    bc = "#4ade80" if pct < 80 else ("#fbbf24" if pct < 95 else "#f87171")
    st.markdown(f"""
    <div class="clock-box">
        <div class="clock-time text-white" style="font-size:2.2rem;">{pct:.1f}%</div>
        <div class="progress-container">
            <div class="progress-bar" style="width:{pct}%;background:{bc};"></div>
        </div>
        <div class="clock-label">Avance de Ejecución</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Table ───
if rows:
    # Build HTML table for full visual control
    table_html = """
    <table class="moc-table">
        <thead>
            <tr>
                <th style="text-align:left;">Emisora</th>
                <th>Posición Inicial</th>
                <th>Títulos/min</th>
                <th>Deberías Llevar</th>
                <th>Faltan</th>
            </tr>
        </thead>
        <tbody>
    """

    for r in rows:
        # Direction tag
        if r["es_compra"]:
            tag = '<span class="tag-compra">COMPRA</span>'
        else:
            tag = '<span class="tag-venta">VENTA</span>'

        # If flat (both zero or equal)
        if r["posicion"] == 0:
            tag = ""

        # Saldo color
        if r["posicion"] > 0:
            ratio = r["faltan"] / r["posicion"]
        else:
            ratio = 0

        if ratio <= 0.20:
            saldo_class = "saldo-ok"
        elif ratio <= 0.50:
            saldo_class = "saldo-warn"
        else:
            saldo_class = "saldo-crit"

        table_html += f"""
            <tr>
                <td>{r["ticker"]} {tag}</td>
                <td>{r["posicion"]:,}</td>
                <td>{r["titulos_min"]:,}</td>
                <td>{r["deberias_llevar"]:,}</td>
                <td class="{saldo_class}">{r["faltan"]:,}</td>
            </tr>
        """

    table_html += """
        </tbody>
    </table>
    """

    st.markdown(table_html, unsafe_allow_html=True)

else:
    st.markdown("")
    st.info("👈 Agrega emisoras en el panel lateral para comenzar.")

# ─── Auto-refresh: sleep 1 second for clock, rerun ───
time_module.sleep(1)
st.rerun()
