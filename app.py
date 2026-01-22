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


# ======================== KONFIGURASI ========================
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

# ======================== DATA WILAYAH ========================
wil_df = load_wilayah_csv()

# ======================== SIDEBAR ========================
menu_list = ["Dashboard"]
if role == "fod":
    menu_list += ["Tambah Data", "Kelola Data", "Infografis Rob"]

menu = st.sidebar.radio("Menu", menu_list, key="menu_main")

st.sidebar.markdown("---")
st.sidebar.subheader("Filter Dashboard")

start_date = st.sidebar.date_input("Tanggal Awal", None, key="sb_start")
end_date = st.sidebar.date_input("Tanggal Akhir", None, key="sb_end")

prov_filter = st.sidebar.selectbox(
    "Provinsi",
    [""] + get_provinsi(wil_df),
    key="sb_prov"
)

kab_filter = st.sidebar.selectbox(
    "Kabupaten",
    [""] if not prov_filter else get_kabupaten(wil_df, prov_filter),
    key="sb_kab"
)

# ======================== HELPER ========================
def load_dashboard_data():
    return crud.fetch_filtered_data(
        start_date=to_db_date_str(start_date) if start_date else None,
        end_date=to_db_date_str(end_date) if end_date else None,
        provinsi=prov_filter or None,
        kabupaten=kab_filter or None
    )

def fmt_waktu(val):
    return "-" if not val else str(val)

# ======================== NOTIFIKASI ========================
if "notif" in st.session_state:
    if st.session_state["notif"] == "tambah":
        st.success("✅ Data berhasil ditambahkan")
    elif st.session_state["notif"] == "update":
        st.success("✅ Data berhasil diperbarui")
    elif st.session_state["notif"] == "hapus":
        st.success("🗑️ Data berhasil dihapus")
    del st.session_state["notif"]

# ======================================================
# ======================== DASHBOARD ===================
# ======================================================
if menu == "Dashboard":

    st.subheader("📍 Peta Kejadian Banjir Rob")

    data = load_dashboard_data()
    if not data:
        st.info("Belum ada data.")
    else:
        create_map(data, prov_filter, kab_filter)

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "📥 Download CSV",
            df.to_csv(index=False).encode(),
            "data_banjir_rob.csv",
            "text/csv",
            key="csv_dash"
        )

        # ===== SOROTAN TERBARU =====
        st.subheader("📰 Sorotan Terbaru")
        for _, row in df.sort_values("Tanggal", ascending=False).head(3).iterrows():
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(
                    f"""
                    **{row['Lokasi']}**  
                    🏙 {row['Kabupaten']}, {row['Provinsi']}  
                    📅 {row['Tanggal']} ⏰ {fmt_waktu(row.get("Waktu"))}
                    """
                )

                st.download_button(
                    "📄 Download PDF",
                    generate_event_pdf(row.to_dict()),
                    f"laporan_{row['No']}.pdf",
                    "application/pdf",
                    key=f"pdf_dash_{row['No']}"
                )

            with c2:
                if row.get("Gambar"):
                    try:
                        r = requests.get(row["Gambar"], timeout=6)
                        if r.status_code == 200:
                            st.image(row["Gambar"])
                    except:
                        st.caption("⚠️ Gagal memuat gambar")

        # ===== PDF PER KEJADIAN =====
        st.subheader("📄 Download Laporan PDF Per Kejadian")

        tanggal_pilih = st.date_input(
            "Pilih Tanggal Kejadian",
            key="dash_tanggal_pdf"
        )

        if tanggal_pilih:
            df["Tanggal_norm"] = pd.to_datetime(
                df["Tanggal"], errors="coerce"
            ).dt.date

            tgl = pd.to_datetime(tanggal_pilih).date()
            df_tgl = df[df["Tanggal_norm"] == tgl]

            if df_tgl.empty:
                st.warning("⚠️ Tidak ada kejadian pada tanggal tersebut")
            else:
                lokasi_pilih = st.selectbox(
                    "Pilih Lokasi Kejadian",
                    df_tgl["Lokasi"].unique().tolist(),
                    key="dash_lokasi_pdf"
                )

                rec = df_tgl[df_tgl["Lokasi"] == lokasi_pilih].iloc[0]

                st.download_button(
                    "📄 Download PDF Kejadian",
                    generate_event_pdf(rec.to_dict()),
                    f"laporan_{rec['Tanggal']}_{rec['Lokasi']}.pdf",
                    "application/pdf",
                    key="dash_pdf_single"
                )

                st.download_button(
                    "📄 Download PDF Semua Kejadian (Tanggal Ini)",
                    generate_multiple_events_pdf(
                        df_tgl.to_dict(orient="records"),
                        tgl
                    ),
                    f"laporan_semua_{tgl}.pdf",
                    "application/pdf",
                    key="dash_pdf_all"
                )

# ======================================================
# ======================== TAMBAH DATA =================
# ======================================================
elif menu == "Tambah Data":

    st.subheader("➕ Tambah Data Banjir Rob")

    prov = st.selectbox("Provinsi", [""] + get_provinsi(wil_df), key="add_prov")
    kab = st.selectbox(
        "Kabupaten",
        [""] if not prov else get_kabupaten(wil_df, prov),
        key="add_kab"
    )
    kec = st.selectbox(
        "Kecamatan",
        [""] if not kab else get_kecamatan(wil_df, prov, kab),
        key="add_kec"
    )

    with st.form("form_add"):
        tgl = st.date_input("Tanggal Kejadian")
        waktu = st.text_input("Waktu Kejadian")
        lokasi = st.text_input("Lokasi")
        lat = st.text_input("Latitude")
        lon = st.text_input("Longitude")
        tinggi = st.text_input("Ketinggian (cm)")
        dampak = st.text_area("Dampak")
        sumber = st.text_input("Sumber")
        gambar = st.text_input("Link Gambar")

        if st.form_submit_button("💾 Simpan"):
            crud.insert_data(
                tanggal=to_db_date_str(tgl),
                waktu=waktu,
                lokasi=lokasi,
                kecamatan=kec,
                kabupaten=kab,
                provinsi=prov,
                latitude=safe_float(lat),
                longitude=safe_float(lon),
                ketinggian=tinggi,
                dampak=dampak,
                sumber=sumber,
                gambar=gambar
            )
            st.session_state["notif"] = "tambah"
            st.rerun()

# ======================================================
# ======================== KELOLA DATA =================
# ======================================================
elif menu == "Kelola Data":

    st.subheader("🛠 Kelola Data Banjir Rob")

    data = crud.fetch_all_data()
    if not data:
        st.info("Belum ada data.")
        st.stop()

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    no = st.selectbox("Pilih No Data", df["No"], key="edit_no")
    rec = df[df["No"] == no].iloc[0]

    # ================== PROVINSI (AMAN) ==================
    prov_list = [""] + get_provinsi(wil_df)

    prov_index = (
        prov_list.index(rec["Provinsi"])
        if rec.get("Provinsi") in prov_list
        else 0
    )

    prov_u = st.selectbox(
        "Provinsi",
        prov_list,
        index=prov_index,
        key="edit_prov"
    )

    if rec.get("Provinsi") not in prov_list and rec.get("Provinsi"):
        st.warning("⚠️ Provinsi pada data lama tidak ditemukan di master wilayah")

    # ================== KABUPATEN (AMAN) ==================
    kab_list = (
        [""] if not prov_u else get_kabupaten(wil_df, prov_u)
    )

    kab_index = (
        kab_list.index(rec["Kabupaten"])
        if rec.get("Kabupaten") in kab_list
        else 0
    )

    kab_u = st.selectbox(
        "Kabupaten",
        kab_list,
        index=kab_index,
        key="edit_kab"
    )

    if prov_u and rec.get("Kabupaten") not in kab_list and rec.get("Kabupaten"):
        st.warning("⚠️ Kabupaten pada data lama tidak ditemukan")

    # ================== KECAMATAN (AMAN) ==================
    kec_list = (
        [""] if not kab_u else get_kecamatan(wil_df, prov_u, kab_u)
    )

    kec_index = (
        kec_list.index(rec["Kecamatan"])
        if rec.get("Kecamatan") in kec_list
        else 0
    )

    kec_u = st.selectbox(
        "Kecamatan",
        kec_list,
        index=kec_index,
        key="edit_kec"
    )

    if kab_u and rec.get("Kecamatan") not in kec_list and rec.get("Kecamatan"):
        st.warning("⚠️ Kecamatan pada data lama tidak ditemukan")

    # ================== FORM EDIT ==================
    with st.form("form_edit"):
        tgl_u = st.date_input("Tanggal", parse_date_safe(rec["Tanggal"]))
        waktu_u = st.text_input("Waktu", rec.get("Waktu", ""))
        lokasi_u = st.text_input("Lokasi", rec["Lokasi"])
        lat_u = st.text_input("Latitude", rec["Latitude"])
        lon_u = st.text_input("Longitude", rec["Longitude"])
        tinggi_u = st.text_input("Ketinggian", rec.get("Ketinggian", ""))
        dampak_u = st.text_area("Dampak", rec.get("Dampak", ""))
        sumber_u = st.text_input("Sumber", rec.get("Sumber", ""))
        gambar_u = st.text_input("Gambar", rec.get("Gambar", ""))

        if st.form_submit_button("💾 Simpan Perubahan"):
            crud.update_data(
                no_id=no,
                tanggal=to_db_date_str(tgl_u),
                waktu=waktu_u,
                lokasi=lokasi_u,
                kecamatan=kec_u,
                kabupaten=kab_u,
                provinsi=prov_u,
                latitude=safe_float(lat_u),
                longitude=safe_float(lon_u),
                ketinggian=tinggi_u,
                dampak=dampak_u,
                sumber=sumber_u,
                gambar=gambar_u
            )
            st.session_state["notif"] = "update"
            st.rerun()

    if st.button("🗑 Hapus Data"):
        crud.delete_data(no)
        st.session_state["notif"] = "hapus"
        st.rerun()


# ======================================================
# ======================== INFOGRAFIS ==================
# ======================================================
elif menu == "Infografis Rob":

    st.subheader("🖼️ Infografis Sebaran Wilayah Terdampak Rob")

    tgl_awal = st.date_input("Tanggal Awal")
    tgl_akhir = st.date_input("Tanggal Akhir")

    mode = st.radio(
        "Jenis",
        ["Harian", "Rekap Bulanan"],
        horizontal=True
    )

    teks = st.text_input(
        "Teks Periode",
        datetime.now().strftime("%d %B %Y")
    )

    if st.button("📊 Generate"):

        data = crud.fetch_filtered_data(
            start_date=to_db_date_str(tgl_awal),
            end_date=to_db_date_str(tgl_akhir)
        )

        df = pd.DataFrame(data)
        kec = df["Kecamatan"].dropna().unique().tolist()

        hasil = generate_infografis_rob(
            kecamatan_list=kec,
            tanggal=teks,
            rekap_bul=(mode == "Rekap Bulanan")
        )

        if hasil["success"]:
            img = hasil["image"]
            st.image(img)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            st.download_button(
                "⬇️ Download Infografis",
                buf,
                hasil["file_name"],
                "image/png"
            )
        else:
            st.error(hasil["error"])
