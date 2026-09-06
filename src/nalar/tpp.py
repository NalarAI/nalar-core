"""Kepala K3, integritas episode di sumbu waktu.

Menjawab keluarga B pada taksonomi: pemecahan episode, readmisi, penagihan
berulang, dan perpanjangan lama rawat. Percobaan keempat membuktikan
memperbesar tulang punggung tidak menambah rupiah yang ditemukan, karena K1
dan K2 hanya menyentuh keluarga A. Kepala inilah yang seharusnya menutup
keluarga B.

Bentuknya proses titik temporal bertanda. Diberikan representasi satu episode,
model menebak dua hal tentang episode berikutnya pada pasien yang sama:

  kapan   jarak hari sampai episode berikutnya, sebagai campuran log-normal
  apa     apakah episode berikutnya melanjutkan diagnosis yang sama,
          berpindah diagnosis, atau tidak ada lagi

Campuran log-normal dipilih, bukan intensitas kontinu dengan integral
kompensator, karena rapatnya sudah ternormalkan sendiri sehingga tidak perlu
kuadratur numerik. Untuk pertanyaan yang kami ajukan, yaitu seberapa
mengejutkan jarak sampai kejadian berikutnya, rapat jarak antar-kejadian sudah
memuat seluruh jawabannya.

Mengapa ini lebih baik daripada aturan jendela tetap. Aturan memakai satu
angka untuk semua, misalnya tiga puluh hari, dan angka tetap salah di dua
arah. Kemoterapi tiap tiga minggu itu sah dan akan tertangkap. Readmisi
ortopedi elektif dua hari itu janggal dan akan tenggelam bersama ribuan kasus
wajar. Model ini belajar jarak yang wajar per jenis kasus, dan jenis kasusnya
ratusan.
"""

from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn

# tanda pada episode berikutnya
TANDA_LANJUT = 0  # diagnosis primer sama, kemungkinan satu episode dipecah
TANDA_PINDAH = 1  # diagnosis primer berbeda
TANDA_HABIS = 2  # tidak ada episode berikutnya di jendela pengamatan
N_TANDA = 3


class KepalaWaktu(nn.Module):
    """Rapat jarak antar-episode dan sebaran tanda, dari representasi episode."""

    def __init__(self, d: int, n_campuran: int = 4, tersembunyi: int = 128):
        super().__init__()
        self.k = n_campuran
        self.badan = nn.Sequential(
            nn.Linear(d, tersembunyi),
            nn.GELU(),
            nn.Linear(tersembunyi, tersembunyi),
            nn.GELU(),
        )
        # bobot campuran, rerata, dan simpangan pada skala logaritma hari
        self.ke_bobot = nn.Linear(tersembunyi, n_campuran)
        self.ke_mu = nn.Linear(tersembunyi, n_campuran)
        self.ke_log_sigma = nn.Linear(tersembunyi, n_campuran)
        self.ke_tanda = nn.Linear(tersembunyi, N_TANDA)
        # awali agar campuran menyebar dari jarak pendek sampai panjang
        with torch.no_grad():
            self.ke_mu.bias.copy_(
                torch.log(torch.tensor([2.0, 14.0, 60.0, 240.0][:n_campuran]))
            )
            self.ke_log_sigma.bias.fill_(math.log(0.9))

    def forward(self, h: torch.Tensor):
        z = self.badan(h)
        log_pi = torch.log_softmax(self.ke_bobot(z), dim=-1)
        mu = self.ke_mu(z)
        log_sigma = self.ke_log_sigma(z).clamp(-3.0, 2.0)
        log_tanda = torch.log_softmax(self.ke_tanda(z), dim=-1)
        return log_pi, mu, log_sigma, log_tanda

    def log_rapat(self, h: torch.Tensor, dhari: torch.Tensor) -> torch.Tensor:
        """Logaritma rapat jarak hari, di bawah campuran log-normal."""
        log_pi, mu, log_sigma, _ = self(h)
        t = dhari.clamp(min=0.5).float().unsqueeze(-1)
        x = torch.log(t)
        sigma = torch.exp(log_sigma)
        # rapat log-normal pada t, bukan pada log t, jadi ada suku minus log t
        komponen = (
            -0.5 * ((x - mu) / sigma) ** 2 - log_sigma - 0.5 * math.log(2 * math.pi) - x
        )
        return torch.logsumexp(log_pi + komponen, dim=-1)

    def rugi(self, h, dhari, tanda, ada_berikutnya) -> torch.Tensor:
        """Kemungkinan logaritmik negatif, waktu ditambah tanda.

        Episode terakhir tiap pasien tidak punya jarak berikutnya, jadi hanya
        menyumbang pada suku tanda. Membiarkannya menyumbang pada suku waktu
        akan mengajari model bahwa jarak tak hingga itu wajar.
        """
        _, _, _, log_tanda = self(h)
        rugi_tanda = -log_tanda.gather(1, tanda.view(-1, 1)).squeeze(1)
        m = ada_berikutnya.bool()
        if m.any():
            rugi_waktu = -self.log_rapat(h[m], dhari[m])
        else:
            rugi_waktu = torch.zeros(1, device=h.device)
        return rugi_tanda.mean() + rugi_waktu.mean()

    @torch.no_grad()
    def peluang_lebih_lama(self, h, dhari) -> np.ndarray:
        """Peluang episode berikutnya seharusnya datang lebih lambat.

        Inilah kecurigaan pemecahan episode yang dinyatakan sebagai peluang.
        Nilainya mendekati satu ketika jarak yang teramati jauh lebih pendek
        daripada yang wajar untuk kasus seperti ini, dan mendekati nol ketika
        jaraknya wajar atau justru panjang.

        Bacanya lurus: berapa besar peluang bahwa kunjungan berikutnya yang sah
        akan datang lebih lambat daripada yang benar benar terjadi.
        """
        log_pi, mu, log_sigma, _ = self(h)
        x = torch.log(dhari.clamp(min=0.5).float()).unsqueeze(-1)
        z = (x - mu) / torch.exp(log_sigma)
        # fungsi sebaran kumulatif normal baku lewat fungsi galat
        cdf_k = 0.5 * (1.0 + torch.erf(z / math.sqrt(2.0)))
        cdf = (torch.exp(log_pi) * cdf_k).sum(-1)
        return (1.0 - cdf).clamp(0.0, 1.0).cpu().numpy()

    @torch.no_grad()
    def peluang_tanda(self, h) -> np.ndarray:
        """Sebaran peluang atas tiga tanda episode berikutnya."""
        _, _, _, log_tanda = self(h)
        return torch.exp(log_tanda).cpu().numpy()

    @torch.no_grad()
    def kejutan(self, h, dhari, tanda) -> np.ndarray:
        """Seberapa mengejutkan pasangan jarak dan tanda yang benar terjadi."""
        _, _, _, log_tanda = self(h)
        s = -(
            self.log_rapat(h, dhari) + log_tanda.gather(1, tanda.view(-1, 1)).squeeze(1)
        )
        return s.cpu().numpy()


def susun_pasangan(episodes, idx):
    """Bangun pasangan episode berurutan pada pasien yang sama.

    Mengembalikan indeks episode asal, jarak hari ke episode berikutnya,
    tandanya, dan penanda apakah episode berikutnya memang ada.
    """
    per_pasien: dict[int, list[int]] = {}
    for i in idx:
        per_pasien.setdefault(int(episodes[i]["peserta_id"]), []).append(int(i))

    asal, dhari, tanda, ada = [], [], [], []
    for pid, daftar in per_pasien.items():
        daftar.sort(key=lambda i: episodes[i]["hari"])
        for a, b in zip(daftar, daftar[1:]):
            asal.append(a)
            dhari.append(max(episodes[b]["hari"] - episodes[a]["hari"], 0))
            tanda.append(
                TANDA_LANJUT
                if episodes[b]["dxp"] == episodes[a]["dxp"]
                else TANDA_PINDAH
            )
            ada.append(1)
        asal.append(daftar[-1])
        dhari.append(0)
        tanda.append(TANDA_HABIS)
        ada.append(0)
    return (
        np.array(asal, dtype=np.int64),
        np.array(dhari, dtype=np.int64),
        np.array(tanda, dtype=np.int64),
        np.array(ada, dtype=np.int8),
    )


@torch.no_grad()
def representasi(model, arr, idx, dev, batch=256) -> torch.Tensor:
    """Representasi episode dari tulang punggung, dikumpulkan sekali."""
    model.eval()
    keluar = []
    for s in range(0, len(idx), batch):
        sel = idx[s : s + batch]
        tok = torch.from_numpy(arr["tok"][sel].astype(np.int64)).to(dev)
        fld = torch.from_numpy(arr["fld"][sel].astype(np.int64)).to(dev)
        dh = torch.from_numpy(arr["dhari"][sel].astype(np.int64)).to(dev)
        h, pad = model.encode(tok, fld, dh)
        v = (h * pad.unsqueeze(-1)).sum(1) / pad.sum(1, keepdim=True).clamp(min=1)
        keluar.append(v.cpu())
    return torch.cat(keluar) if keluar else torch.zeros(0, model.d)


def latih(
    kepala,
    H,
    dhari,
    tanda,
    ada,
    dev,
    langkah=400,
    batch=512,
    lr=2e-3,
    seed=0,
    log_setiap=100,
):
    """Latih kepala waktu. Tidak memakai satu pun label kecurangan."""
    rng = np.random.default_rng(seed)
    opt = torch.optim.AdamW(kepala.parameters(), lr=lr, weight_decay=1e-4)
    kepala.train()
    riwayat = []
    n = len(H)
    for t in range(1, langkah + 1):
        sel = rng.choice(n, size=min(batch, n), replace=False)
        h = H[sel].to(dev)
        d = torch.from_numpy(dhari[sel]).to(dev)
        m = torch.from_numpy(tanda[sel]).to(dev)
        a = torch.from_numpy(ada[sel]).to(dev)
        r = kepala.rugi(h, d, m, a)
        opt.zero_grad(set_to_none=True)
        r.backward()
        torch.nn.utils.clip_grad_norm_(kepala.parameters(), 1.0)
        opt.step()
        if t % log_setiap == 0 or t == 1:
            riwayat.append({"langkah": t, "rugi": round(float(r.item()), 4)})
    return riwayat


def rupiah_dipertaruhkan(episodes, a: int, b: int) -> int:
    """Berapa rupiah yang dipertaruhkan kalau dua episode ini sebenarnya satu.

    Bentuknya berbeda menurut tempat layanan, dan itu bukan kerumitan yang
    dibuat buat. Modusnya memang berbeda.

      Rawat inap dan rawat inap
          Pemecahan episode. Yang dipertaruhkan selisih antara jumlah dua
          tarif terpisah dan satu tarif gabungan.

      Rawat jalan berulang, diagnosis sama
          Kunjungan yang tidak perlu. Yang dipertaruhkan tarif kunjungan
          kedua itu sendiri, karena kalau ia memang tidak perlu, seluruh
          nilainya yang salah, bukan selisihnya.

    Versi pertama hanya menangani pasangan rawat inap, dan akibatnya cuma 93
    klaim dari 42.624 yang mendapat skor. Rawat inap hanya dua persen klaim,
    sedangkan kondisi kronis berulang seperti hemodialisis dan kemoterapi
    justru ada di rawat jalan dan berfrekuensi tinggi.

    Yang menyaring kunjungan sah dari yang tidak perlu bukan fungsi ini,
    melainkan peluang dari kepala waktu. Dialisis dua kali seminggu akan
    dipelajari sebagai wajar, jadi peluangnya rendah dan hasil kalinya kecil.
    """
    from .tarif import kelompokkan, tarif

    ra, rb = episodes[a], episodes[b]
    if ra["dxp"] != rb["dxp"]:
        return 0

    if ra["rawat_inap"] and rb["rawat_inap"]:
        dxs = list(dict.fromkeys(list(ra["dxs"]) + list(rb["dxs"])))[:9]
        prc = list(dict.fromkeys(list(ra["prc"]) + list(rb["prc"])))[:6]
        los = int(ra["los"]) + int(rb["los"])
        kel = kelompokkan(ra["dxp"], dxs, prc, los, True)
        gabung = tarif(
            kel, ra["dxp"], prc, ra["kelas_rawat"], ra["f_kelas"], ra["f_reg"]
        )
        return max(int(ra["tarif"] + rb["tarif"] - gabung), 0)

    if not ra["rawat_inap"] and not rb["rawat_inap"]:
        return int(rb["tarif"]) + int(rb.get("tagih_bhp", 0))

    return 0


# nama lama dipertahankan supaya pemanggil yang sudah ada tidak putus
def selisih_pemecahan(episodes, a: int, b: int) -> int:
    return rupiah_dipertaruhkan(episodes, a, b)
