"""Generate a banner image for the Telegram bot."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'img')
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 800, 400
BG = '#0f172a'
ACCENT = '#1a73e8'
GREEN = '#34a853'
WHITE = '#ffffff'
GRAY = '#94a3b8'


def create_banner():
    img = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Gradient accent strip at top
    for y in range(6):
        draw.rectangle([0, y, W, y], fill=ACCENT)

    # Decorative circles (abstract car/gear shapes)
    draw.ellipse([50, 80, 180, 210], outline=ACCENT, width=3)
    draw.ellipse([80, 110, 150, 180], outline=ACCENT, width=2)
    draw.ellipse([620, 200, 780, 360], outline='#334155', width=2)
    draw.ellipse([650, 230, 750, 330], outline='#334155', width=2)

    # Wrench icon (stylized)
    draw.line([110, 220, 110, 300], fill=ACCENT, width=8)
    draw.ellipse([90, 280, 130, 320], fill=ACCENT)

    # Small decorative dots
    for x in range(100, 700, 40):
        draw.ellipse([x, 370, x + 4, 374], fill='#1e293b')

    # Title
    try:
        font_big = ImageFont.truetype("arial.ttf", 48)
        font_med = ImageFont.truetype("arial.ttf", 22)
        font_sm = ImageFont.truetype("arial.ttf", 16)
    except (OSError, IOError):
        font_big = ImageFont.load_default()
        font_med = font_big
        font_sm = font_big

    # Main title
    draw.text((220, 70), "AutoService", fill=WHITE, font=font_big)
    draw.text((220, 125), "Pro", fill=ACCENT, font=font_big)

    # Tagline
    draw.text((220, 190), "Your car repair tracker", fill=GRAY, font=font_med)

    # Feature badges
    features = [
        ("Status tracking", GREEN),
        ("Notifications", ACCENT),
        ("Online booking", '#fbbc04'),
    ]
    x_pos = 220
    for text, color in features:
        bbox = draw.textbbox((0, 0), text, font=font_sm)
        tw = bbox[2] - bbox[0]
        draw.rounded_rectangle([x_pos, 250, x_pos + tw + 20, 280], radius=12, fill=color)
        draw.text((x_pos + 10, 254), text, fill=WHITE, font=font_sm)
        x_pos += tw + 35

    # Bottom accent line
    draw.rectangle([0, H - 4, W, H], fill=ACCENT)

    path = os.path.join(OUT_DIR, 'bot_banner.png')
    img.save(path, 'PNG')
    print(f'Created {path}')
    return path


def create_welcome_card():
    """Small welcome image for /start."""
    w, h = 600, 300
    img = Image.new('RGB', (w, h), '#0f172a')
    draw = ImageDraw.Draw(img)

    # Background pattern
    for i in range(0, w, 30):
        draw.line([i, 0, i, h], fill='#1e293b', width=1)
    for i in range(0, h, 30):
        draw.line([0, i, w, i], fill='#1e293b', width=1)

    # Central circle
    cx, cy = w // 2, h // 2 - 20
    r = 60
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)

    # Wrench symbol in circle
    draw.line([cx - 15, cy - 25, cx - 15, cy + 25], fill=WHITE, width=6)
    draw.ellipse([cx - 25, cy + 15, cx - 5, cy + 35], fill=WHITE)
    draw.line([cx + 15, cy - 25, cx + 15, cy + 25], fill=WHITE, width=6)
    draw.ellipse([cx + 5, cy + 15, cx + 25, cy + 35], fill=WHITE)

    try:
        font = ImageFont.truetype("arial.ttf", 28)
        font_sm = ImageFont.truetype("arial.ttf", 14)
    except (OSError, IOError):
        font = ImageFont.load_default()
        font_sm = font

    title = "AutoService Pro"
    bbox = draw.textbbox((0, 0), title, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, cy + r + 15), title, fill=WHITE, font=font)

    sub = "Car repair management system"
    bbox2 = draw.textbbox((0, 0), sub, font=font_sm)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((w - tw2) / 2, cy + r + 50), sub, fill=GRAY, font=font_sm)

    # Accent line bottom
    draw.rectangle([0, h - 3, w, h], fill=ACCENT)

    path = os.path.join(OUT_DIR, 'bot_welcome.png')
    img.save(path, 'PNG')
    print(f'Created {path}')
    return path


def create_status_card():
    """Status check image."""
    w, h = 600, 200
    img = Image.new('RGB', (w, h), '#0f172a')
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
        font_sm = ImageFont.truetype("arial.ttf", 14)
    except (OSError, IOError):
        font = ImageFont.load_default()
        font_sm = font

    # Progress bar
    bar_y = 80
    bar_h = 12
    draw.rounded_rectangle([40, bar_y, w - 40, bar_y + bar_h], radius=6, fill='#334155')
    draw.rounded_rectangle([40, bar_y, 40 + int((w - 80) * 0.6), bar_y + bar_h], radius=6, fill=GREEN)

    # Status dots
    steps = ['New', 'Diag', 'Work', 'Done', 'Ready']
    step_w = (w - 80) / (len(steps) - 1)
    for i, label in enumerate(steps):
        x = 40 + int(i * step_w)
        color = GREEN if i < 3 else (ACCENT if i == 3 else '#334155')
        draw.ellipse([x - 8, bar_y - 2, x + 8, bar_y + bar_h + 2], fill=color)
        bbox = draw.textbbox((0, 0), label, font=font_sm)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw / 2, bar_y + bar_h + 8), label, fill=GRAY, font=font_sm)

    title = "Order Status"
    bbox = draw.textbbox((0, 0), title, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, 25), title, fill=WHITE, font=font)

    draw.rectangle([0, h - 3, w, h], fill=ACCENT)

    path = os.path.join(OUT_DIR, 'bot_status.png')
    img.save(path, 'PNG')
    print(f'Created {path}')
    return path


if __name__ == '__main__':
    create_banner()
    create_welcome_card()
    create_status_card()
    print('All bot images generated!')
