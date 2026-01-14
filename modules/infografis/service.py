from pathlib import Path
from datetime import datetime
from .warningtools import plot_rob_affected_areas

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_BASE = BASE_DIR / "output" / "infografis"
OUTPUT_SEBARAN = OUTPUT_BASE / "sebaran"
OUTPUT_REKAP = OUTPUT_BASE / "rekap"

OUTPUT_SEBARAN.mkdir(parents=True, exist_ok=True)
OUTPUT_REKAP.mkdir(parents=True, exist_ok=True)


def generate_infografis_rob(
    affected_areas=None,
    tanggal=None,
    rekap_bul=False,
    **kwargs
):
    if affected_areas is None:
        affected_areas = kwargs.get("kecamatan_list")

    if not affected_areas:
        raise ValueError("affected_areas / kecamatan_list tidak boleh kosong")

    now = datetime.now()

    if rekap_bul:
        output_dir = OUTPUT_REKAP
        prefix = "rob_rekapbulanan"
    else:
        output_dir = OUTPUT_SEBARAN
        prefix = "rob_updateharian"

    file_name = f"{prefix}_{now.strftime('%Y%m%d_%H%M%S')}.png"
    save_path = output_dir / file_name

    try:
        plot_rob_affected_areas(
            affected_areas=affected_areas,
            save_path=save_path,
            tanggal_rekap=tanggal,
            rekap_bul=rekap_bul,
        )

        return {
            "success": True,
            "file_path": str(save_path),
            "file_name": file_name,
            "kategori": "rekap" if rekap_bul else "sebaran"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }