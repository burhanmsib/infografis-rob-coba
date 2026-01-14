import io
import os
import requests
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from PIL import Image as PILImage, UnidentifiedImageError


# =====================================================
# HELPER
# =====================================================
def safe(val, default="-"):
    return val if val not in [None, ""] else default


def load_image_from_url(url):
    """
    Ambil gambar dari URL dan kembalikan BytesIO
    """
    if not url:
        return None

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        img_data = io.BytesIO(response.content)
        img = PILImage.open(img_data)
        img.verify()

        img_data.seek(0)
        return img_data

    except (requests.RequestException, UnidentifiedImageError):
        return None
    except Exception:
        return None


# =====================================================
# PDF – SATU KEJADIAN
# =====================================================
def generate_event_pdf(record: dict):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Justify",
        alignment=4,
        leading=14
    ))

    story = []

    # ================= HEADER =================
    story.append(Paragraph(
        "<b>LAPORAN KEJADIAN BANJIR ROB</b>",
        styles["Title"]
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        f"Tanggal Cetak: {datetime.now().strftime('%d %B %Y')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 16))

    # ================= IDENTITAS =================
    identitas = f"""
    <b>Lokasi</b>      : {safe(record.get('Lokasi'))}<br/>
    <b>Kecamatan</b>   : {safe(record.get('Kecamatan'))}<br/>
    <b>Kabupaten</b>   : {safe(record.get('Kabupaten'))}<br/>
    <b>Provinsi</b>    : {safe(record.get('Provinsi'))}<br/><br/>

    <b>Tanggal</b>     : {safe(record.get('Tanggal'))}<br/>
    <b>Waktu</b>       : {safe(record.get('Waktu'))} WIB<br/>
    <b>Koordinat</b>   : {safe(record.get('Latitude'))}, {safe(record.get('Longitude'))}
    """

    story.append(Paragraph("<b>IDENTITAS KEJADIAN</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(identitas, styles["Justify"]))
    story.append(Spacer(1, 14))

    # ================= INFORMASI KEJADIAN =================
    info = f"""
    <b>Ketinggian Genangan</b> : {safe(record.get('Ketinggian'))} cm<br/><br/>
    <b>Dampak Kejadian</b> :<br/>
    {safe(record.get('Dampak'))}
    """

    story.append(Paragraph("<b>INFORMASI KEJADIAN</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(info, styles["Justify"]))
    story.append(Spacer(1, 14))

    # ================= DOKUMENTASI =================
    story.append(Paragraph("<b>DOKUMENTASI</b>", styles["Heading2"]))
    story.append(Spacer(1, 8))

    img_url = record.get("Gambar")
    img_data = load_image_from_url(img_url)

    if img_data:
        story.append(Image(img_data, width=4.5 * inch, height=3 * inch))
    else:
        story.append(Paragraph(
            "Tidak tersedia dokumentasi foto.",
            styles["Normal"]
        ))

    story.append(Spacer(1, 14))

    # ================= SUMBER =================
    story.append(Paragraph("<b>SUMBER INFORMASI</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        safe(record.get("Sumber")),
        styles["Justify"]
    ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%"))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Dokumen ini dihasilkan secara otomatis oleh Sistem Peta Interaktif Banjir Rob BMKG.",
        styles["Normal"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


# =====================================================
# PDF – REKAP MULTI KEJADIAN (PER TANGGAL)
# =====================================================
def generate_multiple_events_pdf(records: list, tanggal):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph(
        f"<b>LAPORAN KEJADIAN BANJIR ROB</b><br/>Tanggal: {tanggal}",
        styles["Title"]
    ))
    story.append(Spacer(1, 20))

    if not records:
        story.append(Paragraph(
            "Tidak terdapat kejadian banjir rob pada tanggal tersebut.",
            styles["Normal"]
        ))
    else:
        for i, rec in enumerate(records, start=1):
            story.append(Paragraph(
                f"<b>Kejadian {i}</b>",
                styles["Heading3"]
            ))
            story.append(Spacer(1, 6))

            isi = f"""
            Lokasi      : {safe(rec.get('Lokasi'))}<br/>
            Kecamatan   : {safe(rec.get('Kecamatan'))}<br/>
            Kabupaten   : {safe(rec.get('Kabupaten'))}<br/>
            Provinsi    : {safe(rec.get('Provinsi'))}<br/>
            Tanggal     : {safe(rec.get('Tanggal'))}<br/>
            Waktu       : {safe(rec.get('Waktu'))} WIB<br/>
            Koordinat   : {safe(rec.get('Latitude'))}, {safe(rec.get('Longitude'))}<br/>
            Ketinggian  : {safe(rec.get('Ketinggian'))} cm<br/><br/>
            Dampak      : {safe(rec.get('Dampak'))}<br/><br/>
            Sumber      : {safe(rec.get('Sumber'))}
            """

            story.append(Paragraph(isi, styles["Normal"]))
            story.append(Spacer(1, 12))
            story.append(HRFlowable(width="100%"))
            story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer

