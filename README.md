# 🌦️ TAFFWARR Fusion - Jawa Timur Extreme Weather Alert

Sistem otomatis untuk menghasilkan **Press Release Kewaspadaan Cuaca Ekstrem Jawa Timur** berbasis analisis TAFFWARR Fusion, radar BMKG Juanda, dan dinamika atmosfer global (MJO, Kelvin, OLR, SST).

## 📁 Struktur Repo
```
taffwarr_fusion_repo/
├─ app.py                  # Streamlit utama
├─ modules/
│   ├─ atmosphere_scraper.py # Modul pengambil data atmosfer global
│   └─ (modul tambahan lain)
├─ data/
│   ├─ fusion_sample.csv     # Contoh data output TAFFWARR Fusion
│   └─ geo_jatim.json        # Peta batas kabupaten (opsional)
└─ README.md
```

## 🚀 Fitur Utama
- 🧠 Membaca hasil TAFFWARR Fusion (CSV)
- 🌏 Scraping otomatis dinamika atmosfer (MJO, Kelvin, OLR, SST)
- 🛰️ Menampilkan radar BMKG Juanda secara langsung
- 📰 Menghasilkan Press Release Otomatis (TXT/DOCX)

## ⚙️ Cara Menjalankan
```bash
pip install streamlit pandas numpy requests beautifulsoup4 python-docx
streamlit run app.py
```

## 📡 Sumber Data
- BMKG Juanda Radar: [https://stamet-juanda.bmkg.go.id/radar/](https://stamet-juanda.bmkg.go.id/radar/)
- NOAA PSL MJO Index: [https://psl.noaa.gov/mjo/mjoindex/](https://psl.noaa.gov/mjo/mjoindex/)
- NOAA CPC Kelvin Wave/OLR: [https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_olr/](https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_olr/)

---
Made with ❤️ by Kawan AI & Ferri Kusuma
