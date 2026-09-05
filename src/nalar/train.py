"""Pralatih tulang punggung dengan penutupan menurut peran.

Tidak ada label kecurangan yang dipakai di sini. Sama sekali. Model hanya
belajar menebak isi klaim dari sisa isinya. Skor kecurangan lahir kemudian,
dari kesulitan menebak, bukan dari contoh kecurangan.
"""

from __future__ import annotations

import json
import math
import os
import time

import numpy as np
import torch

# Mesin pengembangan hanya punya memori 16 gigabyte dan tanpa kartu grafis
# yang terpasang untuk PyTorch. Memakai seluruh inti yang ada adalah satu
# satunya cara membuat percobaan cukup cepat untuk diiterasi.
torch.set_num_threads(max(1, (os.cpu_count() or 4)))

from .dataset import PenutupPeran
from .model import Nalar
from .schema import MASK, PAD


def perangkat() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def buat_model(kamus, cfg: dict, dev) -> Nalar:
    m, mask = kamus.matriks_leluhur()
    model = Nalar(
        n_vocab=len(kamus),
        leluhur=torch.from_numpy(m),
        leluhur_mask=torch.from_numpy(mask),
        d=cfg.get("d", 256),
        n_lapis=cfg.get("n_lapis", 8),
        n_kepala=cfg.get("n_kepala", 8),
        d_ff=cfg.get("d_ff", 1024),
        dropout=cfg.get("dropout", 0.1),
        pakai_ontologi=cfg.get("pakai_ontologi", True),
        pakai_bias_bidang=cfg.get("pakai_bias_bidang", True),
        pakai_waktu=cfg.get("pakai_waktu", True),
    ).to(dev)
    return model


def pralatih(kamus, arr, idx_latih, idx_valid, cfg=None, dev=None,
             log_setiap: int = 50, jalur_simpan: str | None = None):
    cfg = dict(cfg or {})
    dev = dev or perangkat()
    rng = np.random.default_rng(cfg.get("seed", 0))
    model = buat_model(kamus, cfg, dev)

    penanda_bid = {kamus.id(f"[BID:{f}]") for f in
                   __import__("nalar.schema", fromlist=["FIELDS"]).FIELDS}
    penutup = PenutupPeran(kamus.id(MASK), kamus.id(PAD), rng,
                           hanya_acak=cfg.get("hanya_penutupan_acak", False))

    batch = cfg.get("batch", 96)
    langkah = cfg.get("langkah", 1200)
    lr = cfg.get("lr", 3e-4)
    w_hier = cfg.get("bobot_pinalti_hierarki", 0.01)

    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4,
                            betas=(0.9, 0.98))
    pemanasan = max(1, int(0.06 * langkah))

    def lr_pada(t):
        if t < pemanasan:
            return lr * t / pemanasan
        p = (t - pemanasan) / max(1, langkah - pemanasan)
        return 1e-6 + 0.5 * (lr - 1e-6) * (1 + math.cos(math.pi * p))

    tok_a, fld_a, pjg_a, dh_a = (arr["tok"], arr["fld"], arr["pjg"],
                                 arr["dhari"])
    riwayat = []
    t0 = time.time()
    model.train()

    for t in range(1, langkah + 1):
        for g in opt.param_groups:
            g["lr"] = lr_pada(t)
        pilih = rng.choice(idx_latih, size=min(batch, len(idx_latih)),
                           replace=False)
        tok, sas, _ = penutup.terapkan(tok_a[pilih], fld_a[pilih],
                                       pjg_a[pilih], penanda_bid)
        tok_t = torch.from_numpy(tok.astype(np.int64)).to(dev)
        fld_t = torch.from_numpy(fld_a[pilih].astype(np.int64)).to(dev)
        dh_t = torch.from_numpy(dh_a[pilih].astype(np.int64)).to(dev)
        sas_t = torch.from_numpy(sas).to(dev)

        pos = sas_t != -100
        logit = model(tok_t, fld_t, dh_t, posisi=pos)[0]
        rugi = torch.nn.functional.cross_entropy(logit, sas_t[pos])
        total = rugi
        if w_hier > 0:
            total = total + w_hier * model.emb.pinalti_hierarki()

        opt.zero_grad(set_to_none=True)
        total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        if t % log_setiap == 0 or t == 1:
            v = evaluasi_rugi(model, kamus, arr, idx_valid, penutup,
                              penanda_bid, dev, rng, n_batch=6, batch=batch)
            riwayat.append(dict(langkah=t, rugi_latih=float(rugi.item()),
                                rugi_valid=v, detik=round(time.time() - t0, 1)))
            print(f"  langkah {t:5d}  rugi latih {rugi.item():.4f}  "
                  f"rugi valid {v:.4f}  {time.time() - t0:.0f}s", flush=True)
            model.train()

    if jalur_simpan:
        os.makedirs(os.path.dirname(jalur_simpan), exist_ok=True)
        torch.save({"model": model.state_dict(), "cfg": cfg}, jalur_simpan)
        with open(jalur_simpan.replace(".pt", "_riwayat.json"), "w") as f:
            json.dump(riwayat, f, indent=1)
    return model, riwayat


@torch.no_grad()
def evaluasi_rugi(model, kamus, arr, idx, penutup, penanda_bid, dev, rng,
                  n_batch=6, batch=96):
    model.eval()
    total, n = 0.0, 0
    for _ in range(n_batch):
        pilih = rng.choice(idx, size=min(batch, len(idx)), replace=False)
        tok, sas, _ = penutup.terapkan(arr["tok"][pilih], arr["fld"][pilih],
                                       arr["pjg"][pilih], penanda_bid)
        tok_t = torch.from_numpy(tok.astype(np.int64)).to(dev)
        fld_t = torch.from_numpy(arr["fld"][pilih].astype(np.int64)).to(dev)
        dh_t = torch.from_numpy(arr["dhari"][pilih].astype(np.int64)).to(dev)
        sas_t = torch.from_numpy(sas).to(dev)
        pos = sas_t != -100
        logit = model(tok_t, fld_t, dh_t, posisi=pos)[0]
        rugi = torch.nn.functional.cross_entropy(logit, sas_t[pos])
        total += float(rugi.item())
        n += 1
    return total / max(n, 1)
