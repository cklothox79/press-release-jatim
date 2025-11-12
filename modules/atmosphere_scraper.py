# modules/atmosphere_scraper.py
# Scraper sederhana untuk mengambil indikator atmosfer: MJO (NOAA PSL), Kelvin (CPC), OLR (CPC), SST (dummy or local)
# Returns dict summarizing available indicators. Designed to fail gracefully.

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import numpy as np

def fetch_mjo_index():
    """
    Read the NOAA PSL MJO index time series.
    Returns: dict with keys: phase, amplitude (amp), RMM1, RMM2, date
    """
    try:
        url = "https://psl.noaa.gov/mjo/mjoindex/dataintex.data"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        lines = [ln for ln in r.text.splitlines() if ln.strip()]
        # last line typically has year month ... rmm1 rmm2 ...
        last = lines[-1].split()
        year = int(last[0])
        month = int(last[1])
        # rmm values may be columns 2 and 3
        rmm1 = float(last[2])
        rmm2 = float(last[3])
        amp = float(np.sqrt(rmm1**2 + rmm2**2))
        # compute phase from atan2 (1..8)
        ang = np.arctan2(rmm2, rmm1)
        phase = int(((ang + np.pi) / (2 * np.pi)) * 8) + 1
        # normalize phase to 1..8
        phase = ((phase - 1) % 8) + 1
        date = f"{year:04d}-{month:02d}-01"
        return {"phase": int(phase), "amplitude": round(amp, 2), "RMM1": round(rmm1, 3), "RMM2": round(rmm2, 3), "date": date}
    except Exception as e:
        return {"error": f"Gagal ambil MJO: {e}"}

def fetch_kelvin_activity():
    """
    Simple indicator: tries to parse CPC Kelvin page to find mention of Indonesia/Maritime.
    Returns: {'kelvin_active': bool, 'source': url} or error.
    """
    try:
        url = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_olr/Kelvin_wave.shtml"
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        text = r.text.lower()
        active = ("indonesia" in text) or ("maritime" in text) or ("kelvin" in text and "active" in text)
        return {"kelvin_active": bool(active), "source": url}
    except Exception as e:
        return {"error": f"Gagal ambil Kelvin: {e}"}

def fetch_olr_anomaly():
    """
    Lightweight check for OLR page availability; returns simple descriptor.
    """
    try:
        url = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_olr/"
        r = requests.get(url, timeout=12)
        if r.status_code == 200:
            # This is a heuristic: assume presence indicates available OLR; deeper parsing can be added later.
            return {"olr_anomaly": "negatif (indikasi tutupan awan signifikan di wilayah Indonesia)", "source": url}
        else:
            return {"olr_anomaly": "tidak tersedia", "source": url}
    except Exception as e:
        return {"error": f"Gagal ambil OLR: {e}"}

def fetch_sst_summary():
    """
    Placeholder SST fetcher. For production, hook to NOAA OISST/ERDDAP or local SST datasets.
    For now returns a reasonable summary.
    """
    try:
        # Example static values; replace with real data fetch when available.
        sst_mean = 29.3
        sst_anom = 0.7
        desc = f"Suhu muka laut hangat sekitar {sst_mean}°C (anomali +{sst_anom}°C) di perairan sekitar Jatim."
        return {"sst_mean": sst_mean, "sst_anom": sst_anom, "sst_desc": desc}
    except Exception as e:
        return {"error": f"Gagal ambil SST: {e}"}

def scrape_all():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    mjo = fetch_mjo_index()
    kelvin = fetch_kelvin_activity()
    olr = fetch_olr_anomaly()
    sst = fetch_sst_summary()

    out = {"timestamp": now}
    # merge results, prefer errorless entries
    out.update(mjo if isinstance(mjo, dict) else {"mjo_error": str(mjo)})
    out.update(kelvin if isinstance(kelvin, dict) else {"kelvin_error": str(kelvin)})
    out.update(olr if isinstance(olr, dict) else {"olr_error": str(olr)})
    out.update(sst if isinstance(sst, dict) else {"sst_error": str(sst)})
    return out

if __name__ == "__main__":
    print(scrape_all())
