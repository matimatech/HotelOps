# 🏨 HotelOps — Platform Intelijen Harga Hotel Indonesia

> Memantau dan membandingkan harga hotel secara otomatis dari **Agoda**, **Traveloka**, dan **Tiket.com** untuk membantu pemilik hotel kecil-menengah Indonesia menganalisis harga kompetitor — insight yang selama ini hanya bisa diakses hotel besar dengan tools mahal.

---

## 🔗 Live Demo
> 🚧 Coming soon — Streamlit dashboard akan tersedia setelah pipeline selesai

---

## 📌 Latar Belakang

Pemilik hotel kecil-menengah di Indonesia seringkali tidak tahu:
- Apakah harga mereka kompetitif dibanding hotel sejenis di area yang sama?
- Platform mana (Agoda, Traveloka, Tiket.com) yang memberikan harga paling murah untuk hotel yang sama?
- Kapan kompetitor biasanya menurunkan harga?

Tools seperti **OTA Insight** atau **RateGain** memang bisa menjawab pertanyaan ini, tapi harganya jutaan rupiah per bulan — tidak terjangkau untuk hotel kecil.

**HotelOps hadir sebagai solusi open-source** yang melakukan hal yang sama: scraping harga hotel secara otomatis setiap hari, memproses datanya, dan menyajikannya dalam dashboard yang mudah dipahami.

---

## 🎯 Business Questions yang Dijawab

### 💰 Rate Parity Analysis
- Apakah hotel X menjual harga yang sama di semua platform?
- Platform mana yang paling sering memberikan harga lebih murah untuk hotel yang sama?
- Seberapa besar rata-rata selisih harga antar platform?

### 📉 Competitor Pricing Movement
- Kapan kompetitor biasanya menurunkan harga? (hari dalam seminggu, H-berapa sebelum check-in)
- Hotel mana di sekitar area tertentu yang paling agresif dalam memberikan diskon?
- Ada pola musiman harga di destinasi Bali, Jakarta, atau Yogyakarta?

### 📊 Market Positioning
- Dibanding kompetitor sekelas (bintang sama, area sama), apakah harga suatu hotel kompetitif?
- Apakah hotel dengan rating lebih tinggi selalu menetapkan harga lebih mahal?

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                    DATA SOURCES                         │
│         Agoda · Traveloka · Tiket.com                   │
└──────────────────────┬──────────────────────────────────┘
                       │ Playwright (browser automation)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  ORCHESTRATION                          │
│         Airflow DAG + GitHub Actions (daily)            │
└──────────────────────┬──────────────────────────────────┘
                       │ Raw JSON/CSV
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 DATA WAREHOUSE                          │
│              MotherDuck (DuckDB cloud)                  │
└──────────────────────┬──────────────────────────────────┘
                       │ SQL transformation
                       ▼
┌─────────────────────────────────────────────────────────┐
│               DATA TRANSFORMATION                       │
│                 dbt (staging → mart)                    │
└──────────────────────┬──────────────────────────────────┘
                       │ Clean data
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   DASHBOARD                             │
│                Streamlit (web app)                      │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Tool | Fungsi |
|---|---|---|
| Scraping | Python + Playwright | Otomasi browser untuk ambil data harga |
| Orkestrasi | Apache Airflow | Scheduling & monitoring pipeline harian |
| CI/CD | GitHub Actions | Trigger otomatis scraping setiap hari |
| Data Warehouse | MotherDuck | Penyimpanan & query data cloud |
| Transformasi | dbt | Cleaning, modeling, dan testing data |
| Dashboard | Streamlit | Visualisasi & presentasi insight |

---

## 📍 Cakupan Data

### Kota yang Dipantau
| Kota | Alasan |
|---|---|
| 🌴 Bali | Destinasi wisata terbesar, volume hotel paling tinggi |
| 🏙️ Jakarta | Pusat bisnis, segmen hotel korporat |
| 🏛️ Yogyakarta | Destinasi wisata budaya, harga sangat variatif |

### Platform yang Dipantau
- **Agoda** ✅ (scraper selesai)
- **Traveloka** 🚧 (dalam pengerjaan)
- **Tiket.com** 🚧 (dalam pengerjaan)

### Metodologi Pengambilan Data
- Scraping dilakukan **setiap hari pukul 07.00 WIB**
- Untuk setiap hotel, diambil harga untuk waktu:
  - **H+7** (check-in 7 hari ke depan) → representasi harga near-ter
- Check-out selalu **1 malam setelah check-in** untuk konsistensi perbandingan
- Data scraping dilakukan untuk **tujuan riset dan akademis**

---

## 🗂️ Struktur Database

### Tabel `prices` (Fact Table)

```sql
CREATE TABLE prices (
    price_id          VARCHAR PRIMARY KEY,
    hotel_name        VARCHAR,
    city              VARCHAR,
    star_rating       INTEGER,
    
    platform          VARCHAR,       -- 'agoda' / 'traveloka' / 'tiket'
    check_in_date     DATE,
    check_out_date    DATE,
    price_idr         BIGINT,        -- harga final
    rating            FLOAT,
    review_count      INTEGER,
    scraped_at        TIMESTAMP
);
```

---

## 🗃️ Struktur dbt Models

```
dbt/
├── models/
│   ├── staging/                  ← bersihkan data mentah per platform
│   │   ├── stg_agoda.sql
│   │   ├── stg_traveloka.sql
│   │   └── stg_tiket.sql
│   ├── intermediate/             ← gabungkan & standardisasi
│   │   └── int_hotels_unified.sql
│   └── marts/                    ← siap untuk dashboard
│       ├── mart_price_comparison.sql
│       ├── mart_price_trend.sql
│       └── mart_rate_parity.sql
└── tests/
    └── schema.yml
```

---

## 📁 Struktur Proyek

```
hotelops/
├── scrapers/
│   ├── agoda/
│   │   ├── scraper.py
│   │   └── parser.py
│   ├── traveloka/
│   │   ├── scraper.py
│   │   └── parser.py
│   ├── tiket/
│   │   ├── scraper.py
│   │   └── parser.py
│   └── utils/
│       ├── logger.py
│       └── retry.py
├── dags/
│   └── hotelops_pipeline.py      ← Airflow DAG
├── dbt/
│   ├── models/
│   └── dbt_project.yml
├── dashboard/
│   └── app.py                    ← Streamlit app
├── .github/
│   └── workflows/
│       └── daily_scrape.yml      ← GitHub Actions
├── requirements.txt
├── docker-compose.yml            ← untuk Airflow lokal
└── README.md
```

---

## 🚀 Cara Menjalankan Proyek

### 1. Clone Repository
```bash
git clone https://github.com/username/hotelops.git
cd hotelops
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Setup Environment Variables
```bash
cp .env.example .env
# Isi MOTHERDUCK_TOKEN di file .env
```

### 4. Jalankan Scraper Manual
```bash
python scrapers/agoda/scraper.py --city bali --days 7
```

### 5. Jalankan Airflow (via Docker)
```bash
docker-compose up -d
# Buka http://localhost:8080
```

### 6. Jalankan dbt
```bash
cd dbt
dbt run
dbt test
```

### 7. Jalankan Dashboard
```bash
streamlit run dashboard/app.py
```

---

## 📊 Dashboard Preview

> 🚧 Screenshot akan ditambahkan setelah dashboard selesai

Dashboard terdiri dari 3 halaman utama:

| Halaman | Deskripsi |
|---|---|
| 📍 Market Overview | Gambaran umum harga hotel per kota & platform |
| 🔍 Rate Parity Checker | Bandingkan harga satu hotel di semua platform |
| 📈 Price Trend | Tren harga historis per destinasi & periode |

---

## 📈 Progress

- [x] Scraper Agoda selesai
- [ ] Scraper Traveloka
- [ ] Scraper Tiket.com
- [ ] Setup MotherDuck & schema database
- [ ] dbt models (staging → mart)
- [ ] Airflow DAG
- [ ] GitHub Actions workflow
- [ ] Streamlit dashboard
- [ ] Deploy dashboard (Streamlit Cloud)

---

## ⚠️ Disclaimer

Proyek ini dibuat untuk **tujuan riset dan portofolio akademis**. Scraping dilakukan dengan memperhatikan:
- Jeda waktu antar request untuk menghindari beban server
- Tidak menyimpan data yang bersifat personal
- Data tidak digunakan untuk kepentingan komersial

---

## 👤 Author

**Muh. Afrizal Nur**


[![GitHub](https://img.shields.io/badge/GitHub-username-black?logo=github)](https://github.com/username)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-username-blue?logo=linkedin)](https://linkedin.com/in/username)
