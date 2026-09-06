# Ikut mengerjakan

## Menyiapkan

```
uv sync
uv run python -m unittest discover -s tests
```

Tanpa uv, `pip install -e ".[dev]"` juga bisa.

## Data pihak ketiga

Tidak ikut di repositori karena ukurannya. Ambil dengan:

```
uv run python scripts/unduh_data.py
```

Tarif INA-CBG yang sudah diekstrak tetap ikut di `data/processed`, supaya
model bisa dijalankan tanpa mengunduh apa pun.

## Aturan yang tidak bisa ditawar

**Setiap angka yang masuk dokumen harus berasal dari berkas hasil di `runs`.**
Tidak ada angka yang ditulis tangan. Kalau sebuah angka tidak bisa ditunjuk
asalnya, angka itu dibuang.

**Kegagalan ikut ditulis.** `TEMUAN.md` memuat percobaan yang gagal beserta
sebabnya. Menghapus kegagalan dari catatan sama saja membohongi pembaca
berikutnya, termasuk diri sendiri enam bulan lagi.

**Dugaan diukur, bukan ditebak berulang.** Sepanjang pengerjaan ini ada
sembilan dugaan sebab dan delapan di antaranya salah. Tidak satu pun
diselesaikan oleh dugaan berikutnya.

## Cabang

`dev` adalah cabang utama tempat pekerjaan masuk. `main` hanya untuk yang
sudah diterapkan.
