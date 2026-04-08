import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Constants ────────────────────────────────────────────────
SIZE         = 1080
BLUE         = (27, 79, 138)
GREEN        = (39, 174, 96)
WHITE        = (255, 255, 255)
LIGHT_GRAY   = (210, 210, 210)
DARK_OVERLAY = (0, 0, 0, 180)


# ── Font loader ──────────────────────────────────────────────

def _font(size: int) -> ImageFont.FreeTypeFont:
    """Load the best available system font; fall back to default."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    # Pillow built-in default (no size param)
    return ImageFont.load_default()


# ── Helpers ──────────────────────────────────────────────────

def _crop_center(img: Image.Image, w: int, h: int) -> Image.Image:
    """Resize + center-crop image to exact w × h."""
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_h = h
        new_w = int(img.width * h / img.height)
    else:
        new_w = w
        new_h = int(img.height * w / img.width)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top  = (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


def _gradient_overlay(img: Image.Image) -> Image.Image:
    """Blend a dark gradient from transparent (top 30%) to 80% black (bottom)."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    _, h    = img.size
    start_y = int(h * 0.28)
    for y in range(start_y, h):
        progress = (y - start_y) / (h - start_y)
        alpha    = int(min(progress * 1.25, 1.0) * 204)
        draw.line([(0, y), (img.width - 1, y)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img, overlay).convert('RGB')


def _centered_x(draw: ImageDraw.ImageDraw, text: str,
                 font: ImageFont.FreeTypeFont, canvas_w: int) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return (canvas_w - (bbox[2] - bbox[0])) // 2


def _text_shadow(draw, x, y, text, font, fill, shadow=(0, 0, 0, 180)):
    """Draw text with a subtle drop shadow for readability."""
    for dx, dy in ((2, 2), (-1, -1)):
        draw.text((x + dx, y + dy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


# ── Main entry point ─────────────────────────────────────────

def generate_instagram_image(listing_id: str, property_data: dict,
                              cover_photo_path: str) -> str:
    output_path = (
        Path(__file__).resolve().parent.parent
        / "uploads" / listing_id / "instagram.jpg"
    )
    pd = property_data

    # ── Base ─────────────────────────────────────────────────
    img  = Image.open(cover_photo_path).convert('RGB')
    img  = _crop_center(img, SIZE, SIZE)
    img  = _gradient_overlay(img)
    draw = ImageDraw.Draw(img)

    # ── Fonts ─────────────────────────────────────────────────
    f_badge   = _font(36)
    f_price   = _font(92)
    f_city    = _font(48)
    f_details = _font(38)
    f_agent   = _font(34)

    # ── Sale / Rent badge (top-left) ──────────────────────────
    is_sale    = pd.get("operation", "").lower() == "sale"
    badge_text = "FOR SALE" if is_sale else "FOR RENT"
    badge_bg   = BLUE if is_sale else GREEN

    bx, by     = 44, 44
    pad_x, pad_y = 22, 12
    bbox       = draw.textbbox((0, 0), badge_text, font=f_badge)
    bw         = bbox[2] - bbox[0] + pad_x * 2
    bh         = bbox[3] - bbox[1] + pad_y * 2
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=badge_bg)
    draw.text((bx + pad_x, by + pad_y), badge_text, font=f_badge, fill=WHITE)

    # ── Price ─────────────────────────────────────────────────
    price_text = f"${pd.get('price', 0):,.0f}"
    px         = _centered_x(draw, price_text, f_price, SIZE)
    _text_shadow(draw, px, 580, price_text, f_price, WHITE)

    # ── City, State ───────────────────────────────────────────
    city_text  = f"{pd.get('city', '')}, {pd.get('state', '')}"
    cx         = _centered_x(draw, city_text, f_city, SIZE)
    _text_shadow(draw, cx, 700, city_text, f_city, LIGHT_GRAY)

    # ── Details row ───────────────────────────────────────────
    details = (
        f"{pd.get('bedrooms', 0)} Beds"
        f"   \u00b7   "
        f"{pd.get('bathrooms', 0)} Baths"
        f"   \u00b7   "
        f"{pd.get('built_area', 0):,.0f} sq ft"
    )
    dx = _centered_x(draw, details, f_details, SIZE)
    _text_shadow(draw, dx, 775, details, f_details, LIGHT_GRAY)

    # ── Agent bottom strip ────────────────────────────────────
    strip_h = 95
    strip   = Image.new('RGBA', (SIZE, strip_h), DARK_OVERLAY)
    img_rgba = img.convert('RGBA')
    img_rgba.alpha_composite(strip, (0, SIZE - strip_h))
    img  = img_rgba.convert('RGB')
    draw = ImageDraw.Draw(img)

    agent_text = f"{pd.get('agent_name', '')}   \u00b7   {pd.get('agent_phone', '')}"
    ax         = _centered_x(draw, agent_text, f_agent, SIZE)
    draw.text((ax, SIZE - strip_h + 28), agent_text, font=f_agent, fill=WHITE)

    # ── Save ──────────────────────────────────────────────────
    img.save(str(output_path), 'JPEG', quality=95)
    return str(output_path)
