# 🐀 The Endless Greed: Retro FPS (Pygame)

Sebuah game *First-Person Shooter* (FPS) bergaya retro 2.5D yang dibangun secara murni menggunakan **Python** dan **Pygame**. Game ini menggunakan teknik **Raycasting** klasik (seperti DOOM 1993 atau Wolfenstein 3D) dengan sentuhan grafis *pixel art* kotor dan mekanik *survival endless wave*.

Game ini awalnya dibuat sebagai bahan eksperimen untuk konten video *reverse coding*.

## ✨ Fitur Utama
* **Mesin Raycasting Kustom:** Render 3D dari peta 2D yang dibangun dari nol tanpa menggunakan *game engine* berat.
* **Micro-Surface Pixelation:** Render layar menggunakan skala rendah yang diperbesar secara paksa untuk menciptakan atmosfer horor *pixelated* era DOS/PS1.
* **Spatial Audio System:** Suara mengerikan monster akan terdengar semakin kencang saat mereka merayap mendekat di dalam kegelapan.
* **AI & Musuh Dinamis:**
  * **Tikus Koruptor (Minion):** Tikus berjas dan berdasi yang terus bermunculan.
  * **The Rat King (Boss):** Gumpalan mutasi daging mengerikan yang akan *spawn* secara eksklusif setiap kali 10 Tikus Koruptor dibasmi.
* **Dynamic Emoji HUD:** Antarmuka layar bawah (HUD) menampilkan status peluru, nyawa, dan wajah karakter (*emoji*) yang bereaksi secara *real-time* saat menerima *damage* atau tumbang.
* **Manajemen Sumber Daya:** Sistem peluru dengan magasin (kapasitas 12), mekanik *reload*, dan sistem barang jatuh (*drop rate*) yang sangat ketat untuk Ammo, Armor, dan Medkit.

## 🎮 Kontrol Game
* **W, A, S, D** - Bergerak (Maju, Kiri, Mundur, Kanan)
* **Mouse** - Menoleh / Mengarahkan Kamera
* **Klik Kiri Mouse** - Menembak
* **R** - *Reload* Senjata
* **ESC** - Keluar dari game

## 🛠️ Cara Instalasi & Bermain
1. Pastikan kamu sudah menginstal [Python](https://www.python.org/downloads/) di komputermu.
2. *Clone* repositori ini ke komputer kamu:
```bash
   git clone [https://github.com/USERNAME_KAMU/NAMA_REPO_KAMU.git](https://github.com/USERNAME_KAMU/NAMA_REPO_KAMU.git)
