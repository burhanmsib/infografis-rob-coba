import folium
from streamlit_folium import st_folium
from modules.utils import safe_float
import streamlit as st


def create_map(records, provinsi_filter=None, kabupaten_filter=None):
    """
    Membuat peta interaktif banjir rob menggunakan Folium.
    - Otomatis zoom ke provinsi / kabupaten jika filter diisi.
    - Menampilkan popup dengan gambar (jika ada).
    - Menangani error agar tidak crash saat data kosong atau invalid.
    """
    default_center = [-2.5489, 118.0149]  # Titik tengah Indonesia
    m = folium.Map(location=default_center, zoom_start=5)
    bounds = []

    # Filter hanya record dengan koordinat valid
    valid_records = []
    for r in records:
        lat = safe_float(r.get("Latitude"), None)
        lon = safe_float(r.get("Longitude"), None)
        if lat is not None and lon is not None:
            valid_records.append(r)

    if not valid_records:
        st.warning("⚠️ Tidak ada titik dengan koordinat valid untuk ditampilkan di peta.")
        return st_folium(m, height=900, use_container_width=True)

    lat_center, lon_center = None, None

    # ==== Filter Kabupaten ====
    if kabupaten_filter and kabupaten_filter.strip():
        kab_filter = kabupaten_filter.lower().strip()
        kab_records = [
            r for r in valid_records
            if kab_filter in r.get("Kabupaten", "").lower().strip()
        ]
        if kab_records:
            lat_center = sum(safe_float(r["Latitude"]) for r in kab_records) / len(kab_records)
            lon_center = sum(safe_float(r["Longitude"]) for r in kab_records) / len(kab_records)
            m.location = [lat_center, lon_center]
            m.zoom_start = 10
        else:
            st.info(f"📍 Tidak ditemukan koordinat valid untuk kabupaten: {kabupaten_filter}")

    # ==== Filter Provinsi ====
    elif provinsi_filter and provinsi_filter.strip():
        prov_filter = provinsi_filter.lower().strip()
        prov_records = [
            r for r in valid_records
            if prov_filter in r.get("Provinsi", "").lower().strip()
        ]
        if prov_records:
            lat_center = sum(safe_float(r["Latitude"]) for r in prov_records) / len(prov_records)
            lon_center = sum(safe_float(r["Longitude"]) for r in prov_records) / len(prov_records)
            m.location = [lat_center, lon_center]
            m.zoom_start = 7
        else:
            st.info(f"📍 Tidak ditemukan koordinat valid untuk provinsi: {provinsi_filter}")

    # ==== Tambahkan marker ====
    for r in valid_records:
        lat = safe_float(r["Latitude"])
        lon = safe_float(r["Longitude"])
        lokasi = r.get("Lokasi", "")
        kab = r.get("Kabupaten", "")
        prov = r.get("Provinsi", "")
        tgl = r.get("Tanggal", "")
        img = r.get("Gambar", "")

        # --- Perbaikan agar link Google Drive bisa tampil langsung ---
        if img and "drive.google.com" in img:
            if "uc?id=" not in img:
                # Ambil file_id dari berbagai format URL
                if "/d/" in img:
                    file_id = img.split("/d/")[1].split("/")[0]
                    img = f"https://drive.google.com/uc?export=view&id={file_id}"
                elif "id=" in img:
                    file_id = img.split("id=")[-1]
                    img = f"https://drive.google.com/uc?export=view&id={file_id}"

        # Buat konten popup
        popup_html = f"""
        <b>{lokasi}</b><br>
        {kab}, {prov}<br>
        📅 {tgl}<br>
        """
        if img:
            popup_html += f'<img src="{img}" width="220"><br>'
        else:
            popup_html += "<i>📷 Gambar tidak tersedia</i><br>"

        # Tambahkan marker ke peta
        try:
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{lokasi} ({kab})"
            ).add_to(m)
            bounds.append([lat, lon])
        except Exception:
            continue  # jika ada data yang tidak valid, skip

    # ==== Auto zoom ====
    if not provinsi_filter and not kabupaten_filter:
        if len(bounds) == 1:
            m.location = bounds[0]
            m.zoom_start = 11
        elif len(bounds) > 1:
            m.fit_bounds(bounds)

    return st_folium(m, height=900, use_container_width=True)