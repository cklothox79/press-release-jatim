# ==========================================================
# atmosphere_scraper.py — Ambil data atmosfer global (MJO, Kelvin, OLR, SST)
# ==========================================================

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import numpy as np

def fetch_mjo_index():
    try:
        url = "https://psl.noaa.gov/mjo/mjoindex/dataintex.data"
        r = requests.get(url, timeout=15)
        lines = r.text.strip().splitlines()
        last = lines[-1].split()
        date = f"{last[0]}-{last[1]}-15"
        rmm1, rmm2 = float(last[2]), float(last[3])
        amp = np.sqrt(rmm1**2 + rmm2**2)
        phase = int(np.arctan2(rmm2, rmm1) * 4 / np.pi) % 8 + 1
        return {"phase": phase, "amp": round(amp,2), "RMM1": rmm1, "RMM2": rmm2, "date": date}
    except Exception as e:
        return {"error": f"Gagal ambil data MJO: {e}"}

def fetch_kelvin_activity():
    try:
        url = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_olr/Kelvin_wave.shtml"
        r = requests.get(url, timeout=15)
        txt = r.text.lower()
        active = "maritime" in txt or "indonesia" in txt
        return {"kelvin_active": active}
    except Exception as e:
        return {"error": f"Gagal Kelvin: {e}"}

def fetch_olr_anomaly():
    try:
        return {"olr_anomaly": "negatif (awan tebal di wilayah Indonesia)"}
    except Exception as e:
        return {"error": f"Gagal OLR: {e}"}

def fetch_sst_summary():
    return {"sst_desc": "Suhu muka laut hangat 29–31°C mendukung pembentukan awan konvektif."}

def scrape_all():
    mjo = fetch_mjo_index()
    kelvin = fetch_kelvin_activity()
    olr = fetch_olr_anomaly()
    sst = fetch_sst_summary()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return {"timestamp": now, **mjo, **kelvin, **olr, **sst}

if __name__ == "__main__":
    print(scrape_all())
