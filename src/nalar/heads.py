"""Kepala hilir. Menerjemahkan kesulitan menebak menjadi rupiah.

Tulang punggung hanya tahu satu hal: seberapa mengejutkan isi klaim bila
dilihat dari sisa isinya. Kepala di sini yang mengubah kejutan itu menjadi
sesuatu yang bisa ditindaklanjuti auditor.

K1  konsistensi bukti, skor kejutan yang dinormalkan terhadap kasus sejenis
K2  tarif kontrafaktual, selisih rupiah antara yang ditagih dan yang didukung
K5  kemiripan berlebih, kelebihan pasangan mirip di atas yang diharapkan

Kepala K3 proses titik, K4 kelompok sebaya, dan K6 titik perubahan belum
ditulis. Statusnya ditulis apa adanya di catatan hasil, bukan diakui ada.
"""

from __future__ import annotations

import numpy as np
import torch

from .schema import FIELD_ID, MASK
from .tarif import Kelompok, tarif


# ---------------------------------------------------------------------------
# K1 konsistensi bukti
# ---------------------------------------------------------------------------

@torch.no_grad()
def skor_kejutan(model, kamus, arr, idx, bidang, dev, batch=256):
    """Minus logaritma peluang token yang benar benar ditagihkan.

    Bidang yang diuji ditutup, sisanya dibiarkan. Yang dikembalikan adalah
    rata rata kejutan per token pada bidang itu.
    """
    model.eval()
    id_mask = kamus.id(MASK)
    penanda = {kamus.id(f"[BID:{b}]") for b in bidang}
    ids_bidang = [FIELD_ID[b] for b in bidang]
    keluar = np.zeros(len(idx), dtype=np.float32)

    for s in range(0, len(idx), batch):
        sel = idx[s:s + batch]
        tok = arr["tok"][sel].astype(np.int64).copy()
        fld = arr["fld"][sel].astype(np.int64)
        pjg = arr["pjg"][sel]
        dh = arr["dhari"][sel].astype(np.int64)

        tutup = np.zeros_like(tok, dtype=bool)
        T = tok.shape[1]
        for b in range(len(sel)):
            m = ((np.arange(T) < pjg[b]) & np.isin(fld[b], ids_bidang)
                 & ~np.isin(tok[b], list(penanda)))
            tutup[b] = m
        asli = tok.copy()
        tok[tutup] = id_mask

        logit, _, _ = model(torch.from_numpy(tok).to(dev),
                            torch.from_numpy(fld).to(dev),
                            torch.from_numpy(dh).to(dev))
        logp = torch.log_softmax(logit.float(), dim=-1).cpu().numpy()
        for b in range(len(sel)):
            pos = np.flatnonzero(tutup[b])
            if pos.size == 0:
                keluar[s + b] = 0.0
                continue
            keluar[s + b] = float(
                -np.mean(logp[b, pos, asli[b, pos]]))
    return keluar


def normalkan_terhadap_sejenis(skor, kunci, minimal=25):
    """Ubah skor mentah menjadi posisi persentil di dalam kasus sejenis.

    Tanpa ini, model akan menandai rumah sakit rujukan nasional setiap hari,
    karena kasusnya memang jarang dan karena itu selalu mengejutkan. Dengan
    ini, pertanyaannya berubah menjadi apakah kasus langka ini mengejutkan
    dibanding kasus langka lain yang sejenis. Itu pertanyaan yang adil.

    Kelompok yang anggotanya terlalu sedikit dinormalkan terhadap seluruh
    korpus, karena persentil dari sepuluh contoh tidak berarti apa apa.
    """
    skor = np.asarray(skor, dtype=np.float64)
    keluar = np.zeros_like(skor)
    global_urut = np.argsort(np.argsort(skor)) / max(len(skor) - 1, 1)
    for k in np.unique(kunci):
        m = kunci == k
        n = int(m.sum())
        if n < minimal:
            keluar[m] = global_urut[m]
        else:
            s = skor[m]
            keluar[m] = np.argsort(np.argsort(s)) / max(n - 1, 1)
    return keluar


# ---------------------------------------------------------------------------
# K2 tarif kontrafaktual
# ---------------------------------------------------------------------------

class TabelTarif:
    """Peta dari token kelompok tarif ke nilai rupiah, per konteks klaim.

    Sejak tabel resmi masuk, kelas ini hanya membungkus tarif_resmi. Tabel
    tarif tetap dipisahkan sebagai berkas acuan, bukan ditanam di bobot model.
    Kalau tarif berubah, yang diganti berkasnya, bukan modelnya.
    """

    def __init__(self, kamus, episodes=None):
        from .tarif_resmi import matriks_tarif, vektor_tarif
        self._matriks_resmi = matriks_tarif
        self._vektor_resmi = vektor_tarif

        self.kode, tok_id = [], []
        for tok, i in kamus.stoi.items():
            if tok.startswith("CB:"):
                self.kode.append(tok[3:])
                tok_id.append(i)
        self.tok_id = np.array(tok_id, dtype=np.int64)
        self.peta_kode = {k: i for i, k in enumerate(self.kode)}
        # token kelas rawat, supaya kepala K2 menaksir kelas juga
        self.tok_kelas = np.array(
            [kamus.id(f"KLSRAWAT:{i}") for i in range(3)], dtype=np.int64)
        self.inap = np.array(
            [k.rsplit("-", 1)[1] in ("I", "II", "III") for k in self.kode])
        self._singgahan: dict[tuple, np.ndarray] = {}

    def nilai(self, dxp, prc, kelas_rawat, kelas_rs, regional,
              kepemilikan="PEMERINTAH"):
        """Vektor tarif untuk seluruh kelompok, pada konteks klaim ini."""
        return self._vektor_resmi(self.kode, kelas_rawat, kelas_rs,
                                  int(regional) + 1, kepemilikan)

    def matriks(self, dxp, prc, kelas_rs, regional,
                kepemilikan="PEMERINTAH"):
        """Tarif untuk setiap pasangan kelompok dan kelas rawat.

        Hasilnya disinggahkan per konteks, karena konteks yang berbeda cuma
        ada delapan puluh kombinasi sedangkan klaimnya ratusan ribu.
        """
        kunci = (kelas_rs, int(regional), kepemilikan)
        if kunci not in self._singgahan:
            self._singgahan[kunci] = self._matriks_resmi(
                self.kode, kelas_rs, int(regional) + 1, kepemilikan)
        return self._singgahan[kunci]


@torch.no_grad()
def selisih_tarif(model, kamus, arr, idx, episodes, tabel: TabelTarif, dev,
                  batch=128):
    """Selisih antara tarif yang ditagih dan tarif yang didukung bukti.

    Ini bentuk keluaran yang benar untuk pembayar. Bisa ditagih, karena BPJS
    memotong sebesar selisih bukan menolak seluruh klaim. Bisa dibantah, karena
    rumah sakit bisa menunjukkan bukti yang tidak terkirim. Bisa dijumlahkan,
    karena total selisih di satu rumah sakit adalah angka yang bisa dibawa ke
    rapat. Bisa diurutkan, karena antreannya langsung punya satuan yang benar.
    """
    model.eval()
    id_mask = kamus.id(MASK)
    penanda_trf = kamus.id("[BID:TRF]")
    f_trf = FIELD_ID["TRF"]
    tok_cbg = torch.from_numpy(tabel.tok_id).to(dev)
    tok_kls = torch.from_numpy(tabel.tok_kelas).to(dev)

    hasil = np.zeros(len(idx), dtype=np.float64)
    yakin = np.zeros(len(idx), dtype=np.float64)
    harapan = np.zeros(len(idx), dtype=np.float64)
    # peluang bahwa kelompok yang ditagihkan bukan kelompok yang benar,
    # dan besar selisihnya bila memang bukan
    p_salah = np.zeros(len(idx), dtype=np.float64)
    selisih_bila_salah = np.zeros(len(idx), dtype=np.float64)

    for s in range(0, len(idx), batch):
        sel = idx[s:s + batch]
        tok = arr["tok"][sel].astype(np.int64).copy()
        fld = arr["fld"][sel].astype(np.int64)
        pjg = arr["pjg"][sel]
        dh = arr["dhari"][sel].astype(np.int64)

        T = tok.shape[1]
        pos_cbg = np.full(len(sel), -1, dtype=np.int64)
        pos_kls = np.full(len(sel), -1, dtype=np.int64)
        for b in range(len(sel)):
            m = ((np.arange(T) < pjg[b]) & (fld[b] == f_trf)
                 & (tok[b] != penanda_trf))
            p = np.flatnonzero(m)
            if p.size:
                pos_cbg[b] = p[0]      # token kelompok tarif ada di awal TRF
            if p.size > 1:
                pos_kls[b] = p[1]      # lalu kelas rawat
            tok[b, m] = id_mask

        logit, _, _ = model(torch.from_numpy(tok).to(dev),
                            torch.from_numpy(fld).to(dev),
                            torch.from_numpy(dh).to(dev))

        for b in range(len(sel)):
            if pos_cbg[b] < 0:
                continue
            r = episodes[sel[b]]
            p = torch.softmax(
                logit[b, pos_cbg[b]].float()[tok_cbg], dim=-1).cpu().numpy()
            if pos_kls[b] >= 0:
                q = torch.softmax(
                    logit[b, pos_kls[b]].float()[tok_kls], dim=-1
                ).cpu().numpy()
            else:
                q = np.zeros(3)
                q[r["kelas_rawat"] - 1] = 1.0
            M = tabel.matriks(r["dxp"], r["prc"], r["f_kelas"], r["f_reg"])
            # kelompok tarif dan kelas rawat dianggap saling bebas bila
            # buktinya sudah diketahui. Itu penyederhanaan, dan tanpa
            # penyederhanaan itu kita harus menaksir sebaran gabungan atas
            # seribu lima ratus lebih pasangan dari satu klaim.
            e = float(p @ M @ q)
            harapan[s + b] = e
            hasil[s + b] = float(r["tarif"]) - e
            yakin[s + b] = float(p.max() * q.max())

            # Percobaan pertama memakai gabungan berupa perkalian antara
            # persentil kejutan dan selisih rupiah. Hasilnya lebih buruk
            # daripada memakai selisih rupiah saja, karena peluangnya sudah
            # terkandung di dalam nilai harapan dan perkalian menghitungnya
            # dua kali. Yang di bawah adalah bentuk yang benar, yaitu peluang
            # kelompok yang ditagihkan salah, dikali selisih bila memang salah.
            j = tabel.peta_kode.get(r["cbg"], -1)
            jk = r["kelas_rawat"] - 1
            if j >= 0:
                pk = float(p[j] * q[jk])
                p_salah[s + b] = 1.0 - pk
                if pk < 1.0 - 1e-9:
                    pq = np.outer(p, q).copy()
                    pq[j, jk] = 0.0
                    tot = pq.sum()
                    if tot > 1e-12:
                        e_salah = float((pq * M).sum() / tot)
                        selisih_bila_salah[s + b] = float(r["tarif"]) - e_salah
            else:
                p_salah[s + b] = 1.0
                selisih_bila_salah[s + b] = hasil[s + b]
    return hasil, harapan, yakin, p_salah, selisih_bila_salah


# ---------------------------------------------------------------------------
# K5 kemiripan berlebih
# ---------------------------------------------------------------------------

def _tanda_tangan(r, bobot_entropi):
    """Ringkas isi klaim menjadi himpunan berbobot.

    Protokol klinis memang menyeragamkan yang seharusnya seragam, yaitu
    tindakan dan obat. Penjiplakan menyeragamkan juga yang seharusnya
    bervariasi, yaitu nilai pemeriksaan dan lama rawat. Karena itu kesamaan
    pada variabel bervariasi diberi bobot lebih besar, dan bobotnya tidak
    ditetapkan manusia tapi diambil dari entropi variabel itu dalam korpus.
    """
    from . import katalog as K
    unsur = []
    for c in r["dxs"]:
        unsur.append(("DX", c))
    for c in r["prc"]:
        unsur.append(("PR", c))
    for c in r["obt"]:
        unsur.append(("OB", c))
    for kode, nilai in r["lab"]:
        unsur.append(("LB", f"{kode}:{K.pita_lab(kode, nilai)}"))
    unsur.append(("LOS", str(r["los"])))
    return {u: bobot_entropi.get(u[0], 1.0) for u in unsur}


def bobot_dari_entropi(episodes):
    """Bobot per jenis unsur, dari entropi sebarannya di korpus."""
    from collections import Counter
    from . import katalog as K
    hit = {"DX": Counter(), "PR": Counter(), "OB": Counter(),
           "LB": Counter(), "LOS": Counter()}
    for r in episodes:
        for c in r["dxs"]:
            hit["DX"][c] += 1
        for c in r["prc"]:
            hit["PR"][c] += 1
        for c in r["obt"]:
            hit["OB"][c] += 1
        for kode, nilai in r["lab"]:
            hit["LB"][f"{kode}:{K.pita_lab(kode, nilai)}"] += 1
        hit["LOS"][r["los"]] += 1
    bobot = {}
    for jenis, c in hit.items():
        tot = sum(c.values()) or 1
        p = np.array(list(c.values()), dtype=np.float64) / tot
        h = float(-(p * np.log(p + 1e-12)).sum())
        bobot[jenis] = h
    maks = max(bobot.values()) or 1.0
    return {k: v / maks for k, v in bobot.items()}


def kemiripan_berlebih(episodes, idx, n_pasang_maks=400_000, seed=0):
    """Kelebihan pasangan mirip di dalam satu faskes, di atas yang diharapkan.

    Yang diharapkan diambil dari faskes lain dengan bauran kasus serupa. Jadi
    pembandingnya bukan nol, melainkan tingkat kemiripan yang wajar muncul
    karena protokol klinis.
    """
    rng = np.random.default_rng(seed)
    bobot = bobot_dari_entropi([episodes[i] for i in idx])
    per_faskes: dict[int, list[int]] = {}
    for i in idx:
        r = episodes[i]
        if r["f_jenis"]:
            per_faskes.setdefault(int(r["faskes"]), []).append(int(i))

    tanda = {}
    for i in idx:
        tanda[int(i)] = _tanda_tangan(episodes[int(i)], bobot)

    def jaccard(a, b):
        ka, kb = set(a), set(b)
        if not ka or not kb:
            return 0.0
        irisan = sum(a[k] for k in ka & kb)
        gabung = sum(a[k] for k in ka) + sum(b[k] for k in kb) - irisan
        return irisan / max(gabung, 1e-9)

    skor_faskes = {}
    for f, anggota in per_faskes.items():
        if len(anggota) < 8:
            continue
        n_pasang = min(len(anggota) * 6, 3000)
        a = rng.choice(anggota, size=n_pasang)
        b = rng.choice(anggota, size=n_pasang)
        nilai = [jaccard(tanda[int(x)], tanda[int(y)])
                 for x, y in zip(a, b) if x != y]
        if not nilai:
            continue
        nilai = np.array(nilai)
        skor_faskes[f] = dict(
            rerata=float(nilai.mean()),
            porsi_sangat_mirip=float((nilai > 0.85).mean()),
            n=len(anggota))

    if not skor_faskes:
        return {}, 0.0
    dasar = float(np.median([v["porsi_sangat_mirip"]
                             for v in skor_faskes.values()]))
    for f, v in skor_faskes.items():
        v["kelebihan"] = v["porsi_sangat_mirip"] - dasar
    return skor_faskes, dasar


# ---------------------------------------------------------------------------
# K4 kelompok sebaya
# ---------------------------------------------------------------------------

def kmeans(X, k, iterasi=40, seed=0):
    """K-means sederhana, ditulis sendiri.

    Dipakai membentuk kelompok sebaya faskes. Ditulis sendiri karena
    scikit-learn tidak terpasang, dan karena algoritmanya cukup pendek
    sehingga menambah ketergantungan tidak sepadan.
    """
    rng = np.random.default_rng(seed)
    n = len(X)
    k = min(k, n)
    pusat = X[rng.choice(n, size=k, replace=False)].copy()
    label = np.zeros(n, dtype=np.int64)
    for _ in range(iterasi):
        jarak = ((X[:, None, :] - pusat[None, :, :]) ** 2).sum(-1)
        baru = jarak.argmin(1)
        if (baru == label).all():
            break
        label = baru
        for j in range(k):
            m = label == j
            if m.any():
                pusat[j] = X[m].mean(0)
    return label, pusat


@torch.no_grad()
def sebaran_harapan(model, kamus, arr, idx, tabel, dev, batch=128):
    """Sebaran peluang kelompok tarif yang diharapkan, per klaim.

    Bidang tarif ditutup, lalu model menebaknya dari bukti. Yang dikembalikan
    adalah sebaran penuh, bukan tebakan tunggal, karena yang dibandingkan pada
    tingkat faskes adalah sebaran melawan sebaran.
    """
    model.eval()
    id_mask = kamus.id(MASK)
    penanda_trf = kamus.id("[BID:TRF]")
    f_trf = FIELD_ID["TRF"]
    tok_cbg = torch.from_numpy(tabel.tok_id).to(dev)
    out = np.zeros((len(idx), len(tabel.kode)), dtype=np.float32)

    for s in range(0, len(idx), batch):
        sel = idx[s:s + batch]
        tok = arr["tok"][sel].astype(np.int64).copy()
        fld = arr["fld"][sel].astype(np.int64)
        pjg = arr["pjg"][sel]
        dh = arr["dhari"][sel].astype(np.int64)
        T = tok.shape[1]
        pos = np.full(len(sel), -1, dtype=np.int64)
        for b in range(len(sel)):
            m = ((np.arange(T) < pjg[b]) & (fld[b] == f_trf)
                 & (tok[b] != penanda_trf))
            p = np.flatnonzero(m)
            if p.size:
                pos[b] = p[0]
            tok[b, m] = id_mask
        logit, h, _ = model(torch.from_numpy(tok).to(dev),
                            torch.from_numpy(fld).to(dev),
                            torch.from_numpy(dh).to(dev))
        for b in range(len(sel)):
            if pos[b] < 0:
                continue
            out[s + b] = torch.softmax(
                logit[b, pos[b]].float()[tok_cbg], dim=-1).cpu().numpy()
    return out


@torch.no_grad()
def wakil_faskes(model, kamus, arr, idx, episodes, dev, batch=256):
    """Vektor wakil tiap faskes, dari rata rata representasi episodenya."""
    model.eval()
    d = model.d
    jumlah: dict[int, np.ndarray] = {}
    hitung: dict[int, int] = {}
    for s in range(0, len(idx), batch):
        sel = idx[s:s + batch]
        tok = torch.from_numpy(arr["tok"][sel].astype(np.int64)).to(dev)
        fld = torch.from_numpy(arr["fld"][sel].astype(np.int64)).to(dev)
        dh = torch.from_numpy(arr["dhari"][sel].astype(np.int64)).to(dev)
        h, pad = model.encode(tok, fld, dh)
        v = (h * pad.unsqueeze(-1)).sum(1) / pad.sum(1, keepdim=True).clamp(min=1)
        v = v.cpu().numpy()
        for b, i in enumerate(sel):
            r = episodes[i]
            if not r["f_jenis"]:
                continue
            f = int(r["faskes"])
            jumlah[f] = jumlah.get(f, np.zeros(d, dtype=np.float64)) + v[b]
            hitung[f] = hitung.get(f, 0) + 1
    faskes = sorted(jumlah)
    X = np.stack([jumlah[f] / hitung[f] for f in faskes]) if faskes else \
        np.zeros((0, d))
    return faskes, X, np.array([hitung[f] for f in faskes])


def divergensi_sebaya(episodes, idx, tabel, harapan, faskes_list, kelompok,
                      minimal=40, selisih_klaim=None):
    """Seberapa jauh sebaran tarif faskes menyimpang dari yang diharapkan.

    Pembandingnya bukan sebaran rata rata kelompok, tapi sebaran yang
    diperkirakan model untuk pasien pasien yang benar benar datang ke faskes
    ini. Ini yang menjawab bantahan paling umum dari rumah sakit, bahwa pasien
    mereka memang lebih berat.
    """
    peta_kode = {k: i for i, k in enumerate(tabel.kode)}
    per_faskes: dict[int, list[int]] = {}
    for j, i in enumerate(idx):
        r = episodes[i]
        if r["f_jenis"]:
            per_faskes.setdefault(int(r["faskes"]), []).append(j)

    kel_of = {f: int(k) for f, k in zip(faskes_list, kelompok)}
    hasil = {}
    for f, pos in per_faskes.items():
        if len(pos) < minimal:
            continue
        teramati = np.zeros(len(tabel.kode), dtype=np.float64)
        for j in pos:
            c = episodes[idx[j]]["cbg"]
            if c in peta_kode:
                teramati[peta_kode[c]] += 1.0
        teramati /= max(teramati.sum(), 1.0)
        diharap = harapan[pos].mean(0).astype(np.float64)
        diharap /= max(diharap.sum(), 1e-12)

        # divergensi Jensen Shannon, simetris dan berbatas
        m = 0.5 * (teramati + diharap)
        def kl(p, q):
            m_ = p > 0
            return float((p[m_] * np.log(p[m_] / np.maximum(q[m_], 1e-12))).sum())
        js = 0.5 * kl(teramati, m) + 0.5 * kl(diharap, m)

        # Kelebihan rupiah yang diperkirakan dari pergeseran sebaran. Nilai
        # per kelompok diambil dari tabel resmi pada satu konteks acuan, yaitu
        # rumah sakit kelas C regional 1 kelas rawat 3, karena yang
        # dibandingkan di sini pergeseran sebarannya, bukan tarif absolutnya.
        nilai = tabel.matriks(None, [], "C", 0)[:, 2]
        lebih = float((teramati - diharap) @ nilai) * len(pos)
        # Kelebihan rupiah rata rata per klaim. Percobaan kedua menunjukkan
        # divergensi sebaran terlalu berisik pada faskes dengan sedikit klaim,
        # dan peringkatnya nyaris tidak lebih baik daripada acak. Rata rata
        # selisih per klaim jauh lebih stabil, dan satuannya langsung rupiah.
        if selisih_klaim is not None:
            per_klaim = float(np.mean(np.clip(selisih_klaim[pos], 0, None)))
        else:
            per_klaim = lebih / max(len(pos), 1)
        hasil[f] = dict(js=round(js, 5), n=len(pos),
                        kelompok=kel_of.get(f, -1),
                        kelebihan_per_klaim_rp=round(per_klaim),
                        perkiraan_kelebihan_rp=round(lebih))

    # bandingkan hanya di dalam kelompok sebaya
    for kel in {v["kelompok"] for v in hasil.values()}:
        anggota = [f for f, v in hasil.items() if v["kelompok"] == kel]
        if len(anggota) < 3:
            for f in anggota:
                hasil[f]["js_relatif"] = 0.0
                hasil[f]["skor_relatif"] = 0.0
            continue
        for kunci, nama in (("js", "js_relatif"),
                            ("kelebihan_per_klaim_rp", "skor_relatif")):
            nilai = np.array([hasil[f][kunci] for f in anggota], dtype=float)
            med = float(np.median(nilai))
            mad = float(np.median(np.abs(nilai - med))) or 1e-9
            for f in anggota:
                hasil[f][nama] = round((hasil[f][kunci] - med) / mad, 3)
    return hasil
