# ============================================================
# WARNING TOOLS – REKAP BULANAN (FINAL / STREAMLIT SAFE)
# ============================================================

from pathlib import Path
import os
import geopandas as gpd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager
import io
import warnings

warnings.filterwarnings("ignore")

# ============================================================
# ENV DETECTION
# ============================================================

IS_STREAMLIT_CLOUD = os.getenv("STREAMLIT_CLOUD") == "1"

# Cartopy hanya boleh di-load jika BUKAN Streamlit Cloud
if not IS_STREAMLIT_CLOUD:
    import cartopy.crs as ccrs
else:
    ccrs = None

# ============================================================
# PATH CONFIG (SESUAI STRUKTUR WEB)
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# ⚠️ Pastikan file ini BENAR-BENAR ADA di repo
GDB_KECAMATAN = BASE_DIR / "data" / "spatial" / "batskec_new.gdb"
BG_BULANAN = BASE_DIR / "assets" / "background" / "bg_img_rekapbul.png"

# ============================================================
# LEGEND PANEL (DI BAWAH PETA)
# ============================================================

def create_legend_panel(wilayah_list, width, height, font_path):
    panel = Image.new("RGBA", (width, height), (0, 40, 112, 255))
    draw = ImageDraw.Draw(panel)

    title_font = ImageFont.truetype(font_path, 50)
    item_font = ImageFont.truetype(font_path, 42)

    # Judul
    draw.text(
        (40, 40),
        "Wilayah Terdampak Rob (Warna Merah):",
        fill="white",
        font=title_font
    )

    draw.line(
        [(40, 115), (width - 40, 115)],
        fill="white",
        width=3
    )

    # Layout kolom (mirip senior)
    n = len(wilayah_list)
    num_cols = 4 if n > 45 else 3 if n > 25 else 2
    col_width = (width - 80) // num_cols
    row_height = 52

    for i, wilayah in enumerate(wilayah_list):
        col = i % num_cols
        row = i // num_cols
        x = 40 + col * col_width
        y = 150 + row * row_height

        draw.text(
            (x, y),
            f"Kec. {wilayah}",
            fill="white",
            font=item_font
        )

    return panel

# ============================================================
# MAIN FUNCTION – REKAP BULANAN
# ============================================================

def plot_rob_affected_areas(
    affected_areas_list,
    tanggal_rekap=None,
    save_path=None,
    rekap_bul=True
):
    """
    OUTPUT: PIL.Image (SIAP st.image)
    """

    if not affected_areas_list:
        raise ValueError("affected_areas_list kosong")

    # ========================================================
    # PROTEKSI STREAMLIT CLOUD
    # ========================================================
    if IS_STREAMLIT_CLOUD:
        raise RuntimeError(
            "Infografis rekap bulanan membutuhkan Cartopy "
            "dan hanya dapat dijalankan di server internal."
        )

    if not affected_areas_list:
        raise ValueError("affected_areas_list tidak boleh kosong")

    if not GDB_KECAMATAN.exists():
        raise FileNotFoundError(f"GDB tidak ditemukan: {GDB_KECAMATAN}")

    if not BG_BULANAN.exists():
        raise FileNotFoundError(f"Background tidak ditemukan: {BG_BULANAN}")

    # ========================================================
    # LOAD DATA SPASIAL
    # ========================================================
    batas = gpd.read_file(GDB_KECAMATAN)

    wilayah = batas[batas["NAMOBJ"].isin(affected_areas_list)]
    if wilayah.empty:
        raise ValueError("Nama kecamatan tidak ditemukan di geodatabase")

    # Urutan legend mengikuti geodatabase (PENTING)
    ordered_names = []
    for _, row in batas.iterrows():
        if row["NAMOBJ"] in affected_areas_list and row["NAMOBJ"] not in ordered_names:
            ordered_names.append(row["NAMOBJ"])

    # ========================================================
    # LOAD BACKGROUND
    # ========================================================
    bg_img = Image.open(BG_BULANAN).convert("RGBA")
    bg_w, bg_h = bg_img.size

    # ========================================================
    # DRAW MAP (UKURAN DIPERBESAR – FIX)
    # ========================================================
    fig = plt.figure(figsize=(22, 12), facecolor="none")
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_facecolor("none")

    batas.plot(
        ax=ax,
        facecolor="#E6E6E6",
        edgecolor="white",
        linewidth=0.4,
        zorder=1
    )

    wilayah.plot(
        ax=ax,
        facecolor="red",
        edgecolor="darkred",
        linewidth=0.8,
        alpha=0.95,
        zorder=3
    )

    bounds = batas.total_bounds
    ax.set_extent([bounds[0], 143, bounds[1], 17], crs=ccrs.PlateCarree())
    ax.axis("off")

    # ========================================================
    # EXPORT MAP → IMAGE
    # ========================================================
    buf = io.BytesIO()
    plt.savefig(buf, dpi=180, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)

    map_img = Image.open(buf).convert("RGBA")

    # 🔥 MAP DIBESARKAN (INI KUNCI TERAKHIR)
    scale = (bg_w * 0.95) / map_img.width
    new_size = (int(map_img.width * scale), int(map_img.height * scale))
    map_img = map_img.resize(new_size, Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    overlay.paste(
        map_img,
        ((bg_w - new_size[0]) // 2, 240),
        map_img
    )

    map_with_bg = Image.alpha_composite(bg_img, overlay)

    # ========================================================
    # TANGGAL REKAP
    # ========================================================
    font_path = font_manager.findfont(
        font_manager.FontProperties(family="DejaVu Sans")
    )

    if tanggal_rekap:
        draw = ImageDraw.Draw(map_with_bg)
        font = ImageFont.truetype(font_path, 72)
        draw.text(
            (bg_w - 900, 260),
            tanggal_rekap,
            fill="white",
            font=font
        )

    # ========================================================
    # LEGEND PANEL (BAWAH)
    # ========================================================
    legend_height = 1500
    legend_panel = create_legend_panel(
        ordered_names,
        bg_w,
        legend_height,
        font_path
    )

    final_img = Image.new(
        "RGBA",
        (bg_w, bg_h + legend_height),
        (0, 0, 0, 0)
    )

    final_img.paste(map_with_bg, (0, 0))
    final_img.paste(legend_panel, (0, bg_h))

    # ========================================================
    # SAVE OPTIONAL
    # ========================================================
    if save_path:
        final_img.save(save_path, dpi=(300, 300))

    return final_img

