#!/usr/bin/env python3
"""Template bingkai Reel OMAKARYO (720 x 1280).

Isi bingkai: label merah kiri atas, logo kanan atas, gradasi gelap di bawah,
teks dalam kotak putih/merah (disusun dari bawah, tidak bertumpuk), baris ajakan WhatsApp opsional, wordmark di bawah.

1) Bingkai PNG transparan (untuk ditaruh di atas video di CapCut/Canva/InShot):
   python3 template/bingkai_reel.py png --label "Proses sablon" \
       --teks "Sablon itu dibuat | *kayak gimana sih?*" -o hasil/bingkai.png
   (tanpa --label/--teks = bingkai kosong: logo + gradasi saja)

2) Langsung tempel ke video, teks berganti per adegan (butuh ffmpeg):
   python3 template/bingkai_reel.py video --masuk mentah.mp4 --label "Proses sablon" \
       --adegan "0-3 = Sablon itu dibuat | *kayak gimana sih?*" \
       --adegan "3-6 = Tinta ditarik pakai rakel | *lewat screen.*" \
       --adegan "9-12 = Punya desain sendiri? | *Mockup gratis.* | wa" \
       -o hasil/reel.mp4
   Tambahkan "| wa" di akhir adegan untuk memunculkan baris CHAT ADMIN + nomor WhatsApp.
   Video masuk akan diskalakan & dipotong ke 720x1280 otomatis.
"""
import argparse
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw

import omakaryo as om

W, H = 720, 1280
TEPI = 40
Y_ATAS = 210        # garis tengah label & logo atas (di bawah area nama akun IG)
Y_WORDMARK = 1064   # di atas area tombol/caption Instagram


def dasar(label=None):
    """Lapisan tetap: gradasi, logo kanan atas, wordmark bawah, label kiri atas."""
    k = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    k.alpha_composite(om.gradasi(W, 300, 110, 0), (0, 0))
    k.alpha_composite(om.gradasi(W, 820, 0, 245), (0, H - 820))
    k.alpha_composite(om.gradasi(W, 420, 0, 90), (0, H - 420))
    mark = om.logo("logo-mark", tinggi=30)
    k.alpha_composite(mark, (W - TEPI - mark.width, Y_ATAS - 15))
    wm = om.logo("wordmark", lebar=160)
    k.alpha_composite(wm, ((W - wm.width) // 2, Y_WORDMARK))
    if label:
        d = ImageDraw.Draw(k)
        f = om.font("tebal", 16)
        t = label.upper()
        lb = om.lebar_spasi(t, f, 0.06)
        d.rectangle((TEPI, Y_ATAS - 17, TEPI + lb + 24, Y_ATAS + 17), fill=om.warna("merah"))
        om.teks_spasi(d, (TEPI + 12, Y_ATAS - 10), t, f, om.warna("putih"), 0.06)
    return k


def kotak_baris(t, merah, ukuran):
    """Satu baris teks di dalam kotak: putih (teks gelap) atau merah (teks putih)."""
    f = om.font("judul2", ukuran)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    lb = int(d.textlength(t, font=f))
    px, py = 16, 10
    tinggi_huruf = f.getbbox("ÁHgy")
    th = tinggi_huruf[3] - f.getbbox("H")[1]
    im = Image.new("RGBA", (lb + 2 * px, th + 2 * py), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    isi = om.warna("merah") if merah else om.warna("putih")
    dd.rounded_rectangle((0, 0, im.width - 1, im.height - 1), 8, fill=isi)
    dd.text((px, py - f.getbbox("H")[1]), t, font=f,
            fill=om.warna("putih") if merah else om.warna("gelap"))
    return im


def kartu_wa():
    lebar = W - 2 * TEPI
    im = Image.new("RGBA", (lebar, 76), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, lebar - 1, 75), 38, fill=(0, 0, 0, 170), outline=om.warna("putih", 90), width=2)
    om.teks_spasi(d, (30, 13), "CHAT ADMIN VIA WHATSAPP", om.font("tebal", 12), om.warna("putih", 190), 0.18)
    d.text((30, 31), om.MEREK["whatsapp"], font=om.font("tebal", 28), fill=om.warna("putih"))
    cx, cy, r = lebar - 40, 38, 25
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=om.warna("merah"))
    d.line((cx - 10, cy, cx + 9, cy), fill=om.warna("putih"), width=4)
    d.line((cx + 1, cy - 9, cx + 10, cy), fill=om.warna("putih"), width=4)
    d.line((cx + 1, cy + 9, cx + 10, cy), fill=om.warna("putih"), width=4)
    return im


def teks(isi):
    """Lapisan teks adegan. isi: 'baris putih | *baris merah* | wa'.
    Disusun dari bawah ke atas (di atas wordmark), jadi tidak pernah bertumpuk."""
    k = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not isi:
        return k
    bagian = [b.strip() for b in isi.split("|")]
    wa = bool(bagian) and bagian[-1].lower() == "wa"
    if wa:
        bagian = bagian[:-1]
    lebar = W - 2 * TEPI - 32
    ukuran = 46
    while True:
        f = om.font("judul2", ukuran)
        baris = []
        for t, merah in om.pecah_baris("|".join(bagian)):
            baris += [(x, merah) for x in om.balut(t, f, lebar)]
        if len(baris) <= 4 or ukuran <= 32:
            break
        ukuran -= 2
    kotak = [kotak_baris(t, m, ukuran) for t, m in baris]
    y = Y_WORDMARK - 34
    if wa:
        kw = kartu_wa()
        y -= kw.height
        k.alpha_composite(kw, (TEPI, y))
        y -= 26
    y -= sum(b.height for b in kotak) + 6 * (len(kotak) - 1)
    for b in kotak:
        k.alpha_composite(b, (TEPI, y))
        y += b.height + 6
    return k


def buat_png(a):
    k = dasar(a.label)
    k.alpha_composite(teks(a.teks))
    os.makedirs(os.path.dirname(os.path.abspath(a.keluar)), exist_ok=True)
    k.save(a.keluar)
    print("Tersimpan:", a.keluar)


def buat_video(a):
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg belum terpasang.")
    adegan = []
    for s in a.adegan or []:
        waktu, _, isi = s.partition("=")
        t0, _, t1 = waktu.strip().partition("-")
        adegan.append((float(t0), float(t1), isi.strip()))
    with tempfile.TemporaryDirectory() as tmp:
        jalur_dasar = os.path.join(tmp, "dasar.png")
        dasar(a.label).save(jalur_dasar)
        masukan = ["-i", a.masuk, "-loop", "1", "-i", jalur_dasar]
        saring = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[v0]",
                  "[v0][1:v]overlay=0:0:shortest=1[v1]"]
        akhir = "v1"
        for i, (t0, t1, isi) in enumerate(adegan):
            p = os.path.join(tmp, f"teks{i}.png")
            teks(isi).save(p)
            masukan += ["-loop", "1", "-i", p]
            n = i + 2
            # teks muncul dengan fade singkat
            saring.append(f"[{n}:v]format=rgba,fade=t=in:st={t0}:d=0.25:alpha=1,"
                          f"fade=t=out:st={max(t1 - 0.25, t0)}:d=0.25:alpha=1[t{i}]")
            saring.append(f"[{akhir}][t{i}]overlay=0:0:shortest=1:enable='between(t,{t0},{t1})'[v{n}]")
            akhir = f"v{n}"
        os.makedirs(os.path.dirname(os.path.abspath(a.keluar)), exist_ok=True)
        cmd = ["ffmpeg", "-y", "-v", "error", *masukan, "-filter_complex", ";".join(saring),
               "-map", f"[{akhir}]", "-map", "0:a?", "-c:v", "libx264", "-preset", "medium",
               "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac",
               "-movflags", "+faststart", a.keluar]
        subprocess.run(cmd, check=True)
    print("Tersimpan:", a.keluar)


def main():
    p = argparse.ArgumentParser(description="Bingkai Reel OMAKARYO 720x1280.")
    sub = p.add_subparsers(dest="mode", required=True)
    pp = sub.add_parser("png", help="bingkai PNG transparan")
    pp.add_argument("--label", help="label merah kiri atas, mis. 'Proses sablon'")
    pp.add_argument("--teks", help="'baris putih | *baris merah*' (+ '| wa' untuk baris WhatsApp)")
    pp.add_argument("-o", "--keluar", default="bingkai-reel.png")
    pv = sub.add_parser("video", help="tempel bingkai ke video")
    pv.add_argument("--masuk", required=True, help="video mentah")
    pv.add_argument("--label")
    pv.add_argument("--adegan", action="append", help="'mulai-selesai = teks', detik. Boleh berulang.")
    pv.add_argument("-o", "--keluar", default="reel.mp4")
    a = p.parse_args()
    buat_png(a) if a.mode == "png" else buat_video(a)


if __name__ == "__main__":
    main()
