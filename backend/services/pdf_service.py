import io
from pathlib import Path
from PIL import Image as PilImage
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

# ── Brand colors ────────────────────────────────────────────
BLUE       = HexColor('#1B4F8A')
BLUE_LIGHT = HexColor('#EBF3FC')
GREEN      = HexColor('#27AE60')
GRAY_TEXT  = HexColor('#444444')
GRAY_LIGHT = HexColor('#888888')
GRAY_LINE  = HexColor('#DDDDDD')

PAGE_W, PAGE_H = letter   # 612 x 792 pt
MARGIN = 36
CONTENT_W = PAGE_W - 2 * MARGIN


# ── Helpers ──────────────────────────────────────────────────

def _crop_to_reader(photo_path: str, target_w: float, target_h: float) -> ImageReader:
    """Center-crop a photo to the target aspect ratio and return an ImageReader."""
    img = PilImage.open(photo_path).convert("RGB")
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Image is wider than target — crop sides
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        # Image is taller than target — crop top/bottom
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return ImageReader(buf)



def _draw_wrapped_text(c, text, x, y, max_width, font, size, line_h, color=None):
    """Draw word-wrapped text; returns y after the last line."""
    if color:
        c.setFillColor(color)
    c.setFont(font, size)
    words = text.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if stringWidth(candidate, font, size) <= max_width:
            line = candidate
        else:
            if line:
                c.drawString(x, y, line)
                y -= line_h
            line = word
    if line:
        c.drawString(x, y, line)
        y -= line_h
    return y


def _section_heading(c, label, y):
    """Draw a blue section heading with underline; returns y after heading."""
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, y, label)
    c.setFillColor(BLUE)
    c.rect(MARGIN, y - 5, CONTENT_W, 1.5, fill=1, stroke=0)
    return y - 20


def _check_page(c, y, needed=80):
    """Start a new page if not enough room; returns updated y."""
    if y < needed:
        c.showPage()
        return PAGE_H - MARGIN
    return y


# ── Main entry point ─────────────────────────────────────────

def generate_pdf(listing_id: str, property_data: dict,
                 photo_paths: list, description: str) -> str:
    output_path = (
        Path(__file__).resolve().parent.parent
        / "uploads" / listing_id / "listing.pdf"
    )
    pd_data = property_data

    c = pdfcanvas.Canvas(str(output_path), pagesize=letter)
    y = PAGE_H

    # ── Header ───────────────────────────────────────────────
    header_h = 52
    c.setFillColor(BLUE)
    c.rect(0, PAGE_H - header_h, PAGE_W, header_h, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(MARGIN, PAGE_H - 36, "ListPro")

    op      = "FOR SALE" if pd_data.get("operation", "").upper() == "SALE" else "FOR RENT"
    p_type  = pd_data.get("property_type", "Property")
    title   = f"{p_type}  —  {op}"
    c.setFont("Helvetica", 12)
    tw = stringWidth(title, "Helvetica", 12)
    c.drawString(PAGE_W - MARGIN - tw, PAGE_H - 36, title)

    y = PAGE_H - header_h - 16

    # ── Cover photo ──────────────────────────────────────────
    cover_path = pd_data.get("cover_photo_path", "")
    if cover_path and Path(cover_path).exists():
        photo_h = 210
        try:
            reader = _crop_to_reader(cover_path, CONTENT_W, photo_h)
            c.drawImage(reader, MARGIN, y - photo_h, width=CONTENT_W, height=photo_h)
            y -= photo_h + 14
        except Exception:
            y -= 14
    else:
        y -= 14

    # ── Stats row ────────────────────────────────────────────
    stats = [
        ("PRICE",   f"${pd_data.get('price', 0):,.0f}"),
        ("BEDS",    str(pd_data.get("bedrooms", 0))),
        ("BATHS",   str(pd_data.get("bathrooms", 0))),
        ("SQ FT",   f"{pd_data.get('built_area', 0):,.0f}"),
        ("PARKING", str(pd_data.get("parking", 0))),
    ]
    n_stats  = len(stats)
    stat_w   = CONTENT_W / n_stats
    stat_h   = 50
    gap      = 3

    for i, (label, value) in enumerate(stats):
        sx = MARGIN + i * stat_w
        # Background box
        c.setFillColor(BLUE_LIGHT)
        c.rect(sx + gap, y - stat_h, stat_w - gap * 2, stat_h, fill=1, stroke=0)
        # Blue top accent
        c.setFillColor(BLUE)
        c.rect(sx + gap, y - 4, stat_w - gap * 2, 4, fill=1, stroke=0)
        # Label
        c.setFillColor(GRAY_LIGHT)
        c.setFont("Helvetica", 7)
        c.drawCentredString(sx + stat_w / 2, y - 18, label)
        # Value
        c.setFillColor(HexColor('#1a1a1a'))
        val_size = 13 if len(value) < 9 else 10
        c.setFont("Helvetica-Bold", val_size)
        c.drawCentredString(sx + stat_w / 2, y - 38, value)

    y -= stat_h + 20

    # ── Description ──────────────────────────────────────────
    y = _check_page(c, y, 160)
    y = _section_heading(c, "Property Description", y)

    paragraphs = [p.strip() for p in description.split('\n\n') if p.strip()]
    for para in paragraphs:
        y = _check_page(c, y, 60)
        y = _draw_wrapped_text(c, para, MARGIN, y, CONTENT_W,
                               "Helvetica", 9.5, 14, GRAY_TEXT)
        y -= 8

    # ── Amenities ────────────────────────────────────────────
    amenities = pd_data.get("amenities", [])
    if amenities:
        y -= 6
        y = _check_page(c, y, 120)
        y = _section_heading(c, "Amenities", y)

        col_w  = CONTENT_W / 2
        row_h  = 18
        for i, amenity in enumerate(amenities):
            col = i % 2
            row = i // 2
            ax  = MARGIN + col * col_w
            ay  = y - row * row_h

            if ay < MARGIN + 20:
                c.showPage()
                y  = PAGE_H - MARGIN
                ay = y - (i % 2) * row_h

            c.setFillColor(GREEN)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(ax, ay, "\u2713")          # ✓
            c.setFillColor(GRAY_TEXT)
            c.setFont("Helvetica", 9.5)
            c.drawString(ax + 14, ay, amenity)

        rows = (len(amenities) + 1) // 2
        y -= rows * row_h + 14

    # ── Additional photos ────────────────────────────────────
    valid_photos = [p for p in photo_paths if Path(p).exists()]
    if valid_photos:
        y -= 4
        y = _check_page(c, y, 160)
        y = _section_heading(c, "Property Photos", y)

        thumb_w = (CONTENT_W - 10) / 2
        thumb_h = thumb_w * 0.62

        for i, photo_path in enumerate(valid_photos[:6]):
            col = i % 2
            row = i // 2
            px  = MARGIN + col * (thumb_w + 10)
            py  = y - row * (thumb_h + 10) - thumb_h

            if py < MARGIN:
                c.showPage()
                y  = PAGE_H - MARGIN - 20
                py = y - thumb_h

            try:
                reader = _crop_to_reader(photo_path, thumb_w, thumb_h)
                c.drawImage(reader, px, py, width=thumb_w, height=thumb_h)
            except Exception:
                pass

        rows_used = (len(valid_photos[:6]) + 1) // 2
        y -= rows_used * (thumb_h + 10) + 10

    # ── Agent contact footer ─────────────────────────────────
    y = _check_page(c, y, 70)
    y -= 8
    c.setFillColor(GRAY_LINE)
    c.rect(MARGIN, y, CONTENT_W, 1, fill=1, stroke=0)
    y -= 18

    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, y, pd_data.get("agent_name", ""))

    c.setFillColor(GRAY_TEXT)
    c.setFont("Helvetica", 9)
    parts = []
    if pd_data.get("agent_phone"): parts.append(pd_data["agent_phone"])
    if pd_data.get("agent_email"): parts.append(pd_data["agent_email"])
    c.drawString(MARGIN, y - 14, "  |  ".join(parts))

    c.setFillColor(HexColor('#AAAAAA'))
    c.setFont("Helvetica", 7.5)
    c.drawRightString(PAGE_W - MARGIN, y, "Generated by ListPro")

    c.save()
    return str(output_path)
