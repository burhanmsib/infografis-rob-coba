# modules/crud.py
import streamlit as st
import mysql.connector
from mysql.connector import Error

TABLE_NAME = "rob"

# =====================================================
# KONEKSI DATABASE
# =====================================================
def get_db_connection():
    """Buat koneksi ke database menggunakan kredensial dari secrets.toml"""
    try:
        conn = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            port=st.secrets["mysql"].get("port", 3306),
            connection_timeout=10
        )
        return conn
    except Error as e:
        st.error(f"❌ Gagal terhubung ke database: {e}")
        return None


# =====================================================
# READ
# =====================================================
def fetch_all_data():
    """Ambil seluruh data dari tabel"""
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT
            `No`,
            `Tanggal`,
            `Waktu`,
            `Lokasi`,
            `Kecamatan`,
            `Kabupaten`,
            `Provinsi`,
            `Latitude`,
            `Longitude`,
            `Ketinggian`,
            `Dampak`,
            `Gambar`,
            `Sumber`
        FROM `{TABLE_NAME}`
        ORDER BY `Tanggal` DESC, `Waktu` DESC, `No` DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fetch_filtered_data(
    start_date=None,
    end_date=None,
    provinsi=None,
    kabupaten=None,
    kecamatan=None
):
    """Ambil data berdasarkan filter opsional"""
    conn = get_db_connection()
    if not conn:
        return []

    cur = conn.cursor(dictionary=True)

    q = f"""
        SELECT
            `No`,
            `Tanggal`,
            `Waktu`,
            `Lokasi`,
            `Kecamatan`,
            `Kabupaten`,
            `Provinsi`,
            `Latitude`,
            `Longitude`,
            `Ketinggian`,
            `Dampak`,
            `Gambar`,
            `Sumber`
        FROM `{TABLE_NAME}`
        WHERE 1=1
    """
    params = []

    if start_date:
        q += " AND `Tanggal` >= %s"
        params.append(start_date)

    if end_date:
        q += " AND `Tanggal` <= %s"
        params.append(end_date)

    if provinsi:
        q += " AND `Provinsi` LIKE %s"
        params.append(f"%{provinsi}%")

    if kabupaten:
        q += " AND `Kabupaten` LIKE %s"
        params.append(f"%{kabupaten}%")

    if kecamatan:
        q += " AND `Kecamatan` LIKE %s"
        params.append(f"%{kecamatan}%")

    q += " ORDER BY `Tanggal` DESC, `Waktu` DESC, `No` DESC"

    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# =====================================================
# CREATE
# =====================================================
def insert_data(
    tanggal,
    waktu,
    lokasi,
    kecamatan,
    kabupaten,
    provinsi,
    latitude,
    longitude,
    ketinggian,
    dampak,
    gambar,
    sumber
):
    """Tambahkan satu data baru ke tabel"""
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    sql = f"""
        INSERT INTO `{TABLE_NAME}` (
            `Tanggal`,
            `Waktu`,
            `Lokasi`,
            `Kecamatan`,
            `Kabupaten`,
            `Provinsi`,
            `Latitude`,
            `Longitude`,
            `Ketinggian`,
            `Dampak`,
            `Gambar`,
            `Sumber`
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cur.execute(sql, (
        tanggal,
        waktu,
        lokasi,
        kecamatan,
        kabupaten,
        provinsi,
        latitude,
        longitude,
        ketinggian,
        dampak,
        gambar,
        sumber
    ))

    conn.commit()
    cur.close()
    conn.close()


# =====================================================
# UPDATE
# =====================================================
def update_data(
    no_id,
    tanggal,
    waktu,
    lokasi,
    kecamatan,
    kabupaten,
    provinsi,
    latitude,
    longitude,
    ketinggian,
    dampak,
    gambar,
    sumber
):
    """Perbarui data berdasarkan ID"""
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    sql = f"""
        UPDATE `{TABLE_NAME}` SET
            `Tanggal`=%s,
            `Waktu`=%s,
            `Lokasi`=%s,
            `Kecamatan`=%s,
            `Kabupaten`=%s,
            `Provinsi`=%s,
            `Latitude`=%s,
            `Longitude`=%s,
            `Ketinggian`=%s,
            `Dampak`=%s,
            `Gambar`=%s,
            `Sumber`=%s
        WHERE `No`=%s
    """

    cur.execute(sql, (
        tanggal,
        waktu,
        lokasi,
        kecamatan,
        kabupaten,
        provinsi,
        latitude,
        longitude,
        ketinggian,
        dampak,
        gambar,
        sumber,
        no_id
    ))

    conn.commit()
    cur.close()
    conn.close()


# =====================================================
# DELETE
# =====================================================
def delete_data(no_id):
    """Hapus data berdasarkan ID"""
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()
    cur.execute(f"DELETE FROM `{TABLE_NAME}` WHERE `No`=%s", (no_id,))
    conn.commit()
    cur.close()
    conn.close()