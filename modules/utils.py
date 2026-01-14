import os
from datetime import datetime, date
from decimal import Decimal
import streamlit as st

# ======================== KONFIGURASI UPLOAD ========================
# Gunakan direktori temporary bawaan Streamlit Cloud agar kompatibel
UPLOAD_DIR = os.path.join(st.experimental_get_script_run_ctx().session_id if hasattr(st, "experimental_get_script_run_ctx") else os.getcwd(), "temp_uploads")

# Pastikan folder ada
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ======================== FILE HANDLING ========================
def save_uploaded_file(uploaded_file):
    """
    Simpan file upload ke folder sementara dan kembalikan path lengkap.
    Aman untuk Streamlit Cloud dan lingkungan lokal.
    """
    if uploaded_file is None:
        return None

    # Nama file aman (hapus path)
    filename = os.path.basename(uploaded_file.name)
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Jika nama sudah ada → tambahkan angka unik
    base, ext = os.path.splitext(file_path)
    counter, final_path = 1, file_path
    while os.path.exists(final_path):
        final_path = f"{base}_{counter}{ext}"
        counter += 1

    # Simpan ke disk sementara
    with open(final_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return final_path  # tidak perlu st.info agar UI tetap bersih


# ======================== KONVERSI NUMERIK ========================
def safe_float(value, default=0.0):
    """
    Konversi berbagai tipe (str, int, Decimal) menjadi float aman.
    Jika gagal -> return default (0.0).
    """
    if value is None or value == "":
        return default
    try:
        if isinstance(value, (float, int)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        s = str(value).strip().replace(",", ".")
        return float(s)
    except Exception:
        return default


# ======================== PARSE & FORMAT TANGGAL ========================
def parse_date_safe(val):
    """
    Ubah berbagai format tanggal (string / date) menjadi objek date (Python).
    Digunakan agar st.date_input tidak error saat nilai tanggal tidak standar.
    """
    if isinstance(val, date):
        return val
    if val is None:
        return None

    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None  # biarkan user pilih manual kalau parsing gagal


def to_db_date_str(d):
    """
    Ubah objek date menjadi format string 'YYYY-MM-DD' untuk disimpan di database.
    """
    if isinstance(d, date):
        return d.strftime("%Y-%m-%d")

    parsed = parse_date_safe(d)
    return parsed.strftime("%Y-%m-%d") if parsed else None