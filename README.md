# 🏨 HotelOps: Multi-Source Market Intelligence Pipeline

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Airflow](https://img.shields.io/badge/Orchestrator-Apache%20Airflow-red.svg)](https://airflow.apache.org/)
[![dbt](https://img.shields.io/badge/Transformation-dbt-orange.svg)](https://www.getdbt.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**HotelOps** adalah platform *end-to-end data engineering* yang dirancang untuk mengotomatisasi pengumpulan, pembersihan, dan visualisasi data harga hotel secara real-time. Proyek ini membandingkan data dari tiga kompetitor besar di Indonesia: **Traveloka**, **Agoda**, dan **Skyscanner**.

---

## 🏗️ Arsitektur Sistem

Proyek ini mengikuti prinsip **Modern Data Stack** dengan alur kerja sebagai berikut:

[Image of an end-to-end data engineering architecture diagram showing Playwright, Airflow, dbt, Snowflake, and Flask]

1.  **Ingestion (Playwright):** Bot melakukan pencarian dinamis berdasarkan lokasi dan tanggal pada SPA (*Single Page Application*).
2.  **Orchestration (Airflow):** Mengatur jadwal scraping harian, menangani *retry logic*, dan ketergantungan antar tugas.
3.  **Storage (Data Lake):** Data mentah disimpan dalam format JSON sebagai *Landing Layer*.
4.  **Transformation (dbt):** Mengolah data mentah menjadi tabel siap saji (Medallion Architecture: Bronze -> Silver -> Gold).
5.  **Serving (Flask):** Menyediakan User Interface bagi pengguna bisnis untuk melihat perbandingan harga ter-update.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.11+ |
| **Scraping** | Playwright (Stealth Mode) |
| **Orchestrator** | Apache Airflow (Astro CLI) |
| **Data Warehouse** | MotherDuck |
| **Data Modeling** | dbt (Data Build Tool) |
| **Backend & UI** | Flask, Bootstrap 5, Chart.js |

---

## 📂 Struktur Proyek

```text
hotel-ops/
├── dags/                  # Airflow DAGs (Workflow definition)
├── scrapers/              # Playwright scripts for Traveloka, Agoda, Skyscanner
├── dbt_project/           # dbt models, macros, and tests
├── webapp/                # Flask Application (UI/Frontend)
│   ├── static/            # CSS, JS, and Images
│   └── templates/         # HTML Dashboard
├── config/                # Metadata-driven config (cities, dates)
├── data/                  # Local data lake (Raw & Processed)
└── pyproject.toml         # Project dependencies
└── README.md              # Project documentation