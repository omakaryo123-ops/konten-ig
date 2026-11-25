"""Alat bersama untuk template desain OMAKARYO (warna, font, logo, teks)."""
import json
import os

from PIL import Image, ImageDraw, ImageFont

FOLDER = os.path.dirname(os.path.abspath(__file__))
ASET = os.path.join(FOLDER, "aset")

with open(os.path.join(FOLDER, "merek.json"), encoding="utf-8") as f:
    MEREK = json.load(f)


def warna(nama, alpha=255):
    h = MEREK[nama].lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


FONT = {
    "judul": "InterDisplay-Black.otf",
    "judul2": "InterDisplay-ExtraBold.otf",
    "tebal": "Inter-Bold.otf",
    "semi": "Inter-SemiBold.otf",
    "sedang": "Inter-Medium.otf",
}


def font(jenis, ukuran):
    return ImageFont.truetype(os.path.join(ASET, "font", FONT[jenis]), int(ukuran))


def logo(bagian, varian="putih", lebar=None, tinggi=None):
    """bagian: 'logo-mark' atau 'wordmark'. varian: 'putih' atau 'gelap'."""
    im = Image.open(os.path.join(ASET, f"{bagian}-{varian}.png")).convert("RGBA")
    if lebar:
        im = im.resize((int(lebar), round(im.height * lebar / im.width)), Image.LANCZOS)
    elif tinggi:
        im = im.resize((round(im.width * tinggi / im.height), int(tinggi)), Image.LANCZOS)
    return im


def isi_penuh(foto, w, h, fokus=(0.5, 0.5)):
    """Potong + skala foto supaya memenuhi w x h (seperti 'cover' di CSS)."""
    im = Image.open(foto).convert("RGB") if isinstance(foto, str) else foto.convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = round((im.width - w) * fokus[0])
    y = round((im.height - h) * fokus[1])
    return im.crop((x, y, x + w, y + h))


def gradasi(w, h, atas=0, bawah=255, rgb=(0, 0, 0)):
    """Lapisan gradasi vertikal (alpha atas -> alpha bawah)."""
    g = Image.new("L", (1, h))
    for y in range(h):
        g.putpixel((0, y), round(atas + (bawah - atas) * (y / max(h - 1, 1))))
    g = g.resize((w, h))
    lap = Image.new("RGBA", (w, h), rgb + (0,))
    lap.putalpha(g)
    return lap


def teks_spasi(draw, xy, teks, fnt, isi, spasi=0.0):
    """Gambar teks dengan jarak huruf (tracking) dalam satuan em."""
    x, y = xy
    tambah = fnt.size * spasi
    for ch in teks:
        draw.text((x, y), ch, font=fnt, fill=isi)
        x += draw.textlength(ch, font=fnt) + tambah
    return x


def lebar_spasi(teks, fnt, spasi=0.0):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    return sum(d.textlength(ch, font=fnt) for ch in teks) + fnt.size * spasi * max(len(teks) - 1, 0)


def baris_judul(teks, ukuran, isi, rapat=0.9, jenis="judul", spasi=-0.01):
    """Render satu baris judul sebagai gambar RGBA, dipadatkan horizontal (rapat<1)."""
    fnt = font(jenis, ukuran)
    lb = lebar_spasi(teks, fnt, spasi)
    asc, desc = fnt.getmetrics()
    im = Image.new("RGBA", (int(lb) + 8, asc + desc), (0, 0, 0, 0))
    teks_spasi(ImageDraw.Draw(im), (2, 0), teks, fnt, isi, spasi)
    if rapat != 1:
        im = im.resize((max(1, round(im.width * rapat)), im.height), Image.LANCZOS)
    # pangkas ruang kosong atas/bawah agar jarak baris bisa diatur pasti
    kotak = im.getbbox()
    if kotak:
        im = im.crop((0, fnt.getbbox("H")[1], im.width, asc + desc))
    return im


def pecah_baris(teks):
    """'Baris 1 | *Baris merah*' -> [(teks, merah?)]. Tanda * = warna merah."""
    hasil = []
    for b in teks.split("|"):
        b = b.strip()
        merah = b.startswith("*") and b.endswith("*") and len(b) > 1
        hasil.append((b.strip("*").strip(), merah))
    return hasil


def balut(teks, fnt, lebar_maks):
    """Pecah kalimat biasa menjadi beberapa baris sesuai lebar."""
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    baris, kini = [], ""
    for kata in teks.split():
        coba = (kini + " " + kata).strip()
        if d.textlength(coba, font=fnt) <= lebar_maks or not kini:
            kini = coba
        else:
            baris.append(kini)
            kini = kata
    if kini:
        baris.append(kini)
    return baris
