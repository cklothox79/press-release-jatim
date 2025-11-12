# modules/ecmwf_fetcher.py
# Fetch summary of recent atmosphere variables using Open-Meteo (which provides ECMWF model endpoints)
# If Open-Meteo or ECMWF service unavailable, returns error message gracefully.

import requests
from datetime import datetime, timedelta

def fetch_ecmwf_summary(lat=-7.3, lon=112.7):
    """
    Use Open-Meteo API to fetch recent hourly values (temperature_2m, relative_humidity_2m, precipitation, cloudcover).
    The Open-Meteo API supports different models; by default uses its available models. This is a lightweight summary.
    """
    try:
        end = datetime.utcnow()
        start = end - timedelta(hours=6)
        # format datetimes in ISO without microseconds
        start_iso = start.replace(minute=0, second=0, microsecond=0).isoformat() + "Z"
        end_iso = end.replace(minute=0, second=0, microsecond=0).isoformat() + "Z"

        url = (
            "https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&hourly=temperature_2m,relativehumidity_2m,precipitation,cloudcover"
            f"&start={start_iso}&end={end_iso}&timezone=UTC"
        )
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json().get("hourly", {})
        # get last available index
        if not data:
            return {"error": "No hourly data returned from Open-Meteo."}
        idx = -1
        temp = data.get("temperature_2m", [None])[idx]
        rh = data.get("relativehumidity_2m", [None])[idx]
        rain = data.get("precipitation", [0])[idx]
        cloud = data.get("cloudcover", [None])[idx]
        desc = f"Suhu {temp}°C, RH {rh}%, curah hujan {rain} mm/jam, tutupan awan {cloud}% (lokasi: {lat},{lon})"
        return {"ecmwf_temp": temp, "ecmwf_rh": rh, "ecmwf_rain": rain, "ecmwf_cloud": cloud, "desc": desc}
    except Exception as e:
        return {"error": f"Gagal ambil ECMWF/Open-Meteo: {e}"}

if __name__ == "__main__":
    print(fetch_ecmwf_summary())
