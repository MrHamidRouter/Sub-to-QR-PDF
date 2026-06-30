#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sub to QR Code PDF Generator
=============================

Chand ta link-e subscription ro migire, esm-e config-ha ro estekhraj mikone,
va ye PDF barksibe ba QR Code baraye har sub misaze.

Estefadeh:
    1. Link-haye sub ro dakhele "subs.txt" bezar (har khat yeki).
    2. Script ro run kon:
        python sub_to_qr_pdf.py
    3. PDF tahvil dade mishe.

Niaz-ha:
    pip install qrcode[pil] reportlab jdatetime

Author: Mr.HamidRouter
"""

import os
import sys
import ssl
import re
import base64
import urllib.request
from urllib.parse import unquote

try:
    import jdatetime
    HAS_JDATETIME = True
except ImportError:
    HAS_JDATETIME = False

import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# ============================ SETTINGS ============================
DOMAIN = "https://hamid.getconnected.click:8000"   # your domain
COLS = 4            # columns: 4 x 5 = 20 QR per page
ROWS = 5            # rows
QR_PER_PAGE = COLS * ROWS   # 20
QR_BOX = 120        # QR size (point) in PDF
QR_RES = 400         # QR resolution (pixel) -> ~10 px/module
LABEL_FONT = 9      # config name font size
LINE_GAP = 11       # line gap
CONFIGS_PER_QR = 1  # only 1 config name under each QR
TIMEOUT = 30        # network timeout (sec)
OUTPUT_FILE = "qr_codes.pdf"
INPUT_FILE = "subs.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
SHOP_TITLE = "VMob"        # shop title (top of page)
HEADER_H = 55              # header height
# ----- colors -----
HEADER_BG = (0.13, 0.35, 0.62)     # header blue
HEADER_FG = (1, 1, 1)              # header white text
ACCENT    = (0.95, 0.74, 0.17)     # gold line below header
CELL_BORDER = (0.80, 0.80, 0.80)   # cell border gray
CELL_PAD   = 6                     # cell padding
# ================================================================


def clean_name(name: str) -> str:
    """Extract config name, replace flag emojis with [FLAG:XX] markers,
    remove other emojis (e.g. icon, package, date)."""
    name = unquote(name).strip()
    out = []
    i = 0
    n = len(name)
    while i < n:
        c = name[i]
        # regional indicator pair = country flag
        if (i + 1 < n and
                0x1F1E6 <= ord(c) <= 0x1F1FF and
                0x1F1E6 <= ord(name[i + 1]) <= 0x1F1FF):
            cc = chr(ord(c) - 0x1F1E6 + 65) + chr(ord(name[i + 1]) - 0x1F1E6 + 65)
            out.append("[FLAG:" + cc + "]")
            i += 2
            continue
        # skip other emojis/symbols
        if ord(c) > 0x2600:
            i += 1
            continue
        out.append(c)
        i += 1

    s = "".join(out)
    parts = [p.strip() for p in s.split("|")]
    parts = [p for p in parts if p and p not in ("-",)]
    return " | ".join(parts)


def extract_config_names(decoded_text: str):
    """Extract config names from decoded subscription text.
    Supports: vless://, vmess://, trojan://, ss://"""
    protocols = ("vless://", "vmess://", "trojan://", "ss://")
    names = []
    for line in decoded_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if not line.startswith(protocols):
            continue
        if "#" in line:
            raw_name = line.split("#", 1)[1]
            nm = clean_name(raw_name)
            if nm:
                names.append(nm)
    # remove duplicates
    seen = []
    for nm in names:
        if nm not in seen:
            seen.append(nm)
    return seen


def fetch_sub_names(sub_path: str):
    """Fetch a subscription link online and return (url, config_names)."""
    if sub_path.startswith("http://") or sub_path.startswith("https://"):
        url = sub_path
    elif sub_path.startswith("/sub/"):
        url = DOMAIN + sub_path
    elif sub_path.startswith("sub/"):
        url = DOMAIN + "/" + sub_path
    else:
        url = DOMAIN + "/" + sub_path

    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    raw = urllib.request.urlopen(req, context=ctx, timeout=TIMEOUT).read()

    try:
        decoded = base64.b64decode(raw).decode("utf-8", "ignore")
        if len(decoded) < 5 and len(raw) > 5:
            decoded = raw.decode("utf-8", "ignore")
    except Exception:
        decoded = raw.decode("utf-8", "ignore")

    return url, extract_config_names(decoded)


def make_qr_image(data: str, box: int = QR_BOX, res: int = QR_RES):
    """Generate QR code at high resolution using LANCZOS resampling."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((res, res), resample=3)  # LANCZOS = best quality
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


# ----- Flag image cache (download once, reuse) -----
_FLAG_CACHE = {}


def get_flag_image(cc: str):
    """Download and cache a country flag image from flagcdn.com."""
    cc = cc.upper()
    if cc in _FLAG_CACHE:
        return _FLAG_CACHE[cc]
    url = f"https://flagcdn.com/w80/{cc.lower()}.png"
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        raw = urllib.request.urlopen(req, context=ctx, timeout=15).read()
        buf = BytesIO(raw)
        img = ImageReader(buf)
        _FLAG_CACHE[cc] = img
        return img
    except Exception as e:
        print(f"      [!] flag {cc} download failed: {e}")
        _FLAG_CACHE[cc] = None
        return None


def get_shamsi_date() -> str:
    """Return today's date in Shamsi/Jalali format. Falls back to Gregorian."""
    if HAS_JDATETIME:
        today = jdatetime.date.today()
        months = ["Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad",
                  "Shahrivar", "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand"]
        try:
            mname = months[today.month - 1]
            return f"{today.day} {mname} {today.year}"
        except Exception:
            return f"{today.year}/{today.month:02d}/{today.day:02d}"
    else:
        import datetime
        d = datetime.date.today()
        return f"{d.year}/{d.month:02d}/{d.day:02d}"


def draw_header(c, page_w, page_h):
    """Draw header bar (blue background, gold accent line, shop title, date)."""
    bot = page_h - HEADER_H

    # blue header background
    c.setFillColorRGB(*HEADER_BG)
    c.rect(0, bot, page_w, HEADER_H, fill=1, stroke=0)

    # gold accent line below header
    c.setFillColorRGB(*ACCENT)
    c.rect(0, bot - 4, page_w, 4, fill=1, stroke=0)

    # shop title (left, white, bold)
    c.setFont("Helvetica-Bold", 22)
    c.setFillColorRGB(*HEADER_FG)
    c.drawString(25, bot + 17, SHOP_TITLE)

    # shamsi date (right, white, smaller)
    date_str = get_shamsi_date()
    c.setFont("Helvetica", 11)
    dw = c.stringWidth(date_str, "Helvetica", 11)
    c.drawString(page_w - 25 - dw, bot + 20, date_str)
    c.setFillColorRGB(0, 0, 0)


def draw_cell_frame(c, x, y, w, h):
    """Draw a rounded rectangle border around a cell."""
    c.setLineWidth(0.6)
    c.setStrokeColorRGB(*CELL_BORDER)
    c.roundRect(x, y, w, h, 4, fill=0, stroke=1)


def draw_text_with_flags(c, x_center, y, text, font_name, font_size):
    """Draw centered text with inline flag images for [FLAG:XX] markers."""
    c.setFont(font_name, font_size)
    # split text into tokens: text parts and [FLAG:XX] markers
    tokens = []
    for m in re.finditer(r"\[FLAG:([A-Za-z]{2})\]|([^\[]+)", text):
        flag = m.group(1)
        txt = m.group(2)
        if flag:
            tokens.append(("flag", flag.upper()))
        elif txt:
            tokens.append(("text", txt))

    flag_h = font_size
    flag_w = flag_h * 1.333
    flag_gap = 1.5

    widths = []
    for kind, val in tokens:
        if kind == "text":
            w = c.stringWidth(val, font_name, font_size)
        else:
            w = flag_w + flag_gap
        widths.append(w)

    total_w = sum(widths)
    x = x_center - total_w / 2

    for (kind, val), w in zip(tokens, widths):
        if kind == "text":
            c.drawString(x, y, val)
            x += w
        else:
            img = get_flag_image(val)
            if img is not None:
                c.drawImage(img, x, y - 1, flag_w, flag_h,
                            mask='auto', preserveAspectRatio=True)
            x += w
    return total_w


def read_subs():
    """Read subscription links from subs.txt, or ask user to paste them."""
    subs = []
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    subs.append(line)
        if subs:
            print(f"[+] {len(subs)} subscription(s) loaded from '{INPUT_FILE}'.")
            return subs

    print("Paste subscription links (one per line).")
    print("When done, type:  END")
    while True:
        line = sys.stdin.readline().strip()
        if line.upper() == "END":
            break
        if line:
            subs.append(line)
    return subs


def build_pdf(subs, output_path=OUTPUT_FILE):
    """Build PDF with QR codes grid, config names, and country flags."""
    if not subs:
        print("No subscriptions found!")
        return

    page_w, page_h = A4
    margin = 22
    cell_gap = 6
    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin - HEADER_H
    cell_w = (usable_w - cell_gap * (COLS - 1)) / COLS
    cell_h = (usable_h - cell_gap * (ROWS - 1)) / ROWS

    c = canvas.Canvas(output_path, pagesize=A4)

    total = len(subs)
    print("=" * 55)
    print(f"[i] {total} subscription(s) to process ...")
    print(f"[i] Title: {SHOP_TITLE}  |  Date: {get_shamsi_date()}")
    print("=" * 55)

    draw_header(c, page_w, page_h)

    items = []
    for i, raw in enumerate(subs, 1):
        try:
            url, names = fetch_sub_names(raw)
            if not names:
                fallback = raw if raw.startswith("/sub/") else "/sub/" + raw.split("/sub/")[-1]
                names = [fallback]
            print(f"  [{i}/{total}] OK -> {len(names)} config   ({url})")
        except Exception as e:
            url = raw if raw.startswith("http") else DOMAIN + "/" + raw.lstrip("/")
            names = ["(ERROR)"]
            print(f"  [{i}/{total}] ERROR: {e}   ({url})")
        items.append({"qr_url": url, "names": names})

    print("\n[+] Building PDF ...")
    grid_top = page_h - HEADER_H - margin
    for idx, it in enumerate(items):
        pos_in_page = idx % QR_PER_PAGE
        col = pos_in_page % COLS
        row = pos_in_page // COLS

        cell_x = margin + col * (cell_w + cell_gap)
        cell_y = grid_top - (row + 1) * cell_h - row * cell_gap

        # cell frame
        draw_cell_frame(c, cell_x, cell_y, cell_w, cell_h)

        # QR code centered in top of cell
        qr_x = cell_x + (cell_w - QR_BOX) / 2
        qr_y = cell_y + cell_h - QR_BOX - 8

        img_reader = make_qr_image(it["qr_url"])
        c.drawImage(img_reader, qr_x, qr_y, QR_BOX, QR_BOX,
                    mask='auto', preserveAspectRatio=True)

        # config name below QR (1 line with flag image)
        label_x = cell_x + cell_w / 2
        y_label = qr_y - 14

        shown = it["names"][:CONFIGS_PER_QR]
        for nm in shown:
            text = nm if len(nm) <= 30 else nm[:27] + "..."
            draw_text_with_flags(c, label_x, y_label, text,
                                 "Helvetica", LABEL_FONT)
            y_label -= LINE_GAP

        # next page
        if (idx + 1) % QR_PER_PAGE == 0 and (idx + 1) < len(items):
            c.showPage()
            draw_header(c, page_w, page_h)

    c.save()
    print(f"\n[OK] PDF saved: {output_path}")


def main():
    global SHOP_TITLE
    print("=" * 55)
    print("   Sub to QR Code PDF Generator")
    print(f"   Domain: {DOMAIN}")
    print("=" * 55)

    ans = input(f"\nEnter shop name (Enter = {SHOP_TITLE}): ").strip()
    if ans:
        SHOP_TITLE = ans

    date_str = get_shamsi_date()
    safe_title = SHOP_TITLE.replace("/", "-").replace("\\", "-").strip()
    output_file = f"{safe_title} - {date_str}.pdf"

    subs = read_subs()
    build_pdf(subs, output_file)


if __name__ == "__main__":
    main()
