# Peladen penilaian NALAR.
#
# Modelnya dilatih sekali saat wadah menyala, memakai data buatan yang
# dibangkitkan di tempat. Tidak ada satu pun klaim peserta JKN yang sungguhan
# masuk ke sini, dan memang tidak boleh.
#
# Wadah ini untuk penerapan di dalam, bukan untuk peragaan. Rancangan menyebut
# satu syarat yang tidak bisa ditawar: penilaian dijalankan di tempat data
# berada, dan tidak ada klaim yang dikirim keluar untuk diskor. Itu berarti
# gambar ini dipasang di pusat data yang sudah ada, bukan di layanan awan
# pihak ketiga.
#
#   docker build -t nalar-api .
#   docker run -p 8000:7860 nalar-api
FROM python:3.12-slim

# Pengguna tanpa hak istimewa. Hugging Face menjalankan wadah sebagai uid 1000.
# uid 1000 dipakai karena itu yang lazim dipetakan pada pemasangan berwadah.
RUN useradd -m -u 1000 nalar
USER nalar
ENV PATH="/home/nalar/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HOME=/home/nalar

WORKDIR /home/nalar/app

# Dipasang langsung dari repositori, supaya wadah ini tidak menyimpan salinan
# kedua dari kodenya. Yang berlaku selalu yang ada di cabang dev.
ARG REVISI=dev
RUN pip install --no-cache-dir --user \
    "nalar[api] @ git+https://github.com/NalarAI/nalar-core.git@${REVISI}"

# Bukti bahwa tabel tarif resmi ikut terbawa. Kalau tidak, seluruh alur diam
# diam jatuh ke tarif tebakan, dan itu menaikkan ketimpangan antar kelas
# faskes dari 1,737 ke 3,539 tanpa satu pun pesan galat. Wadah lebih baik
# gagal dibangun daripada berjalan dengan model yang salah.
RUN python -c "\
from nalar import tarif_resmi as t; import sys; p = t._muat();\
print('tarif resmi terbaca:', len(p), 'kunci,', len({k[0] for k in p}), 'kode');\
sys.exit(0 if len(p) > 30000 else 1)"

EXPOSE 7860
CMD ["uvicorn", "nalar.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
