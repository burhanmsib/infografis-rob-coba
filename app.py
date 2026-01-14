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
                        pass

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
        tgl = st.date_input("Tanggal Kejadian", key="add_tgl")
        waktu = st.text_input("Waktu Kejadian", key="add_wkt")
        lokasi = st.text_input("Lokasi", key="add_lok")
        lat = st.text_input("Latitude", key="add_lat")
        lon = st.text_input("Longitude", key="add_lon")
        tinggi = st.text_input("Ketinggian (cm)", key="add_tinggi")
        dampak = st.text_area("Dampak", key="add_dampak")
        sumber = st.text_input("Sumber", key="add_sumber")
        gambar = st.text_input("Link Gambar", key="add_gambar")

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
            st.success("✅ Data berhasil ditambahkan")

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

    prov_u = st.selectbox(
        "Provinsi",
        [""] + get_provinsi(wil_df),
        index=get_provinsi(wil_df).index(rec["Provinsi"]) + 1,
        key="edit_prov"
    )

    kab_u = st.selectbox(
        "Kabupaten",
        get_kabupaten(wil_df, prov_u),
        index=get_kabupaten(wil_df, prov_u).index(rec["Kabupaten"]),
        key="edit_kab"
    )

    kec_u = st.selectbox(
        "Kecamatan",
        get_kecamatan(wil_df, prov_u, kab_u),
        index=get_kecamatan(wil_df, prov_u, kab_u).index(rec["Kecamatan"]),
        key="edit_kec"
    )

    with st.form("form_edit"):
        tgl_u = st.date_input("Tanggal", parse_date_safe(rec["Tanggal"]), key="edit_tgl")
        waktu_u = st.text_input("Waktu", rec.get("Waktu", ""), key="edit_wkt")
        lokasi_u = st.text_input("Lokasi", rec["Lokasi"], key="edit_lok")
        lat_u = st.text_input("Latitude", rec["Latitude"], key="edit_lat")
        lon_u = st.text_input("Longitude", rec["Longitude"], key="edit_lon")
        tinggi_u = st.text_input("Ketinggian", rec.get("Ketinggian", ""), key="edit_tinggi")
        dampak_u = st.text_area("Dampak", rec.get("Dampak", ""), key="edit_dampak")
        sumber_u = st.text_input("Sumber", rec.get("Sumber", ""), key="edit_sumber")
        gambar_u = st.text_input("Gambar", rec.get("Gambar", ""), key="edit_gambar")

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
            st.success("✅ Data diperbarui")
            st.rerun()

    if st.button("🗑 Hapus Data", key="hapus_data"):
        crud.delete_data(no)
        st.success("🗑 Data dihapus")
        st.rerun()

# ======================================================
# ======================== INFOGRAFIS ==================
# ======================================================
elif menu == "Infografis Rob":

    st.subheader("🖼️ Infografis Sebaran Wilayah Terdampak Rob")

    tgl_awal = st.date_input("Tanggal Awal", key="info_awal")
    tgl_akhir = st.date_input("Tanggal Akhir", key="info_akhir")

    mode = st.radio(
        "Jenis",
        ["Harian", "Rekap Bulanan"],
        horizontal=True,
        key="info_mode"
    )

    teks = st.text_input(
        "Teks Periode",
        datetime.now().strftime("%d %B %Y"),
        key="info_teks"
    )

    if st.button("📊 Generate", key="info_gen"):

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
                "image/png",
                key="info_dl"
            )
        else:
            st.error(hasil["error"])
