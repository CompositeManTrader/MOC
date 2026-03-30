"""
MOC TWAP Dashboard — Mesa de Capitales BMV
Ejecución Market On Close con distribución TWAP por emisora.
Actualización cada minuto, zona horaria Ciudad de México.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time as dtime
import pytz
import time as time_module

# ─── Config ───
st.set_page_config(
    page_title="MOC TWAP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CDMX_TZ = pytz.timezone("America/Mexico_City")


def now_cdmx():
    """Hora actual en Ciudad de México."""
    return datetime.now(CDMX_TZ)


# ─── CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="st-"] { font-family: 'DM Sans', sans-serif; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1c 0%, #111827 100%);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 0.8rem 1.6rem;
    margin-bottom: 1.2rem;
    flex-wrap: wrap;
    gap: 0.6rem;
}
.header-item {
    text-align: center;
    min-width: 120px;
}
.header-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.25rem;
    font-weight: 700;
    line-height: 1.2;
}
.header-label {
    font-size: 0.65rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 2px;
}

.text-cyan { color: #38bdf8; }
.text-slate { color: #cbd5e1; }
.text-green { color: #4ade80; }
.text-amber { color: #fbbf24; }
.text-red { color: #f87171; }

.status-active {
    display: inline-block;
    background: #065f4620;
    border: 1px solid #4ade80;
    color: #4ade80;
    padding: 0.15rem 0.6rem;
    border-radius: 16px;
    font-size: 0.75rem;
    font-weight: 600;
    animation: pulse 2s ease-in-out infinite;
}
.status-waiting {
    display: inline-block;
    background: #78350f20;
    border: 1px solid #fbbf24;
    color: #fbbf24;
    padding: 0.15rem 0.6rem;
    border-radius: 16px;
    font-size: 0.75rem;
    font-weight: 600;
}
.status-finished {
    display: inline-block;
    background: #1e1b4b20;
    border: 1px solid #818cf8;
    color: #818cf8;
    padding: 0.15rem 0.6rem;
    border-radius: 16px;
    font-size: 0.75rem;
    font-weight: 600;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(74,222,128,0.35); }
    50% { box-shadow: 0 0 0 5px rgba(74,222,128,0); }
}

.ventana-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #94a3b8;
    padding: 0.5rem 0.8rem;
    background: #1e293b;
    border-radius: 6px;
    margin-top: 0.4rem;
}

div[data-testid="stDataFrame"] table {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95rem !important;
}

.progress-track {
    background: #1e293b;
    border-radius: 6px;
    height: 8px;
    overflow: hidden;
    width: 100%;
    margin-top: 4px;
}
.progress-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 1s ease;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State ───
if "emisoras" not in st.session_state:
    st.session_state.emisoras = {}
if "twap_minutes" not in st.session_state:
    st.session_state.twap_minutes = 20
if "hora_fin" not in st.session_state:
    st.session_state.hora_fin = dtime(15, 0)
if "last_update" not in st.session_state:
    st.session_state.last_update = now_cdmx()

# ─── Sidebar ───
with st.sidebar:
    st.markdown("## ⚙️ Configuración")

    st.markdown("#### Duración TWAP")
    mins = st.radio(
        "min", [20, 30],
        index=0 if st.session_state.twap_minutes == 20 else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.twap_minutes = mins

    st.markdown("#### Hora Fin")
    hora_fin = st.time_input(
        "Hora fin de ejecución",
        value=st.session_state.hora_fin,
        step=timedelta(minutes=1),
        label_visibility="collapsed",
    )
    st.session_state.hora_fin = hora_fin

    # Auto-calculate hora inicio
    fin_dt = datetime.combine(datetime.today(), hora_fin)
    inicio_dt = fin_dt - timedelta(minutes=st.session_state.twap_minutes)
    hora_inicio = inicio_dt.time()

    # Validaciones BMV
    warnings = []
    if hora_fin < dtime(14, 30) or hora_fin > dtime(15, 0):
        warnings.append("Hora fin fuera de rango BMV (14:30–15:00)")
    if hora_inicio < dtime(14, 0):
        warnings.append("Hora inicio calculada antes de las 14:00")

    for w in warnings:
        st.warning(w)

    st.markdown(f"""
    <div class="ventana-text">
        Ventana: {hora_inicio.strftime("%H:%M")} → {hora_fin.strftime("%H:%M")} ({st.session_state.twap_minutes} min)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ➕ Agregar Emisora")

    with st.form("add_emisora", clear_on_submit=True):
        new_ticker = st.text_input("Emisora", placeholder="Ej: AMX").strip().upper()
        new_titulos = st.number_input(
            "Títulos a Vender",
            min_value=0, value=0, step=100,
        )
        submitted = st.form_submit_button("Agregar", use_container_width=True)
        if submitted and new_ticker and new_titulos > 0:
            if new_ticker in st.session_state.emisoras:
                st.session_state.emisoras[new_ticker] += new_titulos
            else:
                st.session_state.emisoras[new_ticker] = new_titulos
            st.rerun()

    if st.session_state.emisoras:
        st.markdown("#### 🗑️ Eliminar")
        del_ticker = st.selectbox(
            "Emisora a eliminar",
            list(st.session_state.emisoras.keys()),
            label_visibility="collapsed",
        )
        if st.button("Eliminar", use_container_width=True):
            del st.session_state.emisoras[del_ticker]
            st.rerun()
        if st.button("Limpiar Todo", use_container_width=True, type="secondary"):
            st.session_state.emisoras = {}
            st.rerun()


# ─── Cálculos TWAP ───
def compute_twap(emisoras: dict, twap_minutes: int, hora_inicio: dtime, hora_fin: dtime):
    """
    Calcula TWAP por emisora.

    Retorna:
        df: DataFrame con columnas de ejecución
        progress: float 0-1
        status: 'waiting' | 'active' | 'finished'
        remaining_secs: segundos restantes
        ahora: datetime actual CDMX
    """
    ahora = now_cdmx()
    today = ahora.date()

    dt_inicio = CDMX_TZ.localize(datetime.combine(today, hora_inicio))
    dt_fin = CDMX_TZ.localize(datetime.combine(today, hora_fin))

    total_seconds = max((dt_fin - dt_inicio).total_seconds(), 1)
    elapsed = max(0, min((ahora - dt_inicio).total_seconds(), total_seconds))
    remaining = total_seconds - elapsed
    progress = elapsed / total_seconds

    if ahora < dt_inicio:
        status = "waiting"
    elif ahora >= dt_fin:
        status = "finished"
    else:
        status = "active"

    total_minutes = total_seconds / 60.0
    remaining_minutes = remaining / 60.0

    rows = []
    for ticker, titulos in emisoras.items():
        titulos_min = titulos / total_minutes if total_minutes > 0 else 0

        if status == "finished":
            saldo = 0
        elif status == "waiting":
            saldo = titulos
        else:
            saldo = remaining_minutes * titulos_min

        saldo = round(saldo)
        ejecutado = titulos - saldo

        rows.append({
            "Emisora": ticker,
            "Posición (Títulos)": titulos,
            "Títulos/min": round(titulos_min),
            "Ejecutado (Títulos)": ejecutado,
            "Saldo (Títulos)": saldo,
        })

    cols = ["Emisora", "Posición (Títulos)", "Títulos/min", "Ejecutado (Títulos)", "Saldo (Títulos)"]
    df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

    return df, progress, status, remaining, ahora


# ─── Compute ───
df, progress, status, remaining_secs, ahora = compute_twap(
    st.session_state.emisoras,
    st.session_state.twap_minutes,
    hora_inicio,
    hora_fin,
)

# ─── Header Bar ───
r_min = int(remaining_secs // 60)
r_sec = int(remaining_secs % 60)
pct = progress * 100

time_color = "text-green" if remaining_secs > 300 else ("text-amber" if remaining_secs > 60 else "text-red")
bar_color = "#4ade80" if pct < 80 else ("#fbbf24" if pct < 95 else "#f87171")

status_html = {
    "waiting": '<span class="status-waiting">EN ESPERA</span>',
    "active": '<span class="status-active">EN VIVO</span>',
    "finished": '<span class="status-finished">FINALIZADO</span>',
}[status]

st.markdown(f"""
<div class="header-bar">
    <div class="header-item">
        <div class="header-value text-cyan">{ahora.strftime("%H:%M:%S")}</div>
        <div class="header-label">CDMX</div>
    </div>
    <div class="header-item">
        {status_html}
        <div class="header-label">{hora_inicio.strftime("%H:%M")} → {hora_fin.strftime("%H:%M")}</div>
    </div>
    <div class="header-item">
        <div class="header-value {time_color}">{r_min:02d}:{r_sec:02d}</div>
        <div class="header-label">Restante</div>
    </div>
    <div class="header-item" style="min-width:160px;">
        <div class="header-value text-slate">{pct:.1f}%</div>
        <div class="progress-track"><div class="progress-fill" style="width:{pct}%;background:{bar_color};"></div></div>
        <div class="header-label">Avance</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Tabla Principal ───
if not df.empty:

    def color_saldo(val):
        """
        Colorea celda de saldo según % pendiente respecto a posición.
        Verde: ≤20% pendiente (on schedule)
        Amarillo: 20-50% pendiente
        Rojo: >50% pendiente
        """
        return ""

    def row_saldo_color(row):
        """Aplica color al saldo según porcentaje restante."""
        pos = row["Posición (Títulos)"]
        saldo = row["Saldo (Títulos)"]
        if pos == 0:
            ratio = 0
        else:
            ratio = saldo / pos

        styles = [""] * len(row)
        saldo_idx = row.index.get_loc("Saldo (Títulos)")
        if ratio <= 0.20:
            styles[saldo_idx] = "color: #4ade80; font-weight: 700;"
        elif ratio <= 0.50:
            styles[saldo_idx] = "color: #fbbf24; font-weight: 700;"
        else:
            styles[saldo_idx] = "color: #f87171; font-weight: 700;"
        return styles

    styled = (
        df.style
        .apply(row_saldo_color, axis=1)
        .format({
            "Posición (Títulos)": "{:,}",
            "Títulos/min": "{:,}",
            "Ejecutado (Títulos)": "{:,}",
            "Saldo (Títulos)": "{:,}",
        })
    )

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=min(600, 55 + len(df) * 42),
    )
else:
    st.info("Agrega emisoras en el panel lateral para iniciar.")

# ─── TWAP Reference ───
with st.expander("Metodología TWAP"):
    st.markdown("""
    **Posición** = Títulos a vender (ingresados por emisora)

    **Títulos/min** = Posición ÷ Minutos totales de ventana

    **Saldo** = Títulos/min × Minutos restantes

    **Ejecutado** = Posición − Saldo

    Colores de saldo: 🟢 ≤20% pendiente · 🟡 20-50% · 🔴 >50%
    """)

# ─── Refresh cada minuto ───
current = now_cdmx()
delta = (current - st.session_state.last_update).total_seconds()
if delta >= 60:
    st.session_state.last_update = current
    st.rerun()
else:
    wait = 60 - delta
    time_module.sleep(wait)
    st.session_state.last_update = now_cdmx()
    st.rerun()
