# modules/gdrive_utils.py
import json
import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials


# ====== KONFIGURASI ======
FOLDER_ID = "1H8bWJS434PTqvr1fCmHkCPpOwcQjCQqC"  # Ganti dengan ID folder Google Drive kamu


def get_drive():
    """
    Autentikasi ke Google Drive menggunakan Service Account.
    File kredensial dibaca langsung dari st.secrets (bukan dari file lokal).
    """
    try:
        # Pastikan data kredensial ada di secrets.toml
        if "gcp_service_account" not in st.secrets:
            st.error("❌ Kredensial Google Drive belum diset di secrets.toml!")
            return None

        creds_data = dict(st.secrets["gcp_service_account"])

        # Buat kredensial Service Account
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_data,
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/drive.file",
            ],
        )

        # Autentikasi Drive
        drive = GoogleDrive(credentials)
        return drive

    except Exception as e:
        st.error(f"⚠️ Gagal autentikasi ke Google Drive: {e}")
        return None


def upload_to_gdrive(local_path, filename):
    """
    Upload file ke Google Drive menggunakan Service Account.
    Mengembalikan URL publik yang bisa langsung ditampilkan di Streamlit.
    """
    drive = get_drive()
    if not drive:
        st.error("❌ Gagal inisialisasi Google Drive.")
        return None

    try:
        # Buat file baru di folder tujuan
        gfile = drive.CreateFile({
            "title": filename,
            "parents": [{"id": FOLDER_ID}]
        })
        gfile.SetContentFile(local_path)
        gfile.Upload()

        # Jadikan publik agar bisa diakses semua orang
        gfile.InsertPermission({
            "type": "anyone",
            "role": "reader"
        })

        file_id = gfile["id"]
        public_url = f"https://drive.google.com/uc?export=view&id={file_id}"

        print(f"✅ Upload sukses: {filename}")
        print(f"🌐 URL publik: {public_url}")

        return public_url

    except Exception as e:
        st.error(f"⚠️ Upload ke Google Drive gagal: {e}")
        return None