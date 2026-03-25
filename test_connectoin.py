import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("MOTHERDUCK_TOKEN")

try:
    conn = duckdb.connect(f"md:?motherduck_token={token}")
    print("✅ Koneksi ke MotherDuck berhasil!")
except Exception as e:
    print(f"Gagal Koneksi: {e}")
