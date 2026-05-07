"""Generate PWA icons for AutoService Pro. Run: python generate_icons.py"""
from PIL import Image, ImageDraw, ImageFont
import os

ICON_DIR = os.path.join(os.path.dirname(__file__), 'static', 'img')
os.makedirs(ICON_DIR, exist_ok=True)

BG_COLOR = '#1a73e8'
FG_COLOR = '#ffffff'


def draw_wrench(draw, cx, cy, size):
    """Draw a simple wrench icon."""
    r = size * 0.35
    # Wrench head (circle with gap)
    draw.ellipse([cx - r, cy - r - size * 0.15, cx + r, cy + r - size * 0.15],
                 outline=FG_COLOR, width=max(int(size * 0.08), 2))
    # Handle
    hw = size * 0.1
    draw.rectangle([cx - hw, cy - size * 0.05, cx + hw, cy + size * 0.4],
                   fill=FG_COLOR)
    # Head fill
    draw.ellipse([cx - r * 0.6, cy - r * 0.6 - size * 0.15,
                  cx + r * 0.6, cy + r * 0.6 - size * 0.15],
                 fill=FG_COLOR)


def create_icon(size, filename, maskable=False):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if maskable:
        # Maskable: fill entire canvas, safe zone is inner 80%
        draw.rectangle([0, 0, size, size], fill=BG_COLOR)
        icon_size = int(size * 0.6)
    else:
        # Regular: circle background
        margin = int(size * 0.02)
        draw.ellipse([margin, margin, size - margin, size - margin], fill=BG_COLOR)
        icon_size = int(size * 0.5)

    cx, cy = size // 2, size // 2
    draw_wrench(draw, cx, cy, icon_size)

    # Add "A" letter
    try:
        font_size = int(size * 0.18)
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()
    text = "A"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy + icon_size * 0.15), text, fill=FG_COLOR, font=font)

    img.save(os.path.join(ICON_DIR, filename), 'PNG')
    print(f'Created {filename} ({size}x{size})')


def create_badge(size, filename):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([0, 0, size, size], fill=BG_COLOR)
    # Simple wrench symbol
    draw_wrench(draw, size // 2, size // 2, int(size * 0.5))
    img.save(os.path.join(ICON_DIR, filename), 'PNG')
    print(f'Created {filename} ({size}x{size})')


if __name__ == '__main__':
    create_icon(192, 'icon-192.png')
    create_icon(512, 'icon-512.png')
    create_icon(512, 'icon-maskable-512.png', maskable=True)
    create_badge(72, 'badge-72.png')
    print('Done! Icons saved to', ICON_DIR)
