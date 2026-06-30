# Sub to QR Code PDF Generator

A Python script that fetches subscription links online, extracts config names, and generates a beautiful PDF with QR codes.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Online Fetch** — automatically grabs subscription content from your panel
- **Config Names** — extracts and displays real config names (not raw links)
- **Country Flags** — downloads and renders actual flag images next to config names
- **High Quality QR** — 400px resolution with LANCZOS resampling (perfectly scannable)
- **Professional Layout** — 4×5 grid (20 QR per A4 page) with styled header
- **Shop Branding** — customizable shop name at the top of every page
- **Shamsi Date** — automatic Jalali/Shamsi date on header
- **Auto Filename** — output named as `ShopName - Day Month Year.pdf`

## Preview

Each page shows:
- **Header bar** — shop name (left) + Shamsi date (right) + gold accent line
- **20 QR codes** — 4 columns × 5 rows with rounded cell borders
- **Config names** — one line below each QR with country flag image

## Installation

```bash
pip install qrcode[pil] reportlab jdatetime
```

## Usage

### Method 1: Using subs.txt (Recommended)

1. Create a file called `subs.txt` in the same folder as the script
2. Put your subscription links in it (one per line):

```
/sub/djMsMTIwLDE3ODI3NzQxNTE618e665809
/sub/djMsMTIxLDE3ODI3NzQxNTEa0789b50d2
/sub/djMsMTIyLDE3ODI3NzQxNTE68895c7c5e
```

3. Run the script:

```bash
python sub_to_qr_pdf.py
```

4. Enter your shop name when asked (or press Enter for default)
5. Done! Your PDF is ready.

### Method 2: Manual Input

If `subs.txt` doesn't exist, the script will ask you to paste links directly in the terminal. Type `END` when done.

## Settings

Edit the `SETTINGS` section at the top of the script:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN` | `https://...` | Your subscription domain |
| `SHOP_TITLE` | `VMob` | Default shop name |
| `COLS` | `4` | Grid columns |
| `ROWS` | `5` | Grid rows |
| `QR_BOX` | `120` | QR size in PDF (points) |
| `QR_RES` | `400` | QR resolution (pixels) |
| `CONFIGS_PER_QR` | `1` | Config names shown below each QR |
| `HEADER_BG` | Blue RGB | Header background color |
| `ACCENT` | Gold RGB | Accent line color |

## Output

PDF file named: `ShopName - Day Month Year.pdf`

Example: `VMob - 9 Tir 1405.pdf`

## Requirements

- Python 3.8+
- Internet connection (to fetch subscriptions and flags)
- Libraries: `qrcode`, `reportlab`, `jdatetime` (optional)

## Author

**Mr.HamidRouter** — [GitHub](https://github.com/Mr-HamidRouter)

## License

MIT License — feel free to use and modify.
