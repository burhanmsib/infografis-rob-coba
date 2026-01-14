import pandas as pd
import streamlit as st

@st.cache_data
def load_wilayah_csv():
    return pd.read_csv("data/referensi/wil_kecamatan.csv")

def get_provinsi(df):
    return sorted(df["Provinsi"].dropna().unique())

def get_kabupaten(df, provinsi):
    return sorted(df[df["Provinsi"] == provinsi]["Kabupaten"].dropna().unique())

def get_kecamatan(df, provinsi, kabupaten):
    return sorted(
        df[
            (df["Provinsi"] == provinsi) &
            (df["Kabupaten"] == kabupaten)
        ]["Kecamatan"].dropna().unique()
    )