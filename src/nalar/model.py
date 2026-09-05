"""Tulang punggung NALAR, ditulis dari nol.

Yang dipakai dari PyTorch hanya operasi tensor, turunan otomatis, dan modul
dasar seperti Linear, Embedding, dan LayerNorm. Modul transformer bawaan dan
modul perhatian bawaan tidak dipakai, karena bias antar-bidang tidak bisa
disisipkan ke dalamnya tanpa menulis ulang perhitungan skornya.

Tiga hal yang berbeda dari encoder biasa:

  1. Embedding dirakit dari leluhur di pohon kode, bukan satu baris tabel.
  2. Skor perhatian menerima bias yang bergantung pada pasangan bidang.
  3. Penutupan saat pralatih mengikuti peran bidang, bukan acak seragam.

Ketiganya bisa dimatikan lewat saklar, supaya ablasi bisa dijalankan dan tiap
komponen membuktikan haknya untuk ada.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from .schema import N_FIELDS


class EmbeddingOntologi(nn.Module):
    """Vektor kode dirakit dari dirinya sendiri dan leluhurnya.

    Kode yang sering muncul akan bergantung pada vektornya sendiri. Kode yang
    jarang akan bergantung pada leluhurnya. Ini penting karena upcoding hampir
    selalu berarti berpindah ke kode tetangga yang lebih mahal, bukan ke kode
    acak. Kalau model tidak tahu mana kode yang bertetangga, ia tidak bisa
    melihat perpindahan itu sebagai hal kecil yang mencurigakan.

    Mengikuti gagasan GRAM. Ditulis ulang dari makalah, bukan memakai kode
    penulisnya, dan disesuaikan pada tiga hal: hierarki ICD-10 bukan CCS,
    pohon yang sama dipakai untuk ATC dan kode kelompok tarif, dan ada pinalti
    agar jarak antar-vektor menghormati jarak di pohon.
    """

    def __init__(self, n_vocab: int, d: int, leluhur: torch.Tensor,
                 leluhur_mask: torch.Tensor, aktif: bool = True):
        super().__init__()
        self.aktif = aktif
        self.d = d
        self.dasar = nn.Embedding(n_vocab, d)
        nn.init.normal_(self.dasar.weight, std=0.02)
        self.register_buffer("leluhur", leluhur)          # (V, L)
        self.register_buffer("leluhur_mask", leluhur_mask)  # (V, L)
        if aktif:
            self.kueri = nn.Linear(d, d, bias=False)
            self.kunci = nn.Linear(d, d, bias=False)

    def tabel(self) -> torch.Tensor:
        """Tabel embedding efektif, ukuran (V, d)."""
        if not self.aktif:
            return self.dasar.weight
        W = self.dasar.weight                       # (V, d)
        anc = self.dasar.weight[self.leluhur]       # (V, L, d)
        q = self.kueri(W).unsqueeze(1)              # (V, 1, d)
        k = self.kunci(anc)                         # (V, L, d)
        skor = (q * k).sum(-1) / math.sqrt(self.d)  # (V, L)
        skor = skor.masked_fill(~self.leluhur_mask, float("-inf"))
        a = torch.softmax(skor, dim=-1).unsqueeze(-1)
        return (a * anc).sum(1)

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        return F.embedding(idx, self.tabel())

    def pinalti_hierarki(self, contoh: int = 512) -> torch.Tensor:
        """Hukum pasangan bersaudara yang vektornya berjauhan.

        Bobotnya kecil dan diuji lewat ablasi. Kalau tidak ada bedanya,
        komponen ini dibuang dan kami tulis bahwa dibuang.
        """
        if not self.aktif:
            return torch.zeros((), device=self.dasar.weight.device)
        V = self.dasar.weight.shape[0]
        i = torch.randint(0, V, (contoh,), device=self.dasar.weight.device)
        induk = self.leluhur[i, 1]                  # leluhur terdekat
        W = self.tabel()
        jarak = (W[i] - W[induk]).pow(2).sum(-1)
        return jarak.mean()


class PerhatianBerbidang(nn.Module):
    """Perhatian diri dengan bias yang bergantung pada pasangan bidang.

    Hubungan antar-bidang tidak setara. Tarif harus sangat memperhatikan
    diagnosis dan prosedur. Diagnosis harus sangat memperhatikan laboratorium
    dan obat. Waktu hampir tidak perlu memperhatikan obat. Transformer biasa
    harus mempelajari semua itu dari nol lewat data. Memberi bias per pasangan
    bidang memberi model titik awal yang benar dan menghemat data.

    Biayanya dua belas kali dua belas kali jumlah kepala per lapis, sekitar
    seribu parameter per lapis. Nyaris gratis. Kebaruannya kecil, karena bias
    pada skor perhatian sudah dipakai pada perhatian berposisi relatif. Yang
    kami klaim hanya penerapannya pada bidang klaim.
    """

    def __init__(self, d: int, n_kepala: int, pakai_bias_bidang: bool = True):
        super().__init__()
        assert d % n_kepala == 0
        self.h = n_kepala
        self.dk = d // n_kepala
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.out = nn.Linear(d, d, bias=False)
        self.pakai_bias_bidang = pakai_bias_bidang
        if pakai_bias_bidang:
            self.bias_bidang = nn.Parameter(
                torch.zeros(n_kepala, N_FIELDS, N_FIELDS))

    def forward(self, x: torch.Tensor, fld: torch.Tensor,
                pad_mask: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape
        qkv = self.qkv(x).view(B, T, 3, self.h, self.dk).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]                 # (B, h, T, dk)
        skor = (q @ k.transpose(-2, -1)) / math.sqrt(self.dk)   # (B, h, T, T)

        if self.pakai_bias_bidang:
            # bias[b, h, i, j] = bias_bidang[h, fld[b,i], fld[b,j]]
            # Diambil lewat satu index_select pada tabel yang diratakan.
            # Cara ini jauh lebih murah daripada expand lalu gather, yang
            # sempat memakan lebih dari separuh waktu satu langkah.
            fi = fld.long()
            pasangan = (fi[:, :, None] * N_FIELDS + fi[:, None, :]).reshape(-1)
            rata = self.bias_bidang.reshape(self.h, -1)          # (h, F*F)
            b = rata.index_select(1, pasangan).view(self.h, B, T, T)
            skor = skor + b.permute(1, 0, 2, 3)

        skor = skor.masked_fill(~pad_mask[:, None, None, :], float("-inf"))
        a = torch.softmax(skor, dim=-1)
        y = (a @ v).transpose(1, 2).reshape(B, T, D)
        return self.out(y)


class Blok(nn.Module):
    """Satu lapis encoder. Normalisasi diletakkan sebelum sub-lapis."""

    def __init__(self, d: int, n_kepala: int, d_ff: int, dropout: float,
                 pakai_bias_bidang: bool):
        super().__init__()
        self.n1 = nn.LayerNorm(d)
        self.att = PerhatianBerbidang(d, n_kepala, pakai_bias_bidang)
        self.n2 = nn.LayerNorm(d)
        self.ff = nn.Sequential(
            nn.Linear(d, d_ff), nn.GELU(), nn.Linear(d_ff, d))
        self.drop = nn.Dropout(dropout)

    def forward(self, x, fld, pad_mask):
        x = x + self.drop(self.att(self.n1(x), fld, pad_mask))
        x = x + self.drop(self.ff(self.n2(x)))
        return x


class WaktuKontinu(nn.Module):
    """Penyandian selisih hari, bukan posisi ke berapa.

    Posisi ke berapa sebuah kejadian tidak penting. Yang penting berapa hari
    jaraknya. Readmisi hari kedua dan readmisi hari kesembilan puluh menempati
    posisi yang sama dalam barisan tapi artinya berlawanan.

    Skala logaritma dipakai karena selisih satu hari dan tiga hari berbeda
    besar maknanya, sedangkan tiga ratus dan tiga ratus tiga hampir sama.
    """

    def __init__(self, d: int, n_frek: int = 8):
        super().__init__()
        self.n_frek = n_frek
        self.proj = nn.Linear(2 * n_frek, d)
        self.register_buffer(
            "frek", torch.exp(torch.linspace(0.0, 3.0, n_frek)))

    def forward(self, dhari: torch.Tensor) -> torch.Tensor:
        t = torch.log1p(dhari.clamp(min=0).float()).unsqueeze(-1)  # (B, 1)
        a = t * self.frek
        return self.proj(torch.cat([torch.sin(a), torch.cos(a)], dim=-1))


class Nalar(nn.Module):
    """Tulang punggung ditambah kepala rekonstruksi."""

    def __init__(self, n_vocab: int, leluhur, leluhur_mask,
                 d: int = 256, n_lapis: int = 8, n_kepala: int = 8,
                 d_ff: int = 1024, dropout: float = 0.1,
                 pakai_ontologi: bool = True, pakai_bias_bidang: bool = True,
                 pakai_waktu: bool = True):
        super().__init__()
        self.d = d
        self.emb = EmbeddingOntologi(n_vocab, d, leluhur, leluhur_mask,
                                     aktif=pakai_ontologi)
        self.emb_bidang = nn.Embedding(N_FIELDS, d)
        self.pakai_waktu = pakai_waktu
        if pakai_waktu:
            self.waktu = WaktuKontinu(d)
        self.blok = nn.ModuleList([
            Blok(d, n_kepala, d_ff, dropout, pakai_bias_bidang)
            for _ in range(n_lapis)])
        self.norm = nn.LayerNorm(d)
        # Kepala rekonstruksi memakai tabel embedding yang sama dengan
        # masukan, yaitu tabel yang sudah dirakit dari leluhur. Mengikatnya
        # ke tabel dasar akan membuat model menebak memakai representasi yang
        # berbeda dari yang ia baca, dan itu keliru.
        self.drop = nn.Dropout(dropout)

    def encode(self, tok, fld, dhari=None):
        pad_mask = tok != 0                       # 0 adalah [PAD]
        x = self.emb(tok) + self.emb_bidang(fld.long())
        if self.pakai_waktu and dhari is not None:
            x = x + self.waktu(dhari).unsqueeze(1)
        x = self.drop(x)
        for b in self.blok:
            x = b(x, fld, pad_mask)
        return self.norm(x), pad_mask

    def forward(self, tok, fld, dhari=None, posisi=None):
        """posisi berupa mask boolean. Bila diberikan, kepala rekonstruksi
        hanya dihitung di posisi itu.

        Proyeksi keluaran ke seluruh kamus adalah operasi termahal di model
        ini. Saat pralatih, yang ditutup hanya sebagian kecil token, jadi
        menghitungnya di seluruh posisi membuang sebagian besar waktu.
        """
        h, pad_mask = self.encode(tok, fld, dhari)
        W = self.emb.tabel()
        if posisi is None:
            return h @ W.t(), h, pad_mask
        return h[posisi] @ W.t(), h, pad_mask

    def jumlah_parameter(self) -> int:
        return sum(p.numel() for p in self.parameters())
