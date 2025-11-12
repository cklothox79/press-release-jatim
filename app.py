# ==========================================================
# app.py
# TAFFWARR Fusion — Press Release Otomatis Cuaca Ekstrem Jawa Timur
# Versi 2.1 — dengan Auto Data, ECMWF, Atmosfer, Histogram, dan Peta Interaktif
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import textwrap
import os
import matplotlib.pyplot as plt
import geopandas as gpd
import plotly.express as px

# === MODULES ===
from modules.atmosphere_scraper import scrape_all as scrape_atmosphere
from modules.ecmwf_fetcher import fetch_ecmwf_summary

# === PAGE CONFIG ===
st.set_page_config(page_title="TAFFWARR Fusion — Press Release Jatim", layout="wide")
st.title("🌩️ TAFFWARR Fusion — Press Release Otomatis (Jawa Timur)")
st.markdown(
    "Aplikasi ini menghasilkan *press release* kewaspadaan cuaca ekstrem di Jawa Timur "
    "berdasarkan data TAFFWARR Fusion, radar Juanda, dinamika atmosfer global, dan model ECMWF (Open-Meteo)."
)

# === SIDEBAR ===
st.sidebar.header("⚙️ Pengaturan Umum")
periode = st.sidebar.text_input("Periode", value="13–19 November 2025")
tanggal = st.sidebar.date_input("Tanggal Terbit", value=datetime.utcnow().date())
nomor = st.sidebar.text_input("Nomor Naskah", value="PR-BMKG-JD/001/2025")
high_thr = st.sidebar.slider("Ambang Potensi Tinggi (%)", 50, 90, 70)
low_thr = st.sidebar.slider("Ambang Potensi Rendah (%)", 10, 50, 40)
auto_seed_toggle = st.sidebar.checkbox("Gunakan seed harian untuk auto-data", value=True)

# === DINAMIKA ATMOSFER & ECMWF ===
st.sidebar.markdown("---")
st.sidebar.subheader("🌏 Dinamika Atmosfer")
atmo = scrape_atmosphere()
st.sidebar.json(atmo)

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Data ECMWF (Open-Meteo)")
ecmwf = fetch_ecmwf_summary()
st.sidebar.json(ecmwf)

# === DATA FUSION (UPLOAD / AUTO) ===
st.markdown("## 📥 Data Probabilitas Cuaca Ekstrem (TAFFWARR Fusion)")

uploaded = st.file_uploader("Unggah CSV (kolom: wilayah, probabilitas)", type=["csv"])
os.makedirs("data", exist_ok=True)
auto_path = "data/fusion_auto.csv"

def generate_auto_data(seed=None):
    wilayah_jatim = [
        "Kab. Bangkalan","Kab. Banyuwangi","Kota Blitar","Kab. Blitar","Kab. Bojonegoro","Kab. Bondowoso",
        "Kab. Gresik","Kab. Jember","Kab. Jombang","Kota Kediri","Kab. Kediri","Kota Batu","Kab. Malang",
        "Kota Malang","Kota Surabaya","Kab. Lamongan","Kab. Lumajang","Kota Madiun","Kab. Madiun","Kab. Magetan",
        "Kota Mojokerto","Kab. Mojokerto","Kab. Ngawi","Kab. Nganjuk","Kab. Pacitan","Kab. Pamekasan",
        "Kota Pasuruan","Kab. Pasuruan","Kab. Ponorogo","Kota Probolinggo","Kab. Probolinggo","Kab. Sampang",
        "Kab. Sidoarjo","Kab. Situbondo","Kab. Sumenep","Kab. Trenggalek","Kab. Tuban","Kab. Tulungagung"
    ]
    if seed is None:
        seed = datetime.now().timetuple().tm_yday
    random.seed(seed)
    def gen_prob(nama):
        selatan = ["Malang","Lumajang","Jember","Trenggalek","Tulungagung","Pacitan","Blitar","Banyuwangi"]
        base = 70 if any(s in nama for s in selatan) else 45
        noise = random.randint(-15, 20)
        return max(15, min(95, base + noise))
    df_auto = pd.DataFrame({
        "wilayah": wilayah_jatim,
        "probabilitas": [gen_prob(w) for w in wilayah_jatim]
    })
    df_auto.to_csv(auto_path, index=False)
    return df_auto, seed

if uploaded:
    df = pd.read_csv(uploaded)
    st.success("File CSV berhasil dimuat.")
else:
    seed = datetime.now().timetuple().tm_yday if auto_seed_toggle else None
    if os.path.exists(auto_path):
        df = pd.read_csv(auto_path)
        st.info(f"Memuat data otomatis dari `{auto_path}` ({len(df)} wilayah).")
    else:
        df, seed = generate_auto_data(seed)
        st.success(f"Data otomatis dibuat untuk {len(df)} wilayah (seed {seed}).")

# === VALIDASI ===
if "wilayah" not in df.columns or "probabilitas" not in df.columns:
    st.error("Data harus memiliki kolom 'wilayah' dan 'probabilitas'.")
    st.stop()

df["probabilitas"] = pd.to_numeric(df["probabilitas"], errors="coerce").fillna(0).clip(0, 100)
df["kategori"] = pd.cut(
    df["probabilitas"],
    bins=[0, low_thr, high_thr, 100],
    labels=["Rendah", "Sedang", "Tinggi"],
    include_lowest=True
)

# === TABEL RINGKASAN ===
col1, col2 = st.columns([1.2, 1])
with col1:
    st.subheader("📋 Tabel Probabilitas per Wilayah")
    st.dataframe(df.style.format({"probabilitas": "{:.1f}"}), height=420)
    st.markdown("### Statistik Ringkasan")
    st.write(df["probabilitas"].describe())

    # === HISTOGRAM DISTRIBUSI ===
    st.markdown("### 📈 Distribusi Probabilitas Cuaca Ekstrem")
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.hist(df["probabilitas"], bins=10, color="#1f77b4", edgecolor='black', alpha=0.8)
    ax.set_xlabel("Probabilitas (%)")
    ax.set_ylabel("Jumlah Wilayah")
    ax.set_title("Distribusi Potensi Cuaca Ekstrem Jawa Timur")
    st.pyplot(fig)

with col2:
    st.subheader("🛰️ Radar BMKG Juanda (Live)")
    radar_url = "https://stamet-juanda.bmkg.go.id/radar/data/composite_latest.png"
    st.image(radar_url, caption="Citra Reflektivitas Komposit (Juanda, update otomatis)", use_column_width=True)
    st.markdown("---")
    st.subheader("🗺️ Peta Potensi Cuaca Ekstrem (Choropleth)")

    geojson_url = "https://raw.githubusercontent.com/superpikar/jatim-geojson/main/jatim_kabkota.geojson"
    try:
        gdf = gpd.read_file(geojson_url)
        merged = gdf.merge(df, left_on="WADMKC", right_on="wilayah", how="left")
        color_map = {"Tinggi": "red", "Sedang": "orange", "Rendah": "green"}
        merged["warna"] = merged["kategori"].map(color_map)
        figmap = px.choropleth_mapbox(
            merged,
            geojson=merged.geometry.__geo_interface__,
            locations=merged.index,
            color="kategori",
            color_discrete_map=color_map,
            hover_name="wilayah",
            hover_data=["probabilitas"],
            mapbox_style="carto-positron",
            zoom=6.5,
            center={"lat": -7.5, "lon": 112.0},
            opacity=0.7
        )
        st.plotly_chart(figmap, use_container_width=True)
    except Exception as e:
        st.warning(f"Gagal memuat peta Jawa Timur: {e}")

# === PRESS RELEASE ===
st.markdown("---")
st.subheader("📰 Draft Press Release Otomatis")

mjo_phase = atmo.get("phase", "?")
mjo_amp = atmo.get("amplitude", "?")
kelvin_active = atmo.get("kelvin_active", False)
olr_text = atmo.get("olr_anomaly", "")
sst_text = atmo.get("sst_desc", "")
ecmwf_desc = ecmwf.get("desc", "")

intro = (
    f"Hampir seluruh wilayah Jawa Timur telah memasuki musim hujan. "
    f"Terindikasi adanya potensi peningkatan cuaca ekstrem pada periode {periode} "
    "yang berpotensi berdampak pada aktivitas masyarakat."
)
cause_parts = [
    f"Fenomena ini dipengaruhi oleh MJO fase {mjo_phase} (amplitudo {mjo_amp}).",
]
if kelvin_active:
    cause_parts.append("Gelombang atmosfer Kelvin aktif melintasi wilayah selatan Jawa.")
if olr_text:
    cause_parts.append(f"Analisis OLR menunjukkan kondisi {olr_text}.")
if sst_text:
    cause_parts.append(sst_text)
if ecmwf_desc:
    cause_parts.append(f"Berdasarkan data ECMWF/Open-Meteo, kondisi atmosfer menunjukkan {ecmwf_desc}.")
cause_text = " ".join(cause_parts)

# Ringkasan wilayah
high_list = df[df["kategori"] == "Tinggi"]["wilayah"].tolist()
med_list = df[df["kategori"] == "Sedang"]["wilayah"].tolist()
low_list = df[df["kategori"] == "Rendah"]["wilayah"].tolist()

def join_list(lst):
    return ", ".join(lst) if lst else "-"

blocks_text = (
    f"Wilayah dengan potensi **TINGGI (≥{high_thr}%)**: {join_list(high_list)}.\n\n"
    f"Wilayah dengan potensi **SEDANG ({low_thr}–{high_thr}%)**: {join_list(med_list)}.\n\n"
    f"Wilayah dengan potensi **RENDAH (<{low_thr}%)**: {join_list(low_list)}."
)

advice = (
    "BMKG Juanda menghimbau masyarakat untuk tetap waspada terhadap potensi hujan lebat "
    "disertai petir dan angin kencang. Wilayah pegunungan dan rawan longsor agar "
    "meningkatkan kewaspadaan terhadap bencana hidrometeorologi. "
    "Pantau terus informasi resmi dari BMKG Juanda."
)

release = f"""
PRESS RELEASE KEWASPADAAN CUACA EKSTREM DI JAWA TIMUR
Nomor: {nomor}
Periode: {periode}
Tanggal Keluaran: {tanggal}

{intro}

{cause_text}

{blocks_text}

{advice}

BMKG Stasiun Meteorologi Juanda
"""

st.code(textwrap.dedent(release), language="markdown")

st.download_button("⬇️ Unduh Press Release (.txt)", release.encode("utf-8"), file_name=f"press_release_jatim_{tanggal}.txt", mime="text/plain")
st.download_button("⬇️ Unduh Data (.csv)", df.to_csv(index=False).encode("utf-8"), file_name=f"probabilitas_jatim_{tanggal}.csv", mime="text/csv")

st.success("✅ Selesai — press release dan visualisasi siap digunakan.")
