from pathlib import Path
import io
import warnings

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib import font_manager

from PIL import Image, ImageDraw, ImageFont

# =========================
# OPTIONAL CARTOPY (SAFE)
# =========================
try:
    import cartopy.crs as ccrs
    CARTOPY_AVAILABLE = True
except Exception:
    CARTOPY_AVAILABLE = False

warnings.filterwarnings("ignore")

# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

BG_HARIAN = BASE_DIR / "assets/background/bg_img_updatehar.png"
BG_BULANAN = BASE_DIR / "assets/background/bg_img_rekapbul.png"

GDB_KECAMATAN = BASE_DIR / "data/spatial/batas_kecamatan.gdb"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_map_annotations(ax, gdf):
    """Titik lokasi + label merah + leader line (BMKG style)"""

    offsets = [
        (1.6, 0.9),
        (-1.6, 0.9),
        (1.6, -0.9),
        (-1.6, -0.9),
    ]

    for i, (_, row) in enumerate(gdf.iterrows()):
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        centroid = geom.centroid
        x, y = centroid.x, centroid.y

        dx, dy = offsets[i % len(offsets)]
        lx, ly = x + dx, y + dy

        ax.scatter(
            x, y,
            s=70,
            color="#C62828",
            edgecolor="white",
            linewidth=1.2,
            zorder=6
        )

        arrow = FancyArrowPatch(
            (x, y),
            (lx - 0.12, ly - 0.12),
            arrowstyle="-",
            connectionstyle="arc3,rad=0.15",
            linewidth=1.6,
            color="#C62828",
            zorder=5
        )
        ax.add_patch(arrow)

        ax.text(
            lx,
            ly,
            str(row.get("NAMOBJ", "")),
            fontsize=12,
            fontweight="bold",
            color="white",
            ha="center",
            va="center",
            bbox=dict(
                facecolor="#B71C1C",
                edgecolor="none",
                boxstyle="round,pad=0.35"
            ),
            zorder=7
        )


def create_legend_panel(areas, width, height, font_path):
    """Panel legenda samping"""

    panel = Image.new("RGBA", (width, height), (0, 40, 112, 255))
    draw = ImageDraw.Draw(panel)

    title_font = ImageFont.truetype(font_path, 50)
    item_font = ImageFont.truetype(font_path, 42)

    draw.text((40, 60), "Wilayah Terdampak Rob:", fill="white", font=title_font)

    draw.line(
        [(40, 130), (width - 40, 130)],
        fill="white",
        width=4
    )

    y = 160
    for area in areas:
        draw.text((60, y), f"Pesisir Kec. {area}", fill="white", font=item_font)
        y += 55

    return panel

# ============================================================
# MAIN FUNCTION
# ============================================================

def plot_rob_affected_areas(
    affected_areas,
    save_path=None,
    tanggal_rekap=None,
    rekap_bul=False,
):
    """
    Generate infografis rob.
    Return: PIL.Image
    """

    if not affected_areas:
        raise ValueError("affected_areas kosong")

    # ========================================================
    # LOAD SPATIAL DATA
    # ========================================================
    try:
        gdf = gpd.read_file(GDB_KECAMATAN)
    except Exception as e:
        raise RuntimeError(f"Gagal membaca data spasial: {e}")

    wilayah = gdf[gdf["NAMOBJ"].isin(affected_areas)]

    if wilayah.empty:
        raise ValueError("Tidak ada wilayah yang cocok dengan affected_areas")

    # ========================================================
    # LOAD BACKGROUND IMAGE
    # ========================================================
    bg_path = BG_BULANAN if rekap_bul else BG_HARIAN

    if not bg_path.exists():
        raise RuntimeError(f"Background tidak ditemukan: {bg_path}")

    bg_img = Image.open(bg_path).convert("RGBA")
    bg_w, bg_h = bg_img.size

    # ========================================================
    # CREATE MAP FIGURE
    # ========================================================
    fig = plt.figure(figsize=(18, 12), facecolor="none")

    if CARTOPY_AVAILABLE:
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent([94, 142, -12, 8], crs=ccrs.PlateCarree())
    else:
        ax = plt.axes()

    ax.set_facecolor("none")

    gdf.plot(
        ax=ax,
        facecolor="#E5E5E5",
        edgecolor="white",
        linewidth=0.5,
        zorder=1
    )

    wilayah.plot(
        ax=ax,
        facecolor="#FFB703",
        edgecolor="red",
        linewidth=2,
        linestyle="--",
        alpha=0.85,
        zorder=3
    )

    create_map_annotations(ax, wilayah)
    ax.axis("off")

    # ========================================================
    # EXPORT MAP TO BUFFER (ANTI MEMORY LEAK)
    # ========================================================
    buf = io.BytesIO()

    plt.savefig(
        buf,
        format="png",
        dpi=150,
        bbox_inches="tight",
        transparent=True
    )

    plt.close(fig)  # ⛔ WAJIB
    buf.seek(0)

    map_img = Image.open(buf).convert("RGBA")

    # ========================================================
    # RESIZE MAP
    # ========================================================
    scale = bg_w / map_img.size[0]
    new_size = (
        int(map_img.size[0] * scale),
        int(map_img.size[1] * scale)
    )

    map_img = map_img.resize(new_size, Image.Resampling.LANCZOS)

    # ========================================================
    # COMPOSE FINAL IMAGE
    # ========================================================
    canvas = bg_img.copy()
    canvas.paste(
        map_img,
        ((bg_w - new_size[0]) // 2, 360),
        map_img
    )

    font_path = font_manager.findfont(
        font_manager.FontProperties(family="DejaVu Sans")
    )

    legend = create_legend_panel(
        affected_areas,
        width=1050,
        height=bg_h,
        font_path=font_path
    )

    final_img = Image.new("RGBA", (bg_w + 1050, bg_h))
    final_img.paste(canvas, (0, 0))
    final_img.paste(legend, (bg_w, 0))

    draw = ImageDraw.Draw(final_img)
    for y in range(0, bg_h, 28):
        draw.line(
            [(bg_w, y), (bg_w, y + 14)],
            fill="white",
            width=4
        )

    if tanggal_rekap:
        font = ImageFont.truetype(font_path, 72)
        draw.text(
            (bg_w - 720, 350),
            tanggal_rekap,
            fill="white",
            font=font
        )

    # ========================================================
    # SAVE FILE (OPTIONAL)
    # ========================================================
    if save_path:
        try:
            final_img.save(save_path, dpi=(300, 300))
        except Exception:
            # ⚠️ jangan crash jika disk read-only
            pass

    return final_img
