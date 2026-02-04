from pathlib import Path
from datetime import datetime

# ================= IMPORT ENGINE =================
# Harian
from .warningtools import plot_rob_affected_areas as plot_rob_harian

# Bulanan
from .warningtoolsmonthly import plot_rob_affected_areas as plot_rob_bulanan


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_BASE = BASE_DIR / "output" / "infografis"
OUTPUT_SEBARAN = OUTPUT_BASE / "sebaran"
OUTPUT_REKAP = OUTPUT_BASE / "rekap"

# Aman untuk Streamlit Cloud
OUTPUT_SEBARAN.mkdir(parents=True, exist_ok=True)
OUTPUT_REKAP.mkdir(parents=True, exist_ok=True)


# ============================================================
# MAIN SERVICE
# ============================================================

def generate_infografis_rob(
    affected_areas=None,
    tanggal=None,
    rekap_bul=False,
    **kwargs
):
    """
    Generate infografis rob (harian / bulanan).

    Return:
    {
        success: bool,
        file_path: str | None,
        file_name: str,
        kategori: str,
        image: PIL.Image
    }
    """

    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================
    if affected_areas is None:
        affected_areas = kwargs.get("kecamatan_list")

    if not affected_areas:
        return {
            "success": False,
            "error": "affected_areas / kecamatan_list tidak boleh kosong"
        }

    # ========================================================
    # OUTPUT CONFIG
    # ========================================================
    now = datetime.now()

    if rekap_bul:
        output_dir = OUTPUT_REKAP
        prefix = "rob_rekapbulanan"
        kategori = "rekap"
    else:
        output_dir = OUTPUT_SEBARAN
        prefix = "rob_updateharian"
        kategori = "sebaran"

    file_name = f"{prefix}_{now.strftime('%Y%m%d_%H%M%S')}.png"
    save_path = output_dir / file_name

    # ========================================================
    # GENERATE IMAGE (ENGINE DIPISAH)
    # ========================================================
    try:
        # ================= BULANAN =================
        if rekap_bul:
            final_img = plot_rob_bulanan(
                affected_areas_list=affected_areas,
                save_path=save_path,
                tanggal_rekap=tanggal,
                rekap_bul=True
            )

        # ================= HARIAN ==================
        else:
            final_img = plot_rob_harian(
                affected_areas=affected_areas,
                save_path=save_path,
                tanggal_rekap=tanggal,
                rekap_bul=False
            )

        if final_img is None:
            raise RuntimeError(
                "plot_rob_* tidak mengembalikan PIL.Image"
            )

        # ⚠️ Jangan paksa file ada (Streamlit Cloud bisa read-only)
        file_path = str(save_path) if save_path.exists() else None

        return {
            "success": True,
            "file_path": file_path,
            "file_name": file_name,
            "kategori": kategori,
            "image": final_img
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
