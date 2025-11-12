# ==========================================================
# TAFFWARR Fusion - Jawa Timur Extreme Weather Alert System
# Streamlit App utama untuk press release otomatis BMKG Juanda
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import textwrap
import requests
from modules.atmosphere_scraper import scrape_all

# --- SETUP ---
st.set_page_config(page_title="🌦️ TAFFWARR Fusion - Press Release", layout="wide")
st.title("🌩️ TAFFWARR Fusion — Press Release Otomatis Cuaca Ekstrem Jawa Timur")

st.markdown(
    "Sistem ini menggabungkan **TAFFWARR Fusion**, **Radar BMKG Juanda**, dan **Dinamika Atmosfer Global (MJO, Kelvin, OLR, SST)** "
    "untuk menghasilkan narasi otomatis *Press Release Kewaspadaan Cuaca Ekstrem* di wilayah Jawa Timur."
)

# ==========================================================
# SIDEBAR: Informasi dan Input
# ==========================================================
st.sidebar.header("⚙️ Pengaturan")
periode = st.sidebar.text_input("Periode", value="13–19 November 2025")
tanggal = st.sidebar.date_input("Tanggal Terbit", value=datetime.utcnow().date())
nomor = st.sidebar.text_input("Nomor Naskah", value="PR-BMKG-JD/001/2025")
high_thr = st.sidebar.slider("Ambang Potensi Tinggi (%)", 50, 90, 70)
low_thr = st.sidebar.slider("Ambang Potensi Rendah (%)", 10, 50, 40)

# ==========================================================
# PANEL DINAMIKA ATMOSFER
# ==========================================================
st.sidebar.subheader("🌏 Dinamika Atmosfer Saat Ini")
atmo_data = scrape_all()
st.sidebar.json(atmo_data)

# ==========================================================
# UPLOAD / SAMPLE DATA FUSION
# ==========================================================
st.markdown("## 📥 Data TAFFWARR Fusion")
uploaded = st.file_uploader("Unggah file CSV hasil Fusion", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    st.success("File berhasil dimuat.")
else:
    st.info("Belum ada CSV diunggah — menggunakan contoh bawaan `data/fusion_sample.csv`.")
    df = pd.read_csv("data/fusion_sample.csv")

# Validasi
if "wilayah" not in df.columns or "probabilitas" not in df.columns:
    st.error("File harus memiliki kolom 'wilayah' dan 'probabilitas'.")
    st.stop()

df["probabilitas"] = pd.to_numeric(df["probabilitas"], errors="coerce").fillna(0).clip(0,100)

# Klasifikasi
def kategori(p):
    if p >= high_thr: return "Tinggi"
    elif p >= low_thr: return "Sedang"
    else: return "Rendah"

df["kategori"] = df["probabilitas"].apply(kategori)

# ==========================================================
# RADAR PANEL
# ==========================================================
st.markdown("## 🛰️ Radar BMKG Juanda (Live)")
radar_url = "https://stamet-juanda.bmkg.go.id/radar/data/composite_latest.png"
try:
    st.image(radar_url, caption="Citra Reflektivitas WOFI (Terbaru)", use_column_width=True)
except:
    st.warning("Radar Juanda tidak dapat dimuat saat ini.")

# ==========================================================
# PRESS RELEASE GENERATOR
# ==========================================================
st.markdown("## 📰 Press Release Otomatis")

# Dinamika Atmosfer untuk narasi
mjo = atmo_data.get("phase", "?")
kelvin = atmo_data.get("kelvin_active", False)
sst_text = atmo_data.get("sst_desc", "")
olr_text = atmo_data.get("olr_anomaly", "")

intro = (
    f"Hampir seluruh wilayah Jawa Timur telah memasuki musim hujan. Berdasarkan hasil analisis TAFFWARR Fusion per {tanggal}, "
    "terindikasi adanya potensi peningkatan cuaca ekstrem dalam sepekan ke depan yang berdampak terhadap aktivitas masyarakat."
)

cause = (
    f"Fenomena ini dipicu oleh aktifnya MJO pada fase {mjo}, "
    f"{'gelombang Kelvin yang melintas di selatan Jawa, ' if kelvin else ''}"
    f"serta kondisi {olr_text}. "
    f"{sst_text}"
)

wil_high = ", ".join(df.query("kategori == 'Tinggi'")["wilayah"])
wil_med = ", ".join(df.query("kategori == 'Sedang'")["wilayah"])
wil_low = ", ".join(df.query("kategori == 'Rendah'")["wilayah"])

regions = f"""
Wilayah potensi **Tinggi**: {wil_high or '-'}
Wilayah potensi **Sedang**: {wil_med or '-'}
Wilayah potensi **Rendah**: {wil_low or '-'}
"""

closing = (
    "BMKG Juanda menghimbau masyarakat untuk tetap waspada terhadap kemungkinan hujan sedang hingga lebat yang dapat disertai petir dan angin kencang. "
    "Daerah bertopografi curam diimbau untuk meningkatkan kewaspadaan terhadap banjir dan longsor. "
    "Pantau informasi cuaca terkini melalui [https://stamet-juanda.bmkg.go.id](https://stamet-juanda.bmkg.go.id)."
)

release = f"""PRESS RELEASE KEWASPADAAN CUACA EKSTREM DI JAWA TIMUR
Periode: {periode}
Nomor: {nomor}
Tanggal: {tanggal}

{intro}

{cause}

{regions}

{closing}
"""

st.code(release, language="text")

# ==========================================================
# DOWNLOAD
# ==========================================================
txt = release.encode("utf-8")
st.download_button("⬇️ Unduh Press Release (.txt)", txt, file_name="press_release_jatim.txt")

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Unduh Ringkasan Wilayah (.csv)", csv, file_name="probabilitas_jatim.csv")
