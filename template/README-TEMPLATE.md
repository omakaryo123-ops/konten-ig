# Template desain OMAKARYO

Template yang bisa dipakai ulang tiap minggu, dibuat dari gaya konten Minggu 3
(gelap `#111111`, merah `#E62129`, huruf Inter tebal, logo transparan) dan
diarahkan ke organisasi siswa & mahasiswa: OSIS, BEM, HIMA, UKM, kepanitiaan,
kaos kelas dan angkatan.

**Teks tidak akan tumpang tindih.** Semua teks disusun bertumpuk dan diukur dulu,
selalu di atas panel polos atau kotak warna (bukan langsung di atas foto). Kalau
isi terlalu panjang, judul mengecil otomatis; kalau tetap tidak muat, skrip
berhenti dan minta teks dipersingkat.

## Isi folder

| File | Gunanya |
|---|---|
| `buat_cover.py` | Bikin slide carousel 1080x1350: `foto`, `kolase`, `isi`, `penutup` |
| `bingkai_reel.py` | Bikin bingkai Reel 720x1280: PNG transparan, atau langsung ditempel ke video |
| `bingkai-reel-kosong.png` | Bingkai Reel siap pakai (logo + gradasi) untuk CapCut/Canva/InShot |
| `merek.json` | Warna, tagline, nomor WhatsApp. Ubah di sini, semua template ikut berubah |
| `aset/` | Logo yang sudah dipotong (ikon & tulisan) + font Inter (lisensi OFL) |

Butuh Python 3 + Pillow (`pip install pillow`). Mode video butuh `ffmpeg`.

## Cara menulis judul

Pisahkan baris dengan `|`. Beri bintang untuk baris merah:
`"Sablon, heat press, | *atau bordir?*"`. Judul otomatis huruf kapital dan
mengecil sendiri kalau terlalu panjang.

## Carousel

```bash
# Cover foto: foto di atas, stiker miring, judul + tag organisasi di bawah
python3 template/buat_cover.py foto --foto topi.jpg --stiker "Merch organisasi" \
  --judul "Satu angkatan, | *satu identitas.*" \
  --sub "Kaos, jaket, topi, dan PDH custom untuk organisasimu." -o hasil/1.jpg

# Cover kolase 2-3 foto berlabel
python3 template/buat_cover.py kolase --foto a.jpg b.jpg c.jpg --label Sablon "Heat press" Bordir \
  --atas "Buat kaos kelas & angkatan" --judul "Sablon, heat press, | *atau bordir?*" \
  --sub "Ini bedanya, biar tidak salah pilih." --nomor "01/06" -o hasil/1.jpg

# Slide isi (slide 2 dst.)
python3 template/buat_cover.py isi --foto bordir.jpg --atas "Tips 03 · Bordir" --nomor "04/06" \
  --judul "Logo organisasi | *dijahit rapi.*" --sub "Cocok untuk PDH dan jaket himpunan." -o hasil/4.jpg

# Slide penutup / ajakan
python3 template/buat_cover.py penutup --foto latar.jpg --nomor "06/06" --atas "Pesan untuk organisasimu" \
  --judul "Siap bikin merch | *angkatanmu?*" --sub "Kirim logo, kami buatkan mockup gratis." \
  --kunci Angkatan -o hasil/6.jpg
```

Opsi lain:
- `--tag BEM HIMA Kepanitiaan` mengganti deretan tag (bawaan: OSIS BEM HIMA UKM ANGKATAN). Tag pertama berwarna merah.
- `--stiker "PDH & jaket himpunan"` stiker merah miring di atas judul (tata `foto`).
- `--fokus 0.3` menggeser potongan foto (0 = atas, 1 = bawah). `--ukuran 130` ukuran awal judul.

## Bingkai Reel

```bash
# PNG transparan, taruh di atas video di aplikasi edit
python3 template/bingkai_reel.py png --label "Proses sablon" \
  --teks "Sablon itu dibuat | *kayak gimana sih?*" -o hasil/bingkai.png

# Langsung jadi video, teks berganti per adegan (detik mulai-selesai)
python3 template/bingkai_reel.py video --masuk mentah.mp4 --label "Topi panitia" \
  --adegan "0-4 = Bordir di topi, | *begini hasilnya.*" \
  --adegan "4-8 = Logo tampil jelas | *dan rapi.*" \
  --adegan "8-11 = Mau topi seperti ini? | *Mockup gratis.* | wa" -o hasil/reel.mp4
```

Tiap baris teks Reel ada di kotak sendiri (putih = baris biasa, merah = baris
bertanda `*`), disusun dari bawah ke atas di atas tulisan OMAKARYO, jadi tidak
pernah menimpa logo atau kartu WhatsApp. Baris panjang dipecah otomatis.
`| wa` di akhir adegan memunculkan kartu CHAT ADMIN + nomor WhatsApp.
Pakai video **mentah tanpa teks**; video Minggu 3 di repo sudah bertulisan.

Posisi teks sengaja dijaga di luar area yang tertutup tampilan Instagram
(nama akun di atas, tombol & caption di kanan/bawah).
