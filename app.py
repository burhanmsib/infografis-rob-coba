import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import io

from modules import crud
from modules.utils import safe_float, parse_date_safe, to_db_date_str
from modules.map_visualization import create_map
from modules.wilayah import (
    load_wilayah_csv,
    get_provinsi,
    get_kabupaten,
    get_kecamatan
)
from login import login, logout
from pdf import generate_event_pdf, generate_multiple_events_pdf
from modules.infografis.service import generate_infografis_rob


# ======================== KONFIGURASI AWAL ========================
st.set_page_config(
    page_title="Peta Interaktif Banjir Rob BMKG",
    layout="wide"
)

st.markdown(
    "<h1 style='text-align:center;'>PETA INTERAKTIF BANJIR ROB BMKG</h1>",
    unsafe_allow_html=True
)

# ======================== LOGIN ========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = "user"

if not st.session_state.logged_in:
    login()
    st.stop()

role = st.session_state.role
st.sidebar.markdown(f"👤 Login sebagai: **{role.upper()}**")
logout()

# ======================== LOAD DATA WILAYAH ========================
wil_df = load_wilayah_csv()

# ======================== SIDEBAR ========================
menu_list = ["Dashboard"]
if role == "fod":
    menu_list.extend(["Tambah Data", "Kelola Data", "Infografis Rob"])

menu = st.sidebar.radio("Menu", menu_list)

st.sidebar.markdown("---")
st.sidebar.subheader("Filter Dashboard")

start_date = st.sidebar.date_input("Tanggal Awal", value=None)
end_date = st.sidebar.date_input("Tanggal Akhir", value=None)

provinsi_filter = st.sidebar.selectbox(
    "Provinsi",
    [""] + get_provinsi(wil_df)
)

kabupaten_filter = st.sidebar.selectbox(
    "Kabupaten",
    [""] if not provinsi_filter else get_kabupaten(wil_df, provinsi_filter)
)

# ======================== HELPER ========================
def load_for_dashboard():
    return crud.fetch_filtered_data(
        start_date=to_db_date_str(start_date) if start_date else None,
        end_date=to_db_date_str(end_date) if end_date else None,
        provinsi=provinsi_filter or None,
        kabupaten=kabupaten_filter or None
    )

def display_waktu(val):
    return "-" if not val else str(val)

# ======================== DASHBOARD ========================
if menu == "Dashboard":

    st.subheader("📍 Peta Kejadian Banjir Rob")
    data = load_for_dashboard()

    if not data:
        st.info("Belum ada data.")
    else:
        create_map(data, provinsi_filter, kabupaten_filter)

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "📥 Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "data_banjir_rob.csv",
            "text/csv"
        )

        # ===== SOROTAN TERBARU =====
        st.subheader("📰 Sorotan Terbaru")
        latest = df.sort_values("Tanggal", ascending=False).head(3)

        for _, row in latest.iterrows():
            c1, c2 = st.columns([2, 1])

            with c1:
                st.markdown(
                    f"""
                    **{row['Lokasi']}**  
                    🏙 {row['Kabupaten']}, {row['Provinsi']}  
                    📅 {row['Tanggal']} ⏰ {display_waktu(row.get("Waktu"))}
                    """
                )

                pdf_buffer = generate_event_pdf(row.to_dict())
                st.download_button(
                    "📄 Download PDF",
                    pdf_buffer,
                    f"laporan_{row['Tanggal']}_{row['Lokasi']}.pdf",
                    "application/pdf",
                    key=f"pdf_latest_{row['No']}"
                )

            with c2:
                img_url = row.get("Gambar", "")
                if img_url:
                    try:
                        r = requests.get(img_url, timeout=8)
                        if r.status_code == 200:
                            st.image(img_url, use_container_width=True)
                    except Exception:
                        st.caption("⚠️ Gagal memuat gambar")

        # ===== PDF BERDASARKAN TANGGAL =====
        st.subheader("📅 Download Laporan Berdasarkan Tanggal")
        tanggal_pilih = st.date_input("Pilih Tanggal Kejadian")

        if tanggal_pilih:
            df["Tanggal_norm"] = pd.to_datetime(df["Tanggal"], errors="coerce").dt.date
            tgl = pd.to_datetime(tanggal_pilih).date()
            df_filtered = df[df["Tanggal_norm"] == tgl]

            if df_filtered.empty:
                st.warning("⚠️ Tidak ada data pada tanggal tersebut")
            else:
                lokasi_opsi = df_filtered["Lokasi"].unique().tolist()
                lokasi_pilih = st.selectbox("Pilih Lokasi", lokasi_opsi)

                rec = df_filtered[df_filtered["Lokasi"] == lokasi_pilih].iloc[0]

                st.download_button(
                    "📄 Download PDF (1 Kejadian)",
                    generate_event_pdf(rec.to_dict()),
                    f"laporan_{rec['Tanggal']}_{rec['Lokasi']}.pdf",
                    "application/pdf"
                )

                st.download_button(
                    "📄 Download PDF Semua Kejadian",
                    generate_multiple_events_pdf(
                        df_filtered.to_dict(orient="records"),
                        tgl
                    ),
                    f"laporan_semua_{tgl}.pdf",
                    "application/pdf"
                )

# ======================== TAMBAH DATA ========================
elif menu == "Tambah Data":

    if role != "fod":
        st.warning("⚠️ Menu ini hanya untuk FOD.")
        st.stop()

    st.subheader("➕ Tambah Data Banjir Rob")

    provinsi = st.selectbox("Provinsi", [""] + get_provinsi(wil_df))
    kabupaten = st.selectbox(
        "Kabupaten",
        [""] if not provinsi else get_kabupaten(wil_df, provinsi)
    )
    kecamatan = st.selectbox(
        "Kecamatan",
        [""] if not kabupaten else get_kecamatan(wil_df, provinsi, kabupaten)
    )

    with st.form("form_tambah"):
        tanggal = st.date_input("Tanggal Kejadian")
        waktu = st.text_input("Waktu Kejadian")
        lokasi = st.text_input("Lokasi")
        latitude = st.text_input("Latitude")
        longitude = st.text_input("Longitude")
        ketinggian = st.text_input("Ketinggian (cm)")
        dampak = st.text_area("Dampak Kejadian")
        sumber = st.text_input("Sumber Informasi")
        gambar = st.text_input("Link Gambar")

        if st.form_submit_button("💾 Simpan Data"):
            crud.insert_data(
                tanggal=to_db_date_str(tanggal),
                waktu=waktu.strip() if waktu else None,
                lokasi=lokasi,
                kecamatan=kecamatan,
                kabupaten=kabupaten,
                provinsi=provinsi,
                latitude=safe_float(latitude),
                longitude=safe_float(longitude),
                ketinggian=ketinggian,
                dampak=dampak,
                sumber=sumber,
                gambar=gambar
            )
            st.success("✅ Data berhasil ditambahkan")

# ======================== KELOLA DATA ========================
elif menu == "Kelola Data":

    if role != "fod":
        st.warning("⚠️ Menu ini hanya untuk FOD.")
        st.stop()

    st.subheader("🛠 Kelola Data Banjir Rob")

    data = crud.fetch_all_data()
    if not data:
        st.info("Belum ada data.")
        st.stop()

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    selected_id = st.selectbox("Pilih No Data", df["No"].tolist())
    rec = df[df["No"] == selected_id].iloc[0]

    st.markdown("### 📍 Wilayah Kejadian")

    prov_u = st.selectbox(
        "Provinsi",
        [""] + get_provinsi(wil_df),
        index=get_provinsi(wil_df).index(rec["Provinsi"]) + 1
        if rec["Provinsi"] in get_provinsi(wil_df) else 0
    )

    kab_u = st.selectbox(
        "Kabupaten",
        [""] if not prov_u else get_kabupaten(wil_df, prov_u),
        index=get_kabupaten(wil_df, prov_u).index(rec["Kabupaten"])
        if prov_u and rec["Kabupaten"] in get_kabupaten(wil_df, prov_u) else 0
    )

    kec_u = st.selectbox(
        "Kecamatan",
        [""] if not kab_u else get_kecamatan(wil_df, prov_u, kab_u),
        index=get_kecamatan(wil_df, prov_u, kab_u).index(rec["Kecamatan"])
        if kab_u and rec["Kecamatan"] in get_kecamatan(wil_df, prov_u, kab_u) else 0
    )

    with st.form("form_update"):
        tanggal_u = st.date_input("Tanggal Kejadian", parse_date_safe(rec["Tanggal"]))
        waktu_u = st.text_input("Waktu Kejadian", rec.get("Waktu", ""))
        lokasi_u = st.text_input("Lokasi", rec["Lokasi"])
        latitude_u = st.text_input("Latitude", rec["Latitude"])
        longitude_u = st.text_input("Longitude", rec["Longitude"])
        ketinggian_u = st.text_input("Ketinggian (cm)", rec.get("Ketinggian", ""))
        dampak_u = st.text_area("Dampak Kejadian", rec.get("Dampak", ""))
        sumber_u = st.text_input("Sumber Informasi", rec.get("Sumber", ""))
        gambar_u = st.text_input("Link Gambar", rec.get("Gambar", ""))

        if st.form_submit_button("💾 Simpan Perubahan"):
            crud.update_data(
                no_id=selected_id,
                tanggal=to_db_date_str(tanggal_u),
                waktu=waktu_u.strip() if waktu_u else None,
                lokasi=lokasi_u,
                kecamatan=kec_u,
                kabupaten=kab_u,
                provinsi=prov_u,
                latitude=safe_float(latitude_u),
                longitude=safe_float(longitude_u),
                ketinggian=ketinggian_u,
                dampak=dampak_u,
                sumber=sumber_u,
                gambar=gambar_u
            )
            st.success("✅ Data berhasil diperbarui")
            st.rerun()

    if st.button("🗑 Hapus Data Ini", type="primary"):
        crud.delete_data(selected_id)
        st.success("✅ Data berhasil dihapus")
        st.rerun()

# ======================== INFOGRAFIS ROB ========================
elif menu == "Infografis Rob":

    if role != "fod":
        st.error("⛔ Menu ini hanya untuk FOD")
        st.stop()

    st.subheader("🖼️ Infografis Sebaran Wilayah Terdampak Rob")

    col1, col2 = st.columns(2)
    with col1:
        tanggal_awal = st.date_input("Tanggal Awal Infografis")
    with col2:
        tanggal_akhir = st.date_input("Tanggal Akhir Infografis")

    mode_infografis = st.radio(
        "Jenis Infografis",
        ["Harian", "Rekap Bulanan"],
        horizontal=True
    )

    tanggal_rekap = st.text_input(
        "Teks Periode",
        value=datetime.now().strftime("%d %B %Y")
    )

    if st.button("📊 Proses & Generate Infografis"):

        data = crud.fetch_filtered_data(
            start_date=to_db_date_str(tanggal_awal),
            end_date=to_db_date_str(tanggal_akhir)
        )

        if not data:
            st.warning("⚠️ Tidak ada data")
            st.stop()

        df = pd.DataFrame(data)
        kecamatan_terdampak = (
            df["Kecamatan"].dropna().astype(str).unique().tolist()
        )

        hasil = generate_infografis_rob(
            kecamatan_list=kecamatan_terdampak,
            tanggal=tanggal_rekap,
            rekap_bul=(mode_infografis == "Rekap Bulanan")
        )

        if hasil["success"]:
            img = hasil["image"]
            st.image(img, use_container_width=True)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            st.download_button(
                "⬇️ Download Infografis",
                data=buf,
                file_name=hasil["file_name"],
                mime="image/png"
            )
        else:
            st.error(hasil["error"])
