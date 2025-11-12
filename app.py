# app.py
# TAFFWARR Fusion - Streamlit Press Release Generator (Jawa Timur)
# - Auto-generate fusion data jika tidak ada upload (seed based on day of year)
# - Integrasi: atmosphere_scraper (MJO/Kelvin/OLR/SST) + ecmwf_fetcher (Open-Meteo/ECMWF)
# - Live radar image dari BMKG Juanda

import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
from io import BytesIO
import textwrap
import os

# modules
from modules.atmosphere_scraper import scrape_all as scrape_atmosphere
from modules.ecmwf_fetcher import fetch_ecmwf_summary

# --- Page config ---
st.set_page_config(page_title="TAFFWARR Fusion — Press Release Jatim", layout="wide")
st.title("🌩️ TAFFWARR Fusion — Press Release Otomatis (Jawa Timur)")
st.markdown("Sistem otomatis untuk menghasilkan press release kewaspadaan cuaca ekstrem di Jawa Timur. "
            "Menggabungkan keluaran Fusion, radar Juanda, MJO/Kelvin/OLR/SST, dan data ECMWF (Open-Meteo).")

# --- Sidebar: settings ---
st.sidebar.header("⚙️ Pengaturan")
periode = st.sidebar.text_input("Periode (contoh: 13–19 November 2025)", value="13–19 November 2025")
tanggal = st.sidebar.date_input("Tanggal Terbit", value=datetime.utcnow().date())
nomor = st.sidebar.text_input("Nomor Naskah", value="PR-BMKG-JD/001/2025")
high_thr = st.sidebar.slider("Ambang Potensi Tinggi (%)", 50, 90, 70)
low_thr = st.sidebar.slider("Ambang Potensi Rendah (%)", 10, 50, 40)
auto_seed_toggle = st.sidebar.checkbox("Gunakan seed harian untuk auto-data (bonus)", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🌏 Dinamika Atmosfer Saat Ini")
with st.spinner("Mengambil data dinamika atmosfer..."):
    atmo = scrape_atmosphere()
    st.sidebar.json(atmo)

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Data ECMWF (Open-Meteo / ECMWF)")
with st.spinner("Mengambil ringkasan ECMWF/Open-Meteo..."):
    ecmwf = fetch_ecmwf_summary()
    st.sidebar.json(ecmwf)

# --- Data input: upload or auto-generate ---
st.markdown("## 📥 Data TAFFWARR Fusion (probabilitas per kabupaten/kota)")
uploaded = st.file_uploader("Unggah file CSV hasil Fusion (kolom minimal: wilayah, probabilitas)", type=["csv"])

# path for auto-save
os.makedirs("data", exist_ok=True)
auto_path = "data/fusion_auto.csv"
sample_path = "data/fusion_sample.csv"

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
    try:
        df = pd.read_csv(uploaded)
        st.success("File CSV berhasil dimuat dari unggahan.")
    except Exception as e:
        st.error(f"Gagal membaca CSV: {e}")
        df = None
else:
    # prefer auto saved if exists and is recent; else regenerate
    seed = None
    if auto_seed_toggle:
        seed = datetime.now().timetuple().tm_yday
    if os.path.exists(auto_path):
        try:
            df = pd.read_csv(auto_path)
            st.info(f"Memuat data otomatis dari `{auto_path}` ({len(df)} wilayah).")
        except:
            df, seed = generate_auto_data(seed)
            st.success(f"Data otomatis baru dibuat (seed {seed}) — file disimpan di `{auto_path}`.")
    else:
        df, seed = generate_auto_data(seed)
        st.success(f"Data otomatis dibuat untuk {len(df)} wilayah (seed {seed}). File disimpan di `{auto_path}`.")

# validate
if df is None or "wilayah" not in df.columns or "probabilitas" not in df.columns:
    st.error("Data harus memiliki kolom 'wilayah' dan 'probabilitas'. Perbaiki file atau gunakan auto-data.")
    st.stop()

# normalize
df["probabilitas"] = pd.to_numeric(df["probabilitas"], errors="coerce").fillna(0).clip(0,100)
df["wilayah"] = df["wilayah"].astype(str)

# classify
def classify(p):
    if p >= high_thr:
        return "Tinggi"
    if p >= low_thr:
        return "Sedang"
    return "Rendah"

df["kategori"] = df["probabilitas"].apply(classify)
df = df.sort_values("probabilitas", ascending=False).reset_index(drop=True)

# --- Main layout: table + radar + press release ---
col1, col2 = st.columns([1.2, 1])
with col1:
    st.subheader("Tabel Ringkasan Probabilitas")
    st.dataframe(df.style.format({"probabilitas":"{:.1f}"}), height=420)
    st.markdown("### Statistik ringkasan")
    st.write(df["probabilitas"].describe())

with col2:
    st.subheader("🛰️ Radar BMKG Juanda (Live)")
    radar_url = "https://stamet-juanda.bmkg.go.id/radar/data/composite_latest.png"
    try:
        st.image(radar_url, caption="Citra Reflektivitas Komposit (WOFI Juanda) — terbaru", use_column_width=True)
    except:
        st.warning("Tidak dapat memuat radar Juanda saat ini.")
    st.markdown("---")
    st.subheader("Informasi Dinamika & ECMWF")
    st.markdown("**Dinamika Atmosfer**")
    st.write(atmo)
    st.markdown("**Ringkasan ECMWF / Open-Meteo**")
    st.write(ecmwf)

st.markdown("---")
st.subheader("📰 Preview — Press Release Otomatis")

# build narrative
mjo_phase = atmo.get("phase", "?")
mjo_amp = atmo.get("amplitude", atmo.get("amp", "?"))
kelvin_active = bool(atmo.get("kelvin_active", False))
olr_text = atmo.get("olr_anomaly", "")
sst_text = atmo.get("sst_desc", "")
ecmwf_desc = ecmwf.get("desc", "")

intro = (f"Hampir seluruh wilayah Jawa Timur telah memasuki musim hujan. Berdasarkan hasil analisis TAFFWARR Fusion per {tanggal}, "
         "terindikasi adanya potensi peningkatan cuaca ekstrem dalam sepekan ke depan yang berpotensi berdampak terhadap aktivitas masyarakat di sejumlah wilayah.")

cause_parts = []
cause_parts.append(f"Fenomena ini dipengaruhi oleh MJO (fase {mjo_phase}, amplitudo {mjo_amp}).")
if kelvin_active:
    cause_parts.append("Masih terdapat gelombang atmosfer Kelvin yang melintas di wilayah selatan Jawa.")
if olr_text:
    cause_parts.append(f"Analisis OLR menunjukkan kondisi: {olr_text}.")
if sst_text:
    cause_parts.append(sst_text)
if ecmwf_desc:
    cause_parts.append(f"Selain itu data model (ECMWF/Open-Meteo) menunjukkan: {ecmwf_desc}")

cause_text = " ".join(cause_parts)

high_list = df[df["kategori"] == "Tinggi"]["wilayah"].tolist()
med_list = df[df["kategori"] == "Sedang"]["wilayah"].tolist()
low_list = df[df["kategori"] == "Rendah"]["wilayah"].tolist()

def list_to_text(lst):
    return ", ".join(lst) if lst else "-"

blocks_text = (
    f"Wilayah dengan potensi TINGGI (≥ {high_thr}%): {list_to_text(high_list)}\n\n"
    f"Wilayah dengan potensi SEDANG (≥ {low_thr}% — < {high_thr}%): {list_to_text(med_list)}\n\n"
    f"Wilayah dengan potensi RENDAH (< {low_thr}%): {list_to_text(low_list)}"
)

advice = ("BMKG Juanda menghimbau masyarakat dan instansi terkait untuk tetap waspada terhadap potensi hujan sedang hingga lebat "
          "yang dapat disertai petir dan angin kencang. Daerah bergunung/curam diimbau meningkatkan kewaspadaan terhadap banjir bandang dan longsor. "
          "Pantau selalu informasi peringatan dini melalui saluran resmi BMKG Juanda.")

release = f"""PRESS RELEASE KEWASPADAAN CUACA EKSTREM DI JAWA TIMUR
Periode: {periode}
Nomor: {nomor}
Tanggal keluaran: {tanggal}

{intro}

{cause_text}

{blocks_text}

{advice}

Demikian informasi kewaspadaan cuaca ekstrem di wilayah Jawa Timur hasil analisis TAFFWARR Fusion.
BMKG Juanda
"""

st.code(textwrap.dedent(release), language="text")

# --- Download buttons ---
st.markdown("### ⬇️ Unduh")
st.download_button("Unduh press release (.txt)", release.encode("utf-8"), file_name=f"press_release_jatim_{tanggal}.txt", mime="text/plain")
st.download_button("Unduh ringkasan wilayah (.csv)", df.to_csv(index=False).encode("utf-8"), file_name=f"probabilitas_jatim_{tanggal}.csv", mime="text/csv")

# optional: show per-wilayah short block
st.markdown("---")
st.subheader("Blok per kabupaten/kota (copyable)")
for _, r in df.iterrows():
    reasons = []
    if "MJO" in atmo or "phase" in atmo:
        reasons.append(f"MJO fase {mjo_phase}")
    if kelvin_active:
        reasons.append("Kelvin wave")
    if "sst_desc" in atmo:
        reasons.append(atmo.get("sst_desc"))
    # include ECMWF short
    reasons.append(ecmwf.get("desc", ""))
    reason_text = "; ".join([x for x in reasons if x])
    st.code(f"{r['wilayah']} — Prob: {r['probabilitas']:.1f}% (Kategori: {r['kategori']}). Penyebab: {reason_text}")

st.success("Selesai. Tekan tombol unduh untuk menyimpan keluaran.")
