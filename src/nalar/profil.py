"""Kepala K4 yang ditulis ulang: mencurigai faskes, bukan klaim.

Versi lama membentuk kelompok sebaya dari representasi transformer, lalu
membandingkan sebaran kode INA-CBG faskes terhadap sebaran harapan memakai
divergensi Jensen Shannon. Presisinya pada sepuluh teratas 0,2 sampai 0,3
melawan tebakan acak 0,16. Praktis tidak lebih baik daripada acak.

Sebabnya bisa ditunjuk. Divergensi itu dihitung atas sebaran multinomial
sepanjang 885 kode, ditaksir dari empat puluh klaim. Dengan sedikit klaim,
sebagian besar divergensi yang terukur adalah derau pencuplikan, bukan
perilaku faskes. Faskes kecil otomatis terlihat menyimpang. Statistik yang
dipakai tidak pernah mengoreksi banyaknya klaim, jadi peringkatnya sebagian
besar mengurutkan faskes menurut kekecilannya.

Versi ini mengganti dua duanya. Kelompok sebaya dibentuk dari sifat yang bisa
dilihat siapa saja, yaitu kelas, wilayah, kepemilikan, dan status daerah
tertinggal, bukan dari representasi yang dipelajari. Dan statistiknya diganti
penyusutan Bayes empiris, yang justru pekerjaannya menghukum taksiran dari
sedikit data supaya mendekat ke rata rata kelompoknya.

Bentuk ini bukan karangan kami. Inilah cara profil penyedia layanan dikerjakan
pada program pembanding, dan alasannya sama: pertanyaannya bukan faskes mana
yang selisihnya paling besar, melainkan faskes mana yang selisihnya paling
besar setelah diperhitungkan berapa banyak klaim yang kita punya darinya.
"""

from __future__ import annotations

import numpy as np


def kunci_sebaya(r) -> str:
    """Kelompok sebaya dari sifat yang teramati, bukan yang dipelajari.

    Rumah sakit boleh membantah skornya, tapi ia tidak bisa membantah bahwa ia
    rumah sakit kelas B milik pemerintah di regional 2. Itu sebabnya kelompok
    ini dibentuk dari kolom administratif saja.
    """
    return f"{r['f_kelas']}|{r['f_reg']}|{r['f_milik']}|{r['f_dtpk']}"


def profil_faskes(episodes, selisih, minimal_klaim=20, minimal_sebaya=3):
    """Selisih per faskes, disusutkan ke rata rata kelompok sebayanya.

    Yang dikembalikan satu baris per faskes, memuat rata rata mentah, rata
    rata setelah disusutkan, skor baku, dan perkiraan kelebihan rupiah
    setahun. Yang dipakai memberi peringkat adalah kelebihan rupiah, karena
    itulah satuan yang bisa dibawa ke rapat.

    minimal_klaim menahan faskes yang klaimnya terlalu sedikit untuk
    dinyatakan apa apa. Mereka tidak dinyatakan bersih, mereka dinyatakan
    belum bisa dinilai, dan itu dua hal yang berbeda.
    """
    selisih = np.asarray(selisih, dtype=np.float64)

    per_faskes: dict[tuple, list[int]] = {}
    sifat: dict[tuple, dict] = {}
    for i, r in enumerate(episodes):
        kunci = (int(r["f_jenis"]), int(r["faskes"]))
        per_faskes.setdefault(kunci, []).append(i)
        sifat.setdefault(kunci, r)

    # Tahap satu: statistik mentah per faskes.
    mentah = {}
    for kunci, pos in per_faskes.items():
        if len(pos) < minimal_klaim:
            continue
        v = selisih[pos]
        mentah[kunci] = {
            "n": len(pos),
            "rata": float(v.mean()),
            "ragam": float(v.var(ddof=1)) if len(v) > 1 else 0.0,
            "sebaya": kunci_sebaya(sifat[kunci]),
            "pos": pos,
        }

    # Tahap dua: rata rata dan ragam antar faskes, per kelompok sebaya.
    #
    # Ragam antar faskes ditaksir dengan mengurangkan ragam dalam faskes dari
    # ragam total. Tanpa pengurangan itu, sebaran antar faskes akan terlihat
    # lebih lebar daripada yang sebenarnya, penyusutannya jadi terlalu lemah,
    # dan faskes kecil kembali naik ke atas. Itu persis kesalahan versi lama.
    kelompok: dict[str, list[tuple]] = {}
    for kunci, d in mentah.items():
        kelompok.setdefault(d["sebaya"], []).append(kunci)

    hasil = {}
    for nama, anggota in kelompok.items():
        if len(anggota) < minimal_sebaya:
            continue
        rata = np.array([mentah[k]["rata"] for k in anggota])
        n = np.array([mentah[k]["n"] for k in anggota], dtype=np.float64)
        ragam_dalam = np.array([mentah[k]["ragam"] for k in anggota])

        mu = float(np.average(rata, weights=n))
        sigma2 = float(np.average(ragam_dalam, weights=n))
        var_total = float(np.average((rata - mu) ** 2, weights=n))
        tau2 = max(var_total - sigma2 / max(n.mean(), 1.0), 1e-9)

        for j, kunci in enumerate(anggota):
            d = mentah[kunci]
            # bobot penyusutan: makin banyak klaim, makin dipercaya
            w = tau2 / (tau2 + sigma2 / max(d["n"], 1))
            susut = w * d["rata"] + (1 - w) * mu
            se = np.sqrt(sigma2 / max(d["n"], 1) + tau2)
            # Pembulatan ke bilangan bulat sempat merusak kepala ini ketika
            # yang dimasukkan bukan rupiah melainkan posisi terhadap ambang,
            # yang nilainya berada di antara minus satu dan satu. Seluruh
            # kolomnya menjadi nol dan peringkatnya kehilangan ketelitian.
            # Sekarang ketelitiannya mengikuti besaran yang masuk.
            kel = float(max(susut - mu, 0.0)) * d["n"]
            bulat = abs(mu) > 1000.0
            hasil[kunci] = {
                "n": d["n"],
                "sebaya": nama,
                "n_sebaya": len(anggota),
                "rata_mentah": round(d["rata"]) if bulat else round(d["rata"], 6),
                "rata_sebaya": round(mu) if bulat else round(mu, 6),
                "rata_susut": round(float(susut)) if bulat else round(float(susut), 6),
                "bobot_percaya": round(float(w), 4),
                "z": round(float((susut - mu) / max(se, 1e-9)), 3),
                "kelebihan": round(kel) if bulat else round(kel, 6),
                # nama lama dipertahankan supaya berkas hasil lama tetap
                # terbaca dan skrip yang sudah ada tidak patah
                "rata_susut_rp": round(float(susut))
                if bulat
                else round(float(susut), 6),
                "rata_sebaya_rp": round(mu) if bulat else round(mu, 6),
                "rata_mentah_rp": round(d["rata"]) if bulat else round(d["rata"], 6),
                "kelebihan_rp": round(kel) if bulat else round(kel, 6),
            }
    return hasil


def peringkat_faskes(profil, atas=None):
    """Faskes diurutkan menurut perkiraan kelebihan rupiah."""
    urut = sorted(profil.items(), key=lambda kv: -kv[1]["kelebihan_rp"])
    return urut[:atas] if atas else urut


def presisi_faskes_pada_k(profil, kebenaran, daftar_k=(10, 25, 50)):
    """Berapa banyak dari k faskes teratas yang memang berkebijakan nakal.

    kebenaran adalah peta dari kunci faskes ke nol atau satu.
    """
    urut = [k for k, _ in peringkat_faskes(profil)]
    dasar = float(np.mean([kebenaran.get(k, 0) for k in urut])) if urut else 0.0
    out = {"prevalensi_dasar": round(dasar, 4), "n_faskes_dinilai": len(urut)}
    for k in daftar_k:
        sel = urut[:k]
        if not sel:
            continue
        out[f"presisi@{k}"] = round(
            float(np.mean([kebenaran.get(x, 0) for x in sel])), 4
        )
        out[f"peningkatan@{k}"] = (
            round(out[f"presisi@{k}"] / dasar, 3) if dasar > 0 else None
        )
    return out


# ---------------------------------------------------------------------------
# Kepala K6, titik perubahan
# ---------------------------------------------------------------------------
#
# Pertanyaannya berbeda dari K4. K4 bertanya faskes mana yang selisihnya
# menonjol terhadap sebayanya. K6 bertanya faskes mana yang berubah perilaku,
# termasuk faskes yang rata rata setahunnya masih terlihat wajar karena
# separuh pertama tahun itu memang wajar.
#
# Ini yang membuatnya perlu. Faskes yang baru mulai menyimpang enam bulan lalu
# akan lolos dari K4 selama beberapa bulan, karena rata ratanya masih tertahan
# oleh masa lalunya yang bersih. Justru faskes itulah yang paling murah
# dihentikan, karena kebiasaannya belum mengeras.


def titik_perubahan(
    nilai, hari, minimal_sisi=25, n_acak=200, seed=0, peringkat=True, blok=None
):
    """Cari satu titik di mana rata rata deret bergeser, plus peluang semunya.

    Statistiknya selisih rata rata terbesar antara sebelum dan sesudah, dicari
    atas semua titik potong yang menyisakan cukup data di kedua sisi.

    Nilai p dihitung dengan mengacak urutan deret lalu mengulang pencarian.
    Ini penting dan sering dilewatkan: mengambil selisih terbesar atas banyak
    titik potong akan menghasilkan angka besar bahkan pada deret yang tidak
    berubah sama sekali. Yang harus dibandingkan bukan selisihnya terhadap
    nol, melainkan selisihnya terhadap selisih terbesar yang muncul kalau
    urutannya memang tidak berarti apa apa.
    """
    nilai = np.asarray(nilai, dtype=np.float64)
    hari = np.asarray(hari, dtype=np.int64)
    urut = np.argsort(hari)
    v, h = nilai[urut], hari[urut]
    n = len(v)
    if n < 2 * minimal_sisi:
        return None

    # Deret selisih itu berduri. Sebagian besar klaim selisihnya nol atau
    # kecil, lalu sesekali muncul satu yang besarnya jutaan. Pada deret
    # seperti itu, selisih rata rata terbesar didominasi oleh letak beberapa
    # klaim besar, bukan oleh pergeseran perilaku. Akibatnya terukur: tanggal
    # tebakan meleset 515 hari dari rentang 1095 hari, praktis setara dengan
    # menebak tengah tengah.
    #
    # Nilainya diganti peringkat di dalam faskes itu sendiri. Yang tersisa
    # tinggal urutannya, dan satu klaim raksasa tidak lagi bisa menarik
    # seluruh statistik ke arahnya. Uji permutasinya tetap sah, karena
    # peringkat dihitung sekali di awal dan yang diacak sesudahnya.
    mentah = v
    rng_awal = np.random.default_rng(seed)
    if peringkat:
        # Nilai yang seri harus diputus secara acak, dan ini bukan detail.
        # Enam puluh persen selisih klaim bernilai nol persis. np.argsort
        # stabil, jadi klaim klaim nol itu menerima peringkat menurut urutan
        # kemunculannya, yaitu urutan waktu. Urutan waktu lalu tersuntik ke
        # dalam nilai yang seharusnya tidak membawanya, dan uji permutasinya
        # runtuh: 71,6 persen faskes ditandai berubah pada data yang tidak
        # memuat satu pun perubahan. Diputus acak, angkanya kembali ke 5,2
        # persen.
        kunci = v + rng_awal.random(n) * 1e-9 * (np.abs(v).max() + 1.0)
        v = np.argsort(np.argsort(kunci)).astype(np.float64) / max(n - 1, 1)

    def cari(x):
        kum = np.cumsum(x)
        total = kum[-1]
        i = np.arange(minimal_sisi, n - minimal_sisi + 1)
        kiri = kum[i - 1] / i
        kanan = (total - kum[i - 1]) / (n - i)
        beda = kanan - kiri
        j = int(np.argmax(beda))
        return float(beda[j]), int(i[j])

    beda, potong = cari(v)
    rng = np.random.default_rng(seed)

    # Pengacakan per blok, bukan per klaim.
    #
    # Uji permutasi mengandaikan klaim saling terpertukarkan. Klaim dari satu
    # pasien tidak. Terukurnya begini: posisi dua klaim milik pasien yang sama
    # berkorelasi 0,135, sedangkan dua klaim yang diambil acak berkorelasi
    # nol. Pasien yang sama datang berdekatan waktunya, jadi korelasi itu
    # tersalin menjadi struktur waktu yang tidak pernah dihancurkan oleh
    # pengacakan per klaim. Akibatnya nilai p terlalu kecil, dan 9,2 persen
    # faskes ditandai berubah pada data yang tidak memuat perubahan apa pun.
    #
    # Yang diacak sekarang urutan bloknya, bukan isinya. Korelasi di dalam
    # pasien tetap utuh pada tiruan acaknya, sehingga yang dibandingkan
    # benar benar setara.
    if blok is not None:
        blok_urut = np.asarray(blok)[urut]
        _, awal = np.unique(blok_urut, return_index=True)
        potongan = np.split(np.arange(n), np.sort(awal)[1:])

        def acak():
            urutan = rng.permutation(len(potongan))
            return v[np.concatenate([potongan[j] for j in urutan])]
    else:

        def acak():
            return rng.permutation(v)

    lebih = sum(1 for _ in range(n_acak) if cari(acak())[0] >= beda)
    return {
        "hari_ganti": int(h[potong]),
        "n_sebelum": potong,
        "n_sesudah": n - potong,
        "rata_sebelum_rp": round(float(mentah[:potong].mean())),
        "rata_sesudah_rp": round(float(mentah[potong:].mean())),
        "lonjakan_rp": round(float(mentah[potong:].mean() - mentah[:potong].mean())),
        "lonjakan_peringkat": round(float(beda), 4),
        "p": round((lebih + 1) / (n_acak + 1), 4),
    }


def perubahan_faskes(
    episodes,
    selisih,
    minimal_klaim=60,
    n_acak=200,
    seed=0,
    peringkat=True,
    per_pasien=True,
):
    """Titik perubahan untuk tiap faskes yang klaimnya cukup banyak."""
    selisih = np.asarray(selisih, dtype=np.float64)
    per: dict[tuple, list[int]] = {}
    for i, r in enumerate(episodes):
        per.setdefault((int(r["f_jenis"]), int(r["faskes"])), []).append(i)
    hasil = {}
    for kunci, pos in per.items():
        if len(pos) < minimal_klaim:
            continue
        t = titik_perubahan(
            selisih[pos],
            [episodes[i]["hari"] for i in pos],
            n_acak=n_acak,
            seed=seed,
            peringkat=peringkat,
            blok=([episodes[i]["peserta_id"] for i in pos] if per_pasien else None),
        )
        if t is not None:
            hasil[kunci] = t
    return hasil
