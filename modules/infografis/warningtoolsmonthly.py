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

# Cartopy hanya di-load jika BUKAN Streamlit Cloud
if not IS_STREAMLIT_CLOUD:
    import cartopy.crs as ccrs
else:
    ccrs = None

# ============================================================
# PATH CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

GDB_KECAMATAN = BASE_DIR / "data" / "spatial" / "batas_kecamatan.gdb"
BG_BULANAN = BASE_DIR / "assets" / "background" / "bg_img_rekapbul.png"

# ============================================================
# LEGEND PANEL
# ============================================================

def create_legend_panel(wilayah_list, width, height, font_path):
    panel = Image.new("RGBA", (width, height), (0, 40, 112, 255))
    draw = ImageDraw.Draw(panel)

    title_font = ImageFont.truetype(font_path, 48)
    item_font = ImageFont.truetype(font_path, 38)

    # Garis putus-putus
    x = 0
    while x < width:
        draw.line([(x, 5), (x + 20, 5)], fill="white", width=3)
        x += 35

    draw.text(
        (40, 50),
        "Wilayah Terdampak Rob (Warna Merah):",
        fill="white",
        font=title_font
    )

    draw.line([(40, 115), (width - 40, 115)], fill="white", width=2)

    n = len(wilayah_list)
    num_cols = 4 if n > 60 else 3 if n > 30 else 2
    col_width = (width - 80) // num_cols
    row_height = 44

    for i, wilayah in enumerate(wilayah_list):
        col = i % num_cols
        row = i // num_cols
        draw.text(
            (40 + col * col_width, 150 + row * row_height),
            f"Kec. {wilayah}",
            fill="white",
            font=item_font
        )

    return panel

# ============================================================
# MAIN FUNCTION – WAJIB AMAN STREAMLIT
# ============================================================

def plot_rob_affected_areas(
    affected_areas=None,
    tanggal_rekap=None,
    save_path=None,
    **_
):
    """
    WAJIB:
    - Tidak crash Streamlit Cloud
    - Return PIL.Image atau None
    """

    # ========================================================
    # STREAMLIT CLOUD MODE (AMAN, TIDAK CRASH)
    # ========================================================
    if IS_STREAMLIT_CLOUD:
        # Return gambar dummy kecil (biar UI & health check aman)
        img = Image.new("RGBA", (800, 400), (240, 240, 240, 255))
        draw = ImageDraw.Draw(img)

        font_path = font_manager.findfont(
            font_manager.FontProperties(family="DejaVu Sans")
        )
        font = ImageFont.truetype(font_path, 24)

        draw.text(
            (40, 180),
            "Infografis rekap bulanan hanya tersedia\n"
            "di server internal (membutuhkan Cartopy).",
            fill="black",
            font=font
        )
        return img

    # ========================================================
    # SERVER INTERNAL MODE (FULL FEATURE)
    # ========================================================
    if not affected_areas:
        raise ValueError("affected_areas kosong")

    batas = gpd.read_file(GDB_KECAMATAN)
    wilayah = batas[batas["NAMOBJ"].isin(affected_areas)]

    ordered_names = [
        row["NAMOBJ"]
        for _, row in batas.iterrows()
        if row["NAMOBJ"] in affected_areas
    ]

    bg_img = Image.open(BG_BULANAN).convert("RGBA")
    bg_w, bg_h = bg_img.size

    fig = plt.figure(figsize=(24, 12), facecolor="none")
    ax = plt.axes(projection=ccrs.PlateCarree())

    batas.plot(ax=ax, facecolor="#E6E6E6", edgecolor="white", linewidth=0.4)
    wilayah.plot(ax=ax, facecolor="red", edgecolor="darkred", linewidth=0.8)

    ax.set_extent([94, 142, -12, 8], crs=ccrs.PlateCarree())
    ax.axis("off")

    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)

    map_img = Image.open(buf).convert("RGBA")

    target_width = int(bg_w * 0.92)
    scale = target_width / map_img.width
    map_img = map_img.resize(
        (int(map_img.width * scale), int(map_img.height * scale)),
        Image.Resampling.LANCZOS
    )

    overlay = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    overlay.paste(map_img, ((bg_w - map_img.width) // 2, 280), map_img)
    map_with_bg = Image.alpha_composite(bg_img, overlay)

    font_path = font_manager.findfont(
        font_manager.FontProperties(family="DejaVu Sans")
    )

    if tanggal_rekap:
        draw = ImageDraw.Draw(map_with_bg)
        font = ImageFont.truetype(font_path, 72)
        draw.text((bg_w - 900, 300), tanggal_rekap, fill="white", font=font)

    legend_panel = create_legend_panel(ordered_names, bg_w, 1400, font_path)

    final_img = Image.new(
        "RGBA", (bg_w, bg_h + 1400), (0, 0, 0, 0)
    )
    final_img.paste(map_with_bg, (0, 0))
    final_img.paste(legend_panel, (0, bg_h))

    if save_path:
        final_img.save(save_path, dpi=(300, 300))

    return final_img
