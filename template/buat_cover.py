#!/usr/bin/env python3
"""Template carousel OMAKARYO (1080 x 1350) untuk organisasi siswa & mahasiswa.

Semua teks disusun bertumpuk dari atas ke bawah dan diukur dulu, jadi tidak
pernah saling menimpa. Teks selalu berada di atas panel gelap/merah yang
polos, bukan langsung di atas foto, supaya tetap terbaca di foto apa pun.
Kalau isinya terlalu panjang, ukuran judul dikecilkan otomatis.

Tata letak:
  foto     : foto di atas + stiker miring, panel judul + tag organisasi di bawah
  kolase   : judul + 2-3 foto berlabel + tag organisasi
  isi      : slide isi (slide 2 dst.): foto, nomor besar, judul, penjelasan
  penutup  : slide ajakan: judul, nomor WhatsApp, kata kunci

Penulisan judul: pisahkan baris dengan "|", beri bintang untuk baris merah.
  "Kaos angkatan | *yang kompak.*"

Contoh:
  python3 template/buat_cover.py foto --foto topi.jpg --stiker "Merch BEM" \
      --judul "Satu angkatan, | *satu identitas.*" --sub "Kaos, jaket, topi custom." \
      --tag OSIS BEM HIMA UKM -o hasil/1.jpg
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageEnhance

import omakaryo as om

W, H = 1080, 1350
TEPI = 64
KAKI = 96            # tinggi area kaki (logo + WA) di bawah
TAG_BAWAAN = ["OSIS", "BEM", "HIMA", "UKM", "ANGKATAN"]


# ------------------------------------------------------------ blok dasar

def judul_blok(teks, lebar_maks, ukuran, jarak=0.98, rapat=0.9):
    baris = om.pecah_baris(teks.upper())
    while True:
        gambar = [om.baris_judul(t, ukuran, om.warna("merah") if m else om.warna("putih"), rapat)
                  for t, m in baris]
        if max(g.width for g in gambar) <= lebar_maks or ukuran <= 40:
            break
        ukuran -= 4
    langkah = round(ukuran * jarak)
    tinggi = langkah * (len(gambar) - 1) + gambar[-1].height
    blok = Image.new("RGBA", (max(g.width for g in gambar), tinggi), (0, 0, 0, 0))
    for i, g in enumerate(gambar):
        blok.alpha_composite(g, (0, i * langkah))
    return blok


def paragraf(teks, lebar, ukuran=30, isi=None, jenis="sedang", jarak=1.38):
    f = om.font(jenis, ukuran)
    baris = om.balut(teks, f, lebar)
    langkah = round(ukuran * jarak)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (lebar, langkah * (len(baris) - 1) + asc + desc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, b in enumerate(baris):
        d.text((0, i * langkah), b, font=f, fill=isi or om.warna("putih", 225))
    return im


def kicker(teks, isi=None):
    """— LABEL KECIL dengan garis merah di depannya."""
    f = om.font("tebal", 18)
    t = teks.upper()
    lb = om.lebar_spasi(t, f, 0.2)
    im = Image.new("RGBA", (int(lb) + 50, 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 11, 26, 15), fill=om.warna("merah"))
    om.teks_spasi(d, (40, 1), t, f, isi or om.warna("putih"), 0.2)
    return im


def deret_tag(tag, lebar_maks):
    """Deretan pil: OSIS · BEM · HIMA ... (pertama merah, sisanya garis)."""
    f = om.font("tebal", 20)
    pil = []
    for i, t in enumerate(tag):
        t = t.upper()
        lb = int(om.lebar_spasi(t, f, 0.1)) + 36
        im = Image.new("RGBA", (lb, 44), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if i == 0:
            d.rounded_rectangle((0, 0, lb - 1, 43), 22, fill=om.warna("merah"))
        else:
            d.rounded_rectangle((1, 1, lb - 2, 42), 21, outline=om.warna("putih", 200), width=2)
        om.teks_spasi(d, (18, 9), t, f, om.warna("putih"), 0.1)
        pil.append(im)
    # pecah ke beberapa baris bila tidak muat
    baris, kini, x = [], [], 0
    for p in pil:
        if kini and x + p.width > lebar_maks:
            baris.append(kini)
            kini, x = [], 0
        kini.append(p)
        x += p.width + 10
    if kini:
        baris.append(kini)
    im = Image.new("RGBA", (lebar_maks, len(baris) * 54 - 10), (0, 0, 0, 0))
    for r, b in enumerate(baris):
        x = 0
        for p in b:
            im.alpha_composite(p, (x, r * 54))
            x += p.width + 10
    return im


def stiker(teks, sudut=-5):
    """Stiker merah miring, gaya tempelan."""
    f = om.font("judul", 40)
    t = teks.upper()
    lb = int(om.lebar_spasi(t, f, 0.0)) + 56
    im = Image.new("RGBA", (lb, 74), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, lb - 1, 73), 10, fill=om.warna("merah"))
    d.text((28, 10), t, font=f, fill=om.warna("putih"))
    bayang = Image.new("RGBA", (lb + 12, 86), (0, 0, 0, 0))
    ImageDraw.Draw(bayang).rounded_rectangle((8, 10, lb + 7, 83), 10, fill=(0, 0, 0, 120))
    bayang.alpha_composite(im, (0, 0))
    return bayang.rotate(-sudut * -1, resample=Image.BICUBIC, expand=True)


def susun(kanvas, blok, x, y, y_maks):
    """Tumpuk blok (gambar, jarak_sesudah) dari y ke bawah. Kembalikan False kalau lewat y_maks."""
    total = sum(b.height + j for b, j in blok if b is not None)
    if y + total > y_maks:
        return False
    for b, j in blok:
        if b is None:
            continue
        kanvas.alpha_composite(b, (x, y))
        y += b.height + j
    return True


def coba_susun(buat, ukuran_awal, ukuran_min=48):
    """Panggil buat(ukuran) dengan ukuran judul yang makin kecil sampai semua muat."""
    u = ukuran_awal
    while u >= ukuran_min:
        hasil = buat(u)
        if hasil is not None:
            return hasil
        u -= 6
    raise SystemExit("Teks terlalu panjang untuk satu slide. Persingkat judul atau --sub.")


# ------------------------------------------------------------ bagian tetap

def kepala(kanvas, nomor=None, gelap_belakang=True):
    if gelap_belakang:
        kanvas.alpha_composite(om.gradasi(W, 170, 170, 0), (0, 0))
    mark = om.logo("logo-mark", tinggi=44)
    kanvas.alpha_composite(mark, (TEPI, 50))
    wm = om.logo("wordmark", tinggi=16)
    kanvas.alpha_composite(wm, (TEPI + mark.width + 16, 50 + 15))
    if nomor:
        d = ImageDraw.Draw(kanvas)
        f = om.font("tebal", 20)
        lb = om.lebar_spasi(nomor, f, 0.12)
        d.rounded_rectangle((W - TEPI - lb - 32, 50, W - TEPI, 94), 22, fill=(0, 0, 0, 150))
        om.teks_spasi(d, (W - TEPI - lb - 16, 60), nomor, f, om.warna("putih"), 0.12)


def kaki(kanvas):
    """Garis tipis + OMAKARYO kiri, WhatsApp kanan. Selalu di 96px terbawah."""
    d = ImageDraw.Draw(kanvas)
    y = H - KAKI
    d.line((TEPI, y, W - TEPI, y), fill=om.warna("putih", 50), width=1)
    wm = om.logo("wordmark", tinggi=17)
    kanvas.alpha_composite(wm, (TEPI, y + 40))
    f = om.font("tebal", 22)
    t = "WA " + om.MEREK["whatsapp"]
    lb = d.textlength(t, font=f)
    d.text((W - TEPI - lb, y + 34), t, font=f, fill=om.warna("putih"))


def foto_area(kanvas, foto, tinggi, fokus=0.5, ke_warna="gelap"):
    kanvas.paste(om.isi_penuh(foto, W, tinggi, (0.5, fokus)), (0, 0))
    kanvas.alpha_composite(om.gradasi(W, 220, 0, 255, om.warna(ke_warna)[:3]), (0, tinggi - 220))


# ------------------------------------------------------------ tata letak

def cover_foto(a):
    tinggi_foto = 760

    def buat(u):
        k = Image.new("RGBA", (W, H), om.warna("gelap"))
        foto_area(k, a.foto[0], tinggi_foto, a.fokus)
        kepala(k, a.nomor)
        lebar = W - 2 * TEPI
        blok = [(judul_blok(a.judul, lebar, u), 22)]
        if a.sub:
            blok.append((paragraf(a.sub, lebar, 30), 28))
        blok.append((deret_tag(a.tag, lebar), 0))
        total = sum(b.height + j for b, j in blok)
        y_maks = H - KAKI - 40
        y = y_maks - total                       # rata bawah, naik seperlunya
        if y < tinggi_foto - 190:                # jangan naik terlalu jauh ke foto
            return None
        if a.stiker:
            s = stiker(a.stiker)
            k.alpha_composite(s, (TEPI - 6, max(130, y - s.height - 26)))
        susun(k, blok, TEPI, y, y_maks)
        kaki(k)
        return k
    return coba_susun(buat, a.ukuran or 116)


def cover_kolase(a):
    def buat(u):
        k = Image.new("RGBA", (W, H), om.warna("gelap"))
        kepala(k, a.nomor, gelap_belakang=False)
        lebar = W - 2 * TEPI
        y = 140
        atas = []
        if a.atas:
            atas.append((kicker(a.atas), 18))
        atas.append((judul_blok(a.judul, lebar, u), 34))
        h_atas = sum(b.height + j for b, j in atas)
        bawah = []
        if a.sub:
            bawah.append((paragraf(a.sub, lebar, 28), 22))
        bawah.append((deret_tag(a.tag, lebar), 0))
        h_bawah = sum(b.height + j for b, j in bawah) + 32
        tg = H - KAKI - 40 - y - h_atas - h_bawah
        if tg < 380:
            return None
        susun(k, atas, TEPI, y, H)
        y0 = y + h_atas
        n = len(a.foto)
        celah = 12
        lb = (lebar - celah * (n - 1)) // n
        d = ImageDraw.Draw(k)
        f = om.font("tebal", 20)
        for i, foto in enumerate(a.foto):
            x = TEPI + i * (lb + celah)
            ptg = om.isi_penuh(foto, lb, tg, (0.5, a.fokus)).convert("RGBA")
            topeng = Image.new("L", (lb, tg), 0)
            ImageDraw.Draw(topeng).rounded_rectangle((0, 0, lb - 1, tg - 1), 18, fill=255)
            k.paste(ptg, (x, y0), topeng)
            label = (a.label[i] if a.label and i < len(a.label) else "").upper()
            if label:
                tl = om.lebar_spasi(label, f, 0.08)
                d.rounded_rectangle((x + 12, y0 + tg - 54, x + 12 + tl + 28, y0 + tg - 14), 20,
                                    fill=om.warna("merah"))
                om.teks_spasi(d, (x + 26, y0 + tg - 45), label, f, om.warna("putih"), 0.08)
        susun(k, bawah, TEPI, y0 + tg + 32, H - KAKI)
        kaki(k)
        return k
    return coba_susun(buat, a.ukuran or 100)


def cover_isi(a):
    tinggi_foto = 640

    def buat(u):
        k = Image.new("RGBA", (W, H), om.warna("gelap"))
        if a.foto:
            foto_area(k, a.foto[0], tinggi_foto, a.fokus)
        kepala(k, a.nomor)
        lebar = W - 2 * TEPI
        blok = []
        if a.atas:
            blok.append((kicker(a.atas), 20))
        blok.append((judul_blok(a.judul, lebar, u), 26))
        if a.sub:
            blok.append((paragraf(a.sub, lebar, 30), 0))
        total = sum(b.height + j for b, j in blok)
        y_maks = H - KAKI - 44
        y = y_maks - total
        if y < tinggi_foto - 120:
            return None
        susun(k, blok, TEPI, y, y_maks)
        kaki(k)
        return k
    return coba_susun(buat, a.ukuran or 92)


def cover_penutup(a):
    def buat(u):
        if a.foto:
            latar = ImageEnhance.Brightness(om.isi_penuh(a.foto[0], W, H, (0.5, a.fokus))).enhance(0.3)
            k = latar.convert("RGBA")
            k.alpha_composite(Image.new("RGBA", (W, H), om.warna("gelap", 150)))
        else:
            k = Image.new("RGBA", (W, H), om.warna("gelap"))
        kepala(k, a.nomor, gelap_belakang=False)
        lebar = W - 2 * TEPI
        blok = []
        if a.atas:
            blok.append((kicker(a.atas), 20))
        blok.append((judul_blok(a.judul, lebar, u), 26))
        if a.sub:
            blok.append((paragraf(a.sub, lebar, 30), 36))
        # kartu WhatsApp
        kartu = Image.new("RGBA", (lebar, 230 if a.kunci else 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(kartu)
        d.rounded_rectangle((0, 0, lebar - 1, 149), 22, fill=om.warna("putih"))
        om.teks_spasi(d, (32, 24), "CHAT ADMIN VIA WHATSAPP", om.font("tebal", 17), om.warna("gelap"), 0.18)
        nomor = om.baris_judul(om.MEREK["whatsapp"], 70, om.warna("gelap"), 0.92, jenis="judul2")
        kartu.alpha_composite(nomor, (30, 60))
        cx, cy, r = lebar - 75, 75, 38
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=om.warna("merah"))
        d.line((cx - 15, cy, cx + 13, cy), fill=om.warna("putih"), width=6)
        d.line((cx + 1, cy - 13, cx + 14, cy), fill=om.warna("putih"), width=6)
        d.line((cx + 1, cy + 13, cx + 14, cy), fill=om.warna("putih"), width=6)
        if a.kunci:
            f = om.font("tebal", 26)
            t = "Ketik kata kunci:"
            d.text((4, 178), t, font=f, fill=om.warna("putih", 220))
            x = 4 + d.textlength(t, font=f) + 16
            kk = a.kunci.upper()
            fk = om.font("judul", 34)
            lk = d.textlength(kk, font=fk)
            d.rounded_rectangle((x, 166, x + lk + 40, 226), 30, fill=om.warna("merah"))
            d.text((x + 20, 173), kk, font=fk, fill=om.warna("putih"))
        blok.append((kartu, 0))
        total = sum(b.height + j for b, j in blok)
        y_maks = H - KAKI - 50
        ruang = y_maks - 150
        if total > ruang:
            return None
        susun(k, blok, TEPI, 150 + (ruang - total) // 2, y_maks)
        kaki(k)
        return k
    return coba_susun(buat, a.ukuran or 100)


def main():
    p = argparse.ArgumentParser(description="Buat slide carousel OMAKARYO 1080x1350.")
    p.add_argument("tata", choices=["foto", "kolase", "isi", "penutup"])
    p.add_argument("--foto", nargs="*", default=[], help="foto (kolase: 2-3 foto)")
    p.add_argument("--judul", required=True, help='pisah baris dengan |, baris merah pakai *...*')
    p.add_argument("--sub", help="kalimat pendek di bawah judul")
    p.add_argument("--label", nargs="*", help="label tiap foto kolase")
    p.add_argument("--tag", nargs="*", default=TAG_BAWAAN, help="tag organisasi (foto/kolase)")
    p.add_argument("--stiker", help='stiker merah miring di atas judul, mis. "Kaos angkatan"')
    p.add_argument("--nomor", help='nomor slide kanan atas, mis. "01/06"')
    p.add_argument("--atas", help='label kecil di atas judul, mis. "Tips 01"')
    p.add_argument("--kunci", help="kata kunci (penutup)")
    p.add_argument("--ukuran", type=int, help="ukuran awal judul (otomatis mengecil kalau tidak muat)")
    p.add_argument("--fokus", type=float, default=0.5, help="posisi potong foto 0=atas 1=bawah")
    p.add_argument("-o", "--keluar", default="cover.jpg")
    a = p.parse_args()
    if a.tata in ("foto", "kolase") and not a.foto:
        p.error("--foto wajib untuk tata letak ini")
    hasil = {"foto": cover_foto, "kolase": cover_kolase, "isi": cover_isi,
             "penutup": cover_penutup}[a.tata](a)
    os.makedirs(os.path.dirname(os.path.abspath(a.keluar)), exist_ok=True)
    hasil.convert("RGB").save(a.keluar, quality=93)
    print("Tersimpan:", a.keluar)


if __name__ == "__main__":
    main()
