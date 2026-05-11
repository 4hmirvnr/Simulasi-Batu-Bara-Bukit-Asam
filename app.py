import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Simulasi Pasar Batubara", layout="wide")
st.title("Simulasi Dinamis Ekstraksi Batubara")
st.markdown("Dasbor ini menyederhanakan dampak harga, tingkat diskonto, dan MUC terhadap produksi, stok, dan waktu habisnya cadangan batubara dalam tiga struktur pasar.")

# --- SIDEBAR: INPUT PENGGUNA (USER FRIENDLY) ---
st.sidebar.header("Parameter Simulasi")

# Parameter Permintaan (Berdasarkan Fungsi: P = a - bQ)
st.sidebar.subheader("Fungsi Permintaan")
a = st.sidebar.number_input("Choke Price (a)", value=36.22, help="Harga maksimum di mana permintaan menjadi nol.")
b = st.sidebar.number_input("Slope (b)", value=0.00000454, format="%.8f")

# Parameter Biaya
st.sidebar.subheader("Biaya & Stok")
mc = st.sidebar.number_input("Marginal Cost (MC)", value=15.0, help="Biaya marginal produksi.")
muc_0 = st.sidebar.number_input("MUC Awal (MUC_0)", value=5.0, help="Nilai langka (Marginal User Cost) pada tahun 0.")
stock_awal = st.sidebar.number_input("Total Cadangan Awal (S_0)", value=5000000.0, step=100000.0)

# Parameter Dinamis
st.sidebar.subheader("Dinamika Waktu")
r = st.sidebar.slider("Tingkat Diskonto (r)", min_value=0.01, max_value=0.20, value=0.0475, step=0.0025, format="%.4f")

# Green Paradox Toggle
st.sidebar.subheader("Analisis Tambahan")
green_paradox = st.sidebar.checkbox("Simulasikan Green Paradox", value=False, help="Mengasumsikan ancaman regulasi emisi di masa depan yang meningkatkan tingkat diskonto efektif perusahaan.")

if green_paradox:
    r = r + 0.05  # Green paradox meningkatkan diskonto karena perusahaan mempercepat ekstraksi
    st.sidebar.warning("Green Paradox Aktif: Ketakutan akan regulasi masa depan memicu peningkatan ekstraksi saat ini (Diskonto naik).")

# --- LOGIKA SIMULASI ---
years = 150
data = []

S_perfect = stock_awal
S_monopoly = stock_awal
S_oligopoly = stock_awal

T_perfect, T_monopoly, T_oligopoly = None, None, None

for t in range(years):
    # Hitung MUC berdasarkan Hotelling's Rule
    muc_t = muc_0 * ((1 + r) ** t)
    
    # 1. Pasar Persaingan Sempurna: P = MC + MUC
    p_perfect = mc + muc_t
    q_perfect = max(0, (a - p_perfect) / b) if p_perfect < a else 0
    if S_perfect <= 0: q_perfect = 0
    S_perfect = max(0, S_perfect - q_perfect)
    if q_perfect == 0 and T_perfect is None: T_perfect = t

    # 2. Pasar Monopoli: MR = MC + MUC -> a - 2bQ = MC + MUC
    q_monopoly = max(0, (a - (mc + muc_t)) / (2 * b)) if (mc + muc_t) < a else 0
    if S_monopoly <= 0: q_monopoly = 0
    p_monopoly = a - (b * q_monopoly) if q_monopoly > 0 else a
    S_monopoly = max(0, S_monopoly - q_monopoly)
    if q_monopoly == 0 and T_monopoly is None: T_monopoly = t

    # 3. Pasar Oligopoli (Asumsi Cournot N=3): Q = (N/(N+1)) * ((a - (MC + MUC))/b)
    N = 3
    q_oligopoly = max(0, (N / (N + 1)) * ((a - (mc + muc_t)) / b)) if (mc + muc_t) < a else 0
    if S_oligopoly <= 0: q_oligopoly = 0
    p_oligopoly = a - (b * q_oligopoly) if q_oligopoly > 0 else a
    S_oligopoly = max(0, S_oligopoly - q_oligopoly)
    if q_oligopoly == 0 and T_oligopoly is None: T_oligopoly = t

    data.append([t, muc_t, p_perfect, q_perfect, S_perfect, p_monopoly, q_monopoly, S_monopoly, p_oligopoly, q_oligopoly, S_oligopoly])

df = pd.DataFrame(data, columns=[
    'Tahun', 'MUC', 
    'P_Persaingan', 'Q_Persaingan', 'S_Persaingan',
    'P_Monopoli', 'Q_Monopoli', 'S_Monopoli',
    'P_Oligopoli', 'Q_Oligopoli', 'S_Oligopoli'
])

# Menangani jika cadangan tidak habis dalam batas iterasi
T_perfect = T_perfect if T_perfect else ">150"
T_monopoly = T_monopoly if T_monopoly else ">150"
T_oligopoly = T_oligopoly if T_oligopoly else ">150"


# --- VISUALISASI UTAMA ---
col1, col2, col3 = st.columns(3)
col1.metric("Waktu Habis (Persaingan)", f"{T_perfect} Tahun")
col2.metric("Waktu Habis (Oligopoli N=3)", f"{T_oligopoly} Tahun")
col3.metric("Waktu Habis (Monopoli)", f"{T_monopoly} Tahun")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Lintasan Produksi (Q)", "Sisa Cadangan (S)", "Dinamika Harga (P)"])

with tab1:
    fig_q = go.Figure()
    fig_q.add_trace(go.Scatter(x=df['Tahun'], y=df['Q_Persaingan'], name='Persaingan', line=dict(color='blue')))
    fig_q.add_trace(go.Scatter(x=df['Tahun'], y=df['Q_Oligopoli'], name='Oligopoli', line=dict(color='orange')))
    fig_q.add_trace(go.Scatter(x=df['Tahun'], y=df['Q_Monopoli'], name='Monopoli', line=dict(color='green')))
    fig_q.update_layout(title="Tingkat Produksi (Ekstraksi) per Tahun", xaxis_title="Tahun", yaxis_title="Kuantitas Produksi")
    st.plotly_chart(fig_q, use_container_width=True)

with tab2:
    fig_s = go.Figure()
    fig_s.add_trace(go.Scatter(x=df['Tahun'], y=df['S_Persaingan'], name='Persaingan', line=dict(color='blue', dash='dash')))
    fig_s.add_trace(go.Scatter(x=df['Tahun'], y=df['S_Oligopoli'], name='Oligopoli', line=dict(color='orange', dash='dash')))
    fig_s.add_trace(go.Scatter(x=df['Tahun'], y=df['S_Monopoli'], name='Monopoli', line=dict(color='green', dash='dash')))
    fig_s.update_layout(title="Penurunan Sisa Cadangan (Deplesi)", xaxis_title="Tahun", yaxis_title="Sisa Stok")
    st.plotly_chart(fig_s, use_container_width=True)

with tab3:
    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(x=df['Tahun'], y=df['P_Persaingan'], name='Persaingan', line=dict(color='blue')))
    fig_p.add_trace(go.Scatter(x=df['Tahun'], y=df['P_Oligopoli'], name='Oligopoli', line=dict(color='orange')))
    fig_p.add_trace(go.Scatter(x=df['Tahun'], y=df['P_Monopoli'], name='Monopoli', line=dict(color='green')))
    fig_p.update_layout(title="Proyeksi Harga Batubara (P)", xaxis_title="Tahun", yaxis_title="Harga")
    st.plotly_chart(fig_p, use_container_width=True)


# --- ANALISIS GREEN PARADOX ---
st.markdown("---")
st.subheader("🌿 Analisis Green Paradox")
st.info("""
**Apa itu Green Paradox?** Jika pemerintah mengumumkan rencana transisi energi hijau yang agresif (misalnya pajak karbon tinggi di masa depan), perusahaan tambang menyadari batubara mereka akan kehilangan nilai di kemudian hari. 
* **Reaksi Rasional:** Perusahaan akan menaikkan *tingkat diskonto* (r) mereka secara artifisial untuk mencerminkan risiko ini.
* **Dampaknya:** Daripada mengurangi emisi, ancaman regulasi ini memicu perusahaan untuk memproduksi lebih banyak batubara **sekarang**, mempercepat deplesi cadangan, dan malah menyebabkan lonjakan emisi karbon jangka pendek.
* *Cobalah centang kotak "Simulasikan Green Paradox" di sidebar untuk melihat bagaimana waktu habisnya cadangan menjadi lebih singkat.*
""")
