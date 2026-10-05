"""
Shared utilities for accounts app.
"""
import hashlib
from io import BytesIO
from django.core.files.base import ContentFile


def generate_avatar(name, size=200):
    """
    Generates a simple colored-circle avatar with initials, entirely with
    Pillow (no external image downloads or bundled font files needed, so
    this works identically on any machine/OS). Used as an automatic
    profile photo for users who haven't uploaded their own yet.
    """
    from PIL import Image, ImageDraw, ImageFont

    colors = ['#0F766E', '#2563EB', '#DC2626', '#7C3AED', '#EA580C', '#0891B2', '#DB2777', '#65A30D']
    idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(colors)
    bg_color = colors[idx]

    img = Image.new('RGB', (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)
    parts = [p for p in name.split() if p]
    initials = ''.join([p[0].upper() for p in parts[:2]]) or '?'

    try:
        font = ImageFont.load_default(size=int(size * 0.42))
    except TypeError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - text_w) / 2 - bbox[0], (size - text_h) / 2 - bbox[1]),
        initials, fill='white', font=font
    )

    buf = BytesIO()
    img.save(buf, format='JPEG', quality=90)
    buf.seek(0)
    return ContentFile(buf.read())
