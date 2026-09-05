"""Percobaan ujung ke ujung: dari klaim sintetis sampai peringkat audit.

Ini gerbang keputusan Fase 0 pada rancangan. Pertanyaannya bukan apakah
angkanya bagus, tapi apakah alurnya berjalan dan apakah model mengalahkan
mesin aturan. Kalau tidak mengalahkan, itu yang dilaporkan.

Jalankan:
    python scripts/percobaan.py --peserta 8000 --langkah 350
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nalar import kalibrasi, metrik  # noqa: E402
from nalar.dataset import (bangun_array, bangun_meta,  # noqa: E402
                           pisah_menurut_entitas)
from nalar.generator import Pembangkit  # noqa: E402
from nalar.heads import (TabelBarang, TabelTarif,  # noqa: E402
                         divergensi_sebaya, kemiripan_berlebih, kmeans,
                         normalkan_terhadap_sejenis, sebaran_harapan,
                         selisih_tagihan, selisih_tarif, skor_kejutan,
                         wakil_faskes)
from nalar.konformal import Kalibrator, periksa_jaminan  # noqa: E402
from nalar.pembanding import (RegresiLogistik, fitur_tangan,  # noqa: E402
                              mesin_aturan)
from nalar.tokenizer import Penoken  # noqa: E402
from nalar.train import perangkat, pralatih  # noqa: E402
from nalar.vocab import Kamus  # noqa: E402


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--peserta", type=int, default=8000)
    ap.add_argument("--tahun", type=int, default=3)
    ap.add_argument("--fktp", type=int, default=300)
    ap.add_argument("--fkrtl", type=int, default=50)
    ap.add_argument("--langkah", type=int, default=350)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--d", type=int, default=128)
    ap.add_argument("--lapis", type=int, default=4)
    ap.add_argument("--kepala", type=int, default=4)
    ap.add_argument("--dff", type=int, default=384)
    ap.add_argument("--utas", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--keluaran", default="runs/percobaan.json")
    ap.add_argument("--tarif-cadangan", action="store_true",
                    help="pakai tarif tebakan, bukan tabel resmi. Untuk ablasi.")
    a = ap.parse_args()

    torch.set_num_threads(a.utas)
    if getattr(a, "tarif_cadangan", False):
        # Ablasi: matikan tabel resmi dengan mengarahkan berkasnya ke jalur
        # yang tidak ada, sehingga seluruh alur jatuh ke tarif tebakan.
        from nalar import tarif_resmi as _tr
        _tr.CSV_TARIF = os.path.join(AKAR_PALSU := "", "tidak_ada.csv")
        _tr._muat.cache_clear()
        _tr._cadangan_per_kode.cache_clear()
        _tr.kode_tersedia.cache_clear()
        print("[ablasi] tabel tarif resmi dimatikan, memakai tarif tebakan",
              flush=True)
    t_mulai = time.time()
    catatan: dict = {"pengaturan": vars(a)}

    # --- 1. data ----------------------------------------------------------
    print("[1] membangkitkan data", flush=True)
    t = time.time()
    g = Pembangkit(n_peserta=a.peserta, tahun=a.tahun, seed=a.seed,
                   n_fktp=a.fktp, n_fkrtl=a.fkrtl)
    eps = g.jalankan()
    print(f"    {len(eps)} episode dalam {time.time() - t:.0f}s", flush=True)
    catatan["data"] = {
        "n_episode": len(eps),
        "n_peserta": a.peserta,
        "n_fktp": g.jaringan.n_fktp,
        "n_fkrtl": g.jaringan.n_fkrtl,
        "faktor_kompresi_peserta_per_faskes": g.jaringan.faktor_kompresi,
        "uji_kecocokan_agregat": kalibrasi.laporan(eps, a.peserta, a.tahun),
    }
    curang = np.array([1 if r["modus"] else 0 for r in eps])
    selisih = np.array([max(r["selisih_rp"], 0) for r in eps], dtype=np.float64)
    total_tagih = sum(r["tarif"] + r.get("tagih_bhp", 0) for r in eps)
    catatan["data"]["porsi_klaim_terpengaruh"] = round(float(curang.mean()), 4)
    catatan["data"]["porsi_nilai_terpengaruh"] = round(
        float(selisih.sum() / max(total_tagih, 1)), 4)

    # --- 2. penokenan -----------------------------------------------------
    print("[2] menokenkan", flush=True)
    V = Kamus()
    pen = Penoken(V,
                  Penoken.pelajari_tepi([r["tarif"] for r in eps]),
                  Penoken.pelajari_tepi([r.get("tagih_bhp", 0) for r in eps]))
    arr = bangun_array(eps, pen)
    meta = bangun_meta(eps)
    catatan["kamus"] = {"ukuran": len(V),
                        "panjang_rerata": float(arr["pjg"].mean()),
                        "panjang_maks": int(arr["pjg"].max())}

    # --- 3. pemisahan menurut entitas -------------------------------------
    m_tr, m_te = pisah_menurut_entitas(meta, frac_uji=0.25, seed=a.seed)
    idx_tr, idx_te = np.flatnonzero(m_tr), np.flatnonzero(m_te)
    # sebagian latih disisihkan untuk kalibrasi konformal
    rng = np.random.default_rng(a.seed)
    rng.shuffle(idx_tr)
    n_kal = min(6000, len(idx_tr) // 5)
    idx_kal, idx_latih = idx_tr[:n_kal], idx_tr[n_kal:]
    print(f"    latih {len(idx_latih)} | kalibrasi {len(idx_kal)} "
          f"| uji {len(idx_te)}", flush=True)
    catatan["pemisahan"] = {"cara": "menurut faskes, bukan acak per klaim",
                            "n_latih": len(idx_latih), "n_kalibrasi": len(idx_kal),
                            "n_uji": len(idx_te)}

    # --- 4. pralatih ------------------------------------------------------
    print("[3] pralatih tulang punggung, tanpa satu pun label kecurangan",
          flush=True)
    dev = perangkat()
    cfg = dict(d=a.d, n_lapis=a.lapis, n_kepala=a.kepala, d_ff=a.dff,
               batch=a.batch, langkah=a.langkah, lr=4e-4, seed=a.seed)
    model, riwayat = pralatih(V, arr, idx_latih, idx_kal, cfg, dev,
                              log_setiap=max(25, a.langkah // 8),
                              jalur_simpan="runs/nalar.pt")
    catatan["pralatih"] = {
        "perangkat": str(dev),
        "parameter_juta": round(model.jumlah_parameter() / 1e6, 3),
        "riwayat": riwayat,
        "rugi_awal": riwayat[0]["rugi_valid"] if riwayat else None,
        "rugi_akhir": riwayat[-1]["rugi_valid"] if riwayat else None,
    }

    # --- 5. kepala hilir --------------------------------------------------
    print("[4] menskor dengan kepala K1 dan K2", flush=True)
    t = time.time()
    k1_mentah = skor_kejutan(model, V, arr, idx_te, ["TRF"], dev)
    kunci_sejenis = np.array([f"{eps[i]['dxp']}|{eps[i]['rawat_inap']}"
                              for i in idx_te])
    k1 = normalkan_terhadap_sejenis(k1_mentah, kunci_sejenis)

    tabel = TabelTarif(V, eps)
    k2_selisih, k2_harapan, k2_yakin, p_salah, sel_salah = selisih_tarif(
        model, V, arr, idx_te, eps, tabel, dev)
    print(f"    selesai dalam {time.time() - t:.0f}s", flush=True)

    # K7 konsistensi tagihan bahan habis pakai. Ditambahkan setelah pembedahan
    # kebenaran dasar menunjukkan upcoding hanya dua belas persen selisih
    # rupiah, sedangkan barang fiktif dan harga digelembungkan bersama lima
    # puluh tiga persen dan tidak terlihat kepala mana pun.
    print("[4b] kepala K7 konsistensi tagihan", flush=True)
    barang = TabelBarang(V)
    k7_selisih, k7_harapan = selisih_tagihan(model, V, arr, idx_te, eps,
                                             barang, dev)

    # Skor gabungan: peluang kelompok yang ditagihkan salah, dikali selisih
    # rupiah bila memang salah. Percobaan pertama memakai perkalian persentil
    # kejutan dengan selisih, dan itu lebih buruk daripada selisih saja karena
    # peluangnya sudah terkandung di dalam nilai harapan.
    skor_nalar = p_salah * np.clip(sel_salah, 0, None)

    # --- 6. pembanding ----------------------------------------------------
    print("[5] menjalankan pembanding", flush=True)
    eps_te = [eps[i] for i in idx_te]
    skor_aturan, alasan = mesin_aturan(eps_te)

    X_tr = fitur_tangan([eps[i] for i in idx_latih])
    X_te = fitur_tangan(eps_te)
    y_tr = curang[idx_latih]
    reg = RegresiLogistik().fit(X_tr, y_tr)
    skor_reg = reg.skor(X_te) * np.maximum(
        [r["tarif"] + r.get("tagih_bhp", 0) for r in eps_te], 1)

    # --- 7. metrik --------------------------------------------------------
    sel_te = selisih[idx_te]
    cur_te = curang[idx_te]
    daftar_k = [50, 100, 250, 500, 1000]
    daftar_k = [k for k in daftar_k if k <= len(idx_te)]

    penskor = {
        "nalar": skor_nalar,
        "nalar_k1_saja": k1,
        "nalar_k2_saja": np.clip(k2_selisih, 0, None),
        "nalar_gabungan_lama": k1 * np.clip(k2_selisih, 0, None),
        "mesin_aturan": skor_aturan,
        "regresi_logistik": skor_reg,
        "nalar_k7_saja": np.clip(k7_selisih, 0, None),
        "nilai_klaim": np.array(
            [r["tarif"] + r.get("tagih_bhp", 0) for r in eps_te],
            dtype=np.float64),
        "acak": rng.random(len(idx_te)),
    }
    hasil = metrik.kurva(penskor, sel_te, cur_te, daftar_k)
    for nama in ("nalar", "nalar_k2_saja", "regresi_logistik",
                 "nilai_klaim"):
        hasil[nama]["peningkatan_atas_aturan"] = metrik.peningkatan_atas(
            hasil, nama, "mesin_aturan", daftar_k)
    hasil["_total_selisih_tersedia"] = round(float(sel_te.sum()))
    hasil["_n_uji"] = len(idx_te)
    catatan["metrik"] = hasil

    # --- 8. kalibrasi konformal -------------------------------------------
    print("[6] kalibrasi konformal", flush=True)
    k1_kal_mentah = skor_kejutan(model, V, arr, idx_kal, ["TRF"], dev)
    kunci_kal = np.array([f"{eps[i]['dxp']}|{eps[i]['rawat_inap']}"
                          for i in idx_kal])
    k1_kal = normalkan_terhadap_sejenis(k1_kal_mentah, kunci_kal)
    _, _, _, ps_kal, ss_kal = selisih_tarif(model, V, arr, idx_kal, eps,
                                            tabel, dev)
    skor_kal = ps_kal * np.clip(ss_kal, 0, None)

    kel_kal = np.array([eps[i]["f_kelas"] for i in idx_kal])
    kel_te = np.array([r["f_kelas"] for r in eps_te])
    hasil_konformal = {}
    for alpha in (0.01, 0.02, 0.05):
        kal = Kalibrator(alpha=alpha).pasang(skor_kal, kel_kal)
        hasil_konformal[str(alpha)] = periksa_jaminan(
            skor_nalar, cur_te == 0, kal, kel_te)
    catatan["konformal"] = hasil_konformal

    # --- 9. keadilan ------------------------------------------------------
    kal = Kalibrator(alpha=0.02).pasang(skor_kal, kel_kal)
    tanda = kal.tandai(skor_nalar, kel_te)
    catatan["keadilan"] = {
        "menurut_kelas_faskes": metrik.keadilan_kelompok(
            tanda, kel_te, cur_te == 0),
        "menurut_daerah_tertinggal": metrik.keadilan_kelompok(
            tanda, np.array([r["f_dtpk"] for r in eps_te]), cur_te == 0),
    }

    # --- 10. kalibrasi selisih dan K5 -------------------------------------
    catatan["kalibrasi_selisih_k2"] = metrik.kalibrasi_selisih(
        k2_selisih, sel_te)

    print("[7] kepala K5 kemiripan berlebih", flush=True)
    skor_k5, dasar = kemiripan_berlebih(eps, idx_te, seed=a.seed)
    keb = {int(f): int(g.kebijakan.rs[f]) for f in skor_k5}
    urut = sorted(skor_k5.items(), key=lambda kv: -kv[1]["kelebihan"])[:10]
    catatan["k5_kemiripan"] = {
        "dasar_median": round(dasar, 4),
        "sepuluh_teratas": [
            dict(faskes=int(f), kelebihan=round(v["kelebihan"], 4),
                 n_klaim=v["n"], kebijakan_sebenarnya=keb.get(int(f)))
            for f, v in urut],
    }
    nakal = [1 if keb.get(int(f), 0) > 0 else 0 for f, _ in urut]
    catatan["k5_kemiripan"]["presisi_sepuluh_teratas"] = (
        round(float(np.mean(nakal)), 3) if nakal else None)

    # --- 11. kepala K4 kelompok sebaya -----------------------------------
    print("[8] kepala K4 kelompok sebaya", flush=True)
    faskes_list, Xf, n_klaim = wakil_faskes(model, V, arr, idx_te, eps, dev)
    if len(faskes_list) >= 6:
        k = max(2, min(5, len(faskes_list) // 4))
        label, _ = kmeans(Xf, k, seed=a.seed)
        harapan = sebaran_harapan(model, V, arr, idx_te, tabel, dev)
        div = divergensi_sebaya(eps, idx_te, tabel, harapan, faskes_list,
                                label, selisih_klaim=np.clip(k2_selisih, 0, None))
        urut4 = sorted(div.items(), key=lambda kv: -kv[1]["skor_relatif"])[:10]
        keb_rs = {int(f): int(g.kebijakan.rs[f]) for f in div}
        catatan["k4_sebaya"] = {
            "n_faskes_dinilai": len(div),
            "n_kelompok_sebaya": int(k),
            "sepuluh_teratas": [
                dict(faskes=int(f), skor_relatif=v["skor_relatif"],
                     js_relatif=v["js_relatif"], n_klaim=v["n"],
                     kelebihan_per_klaim_rp=v["kelebihan_per_klaim_rp"],
                     kelompok=v["kelompok"],
                     perkiraan_kelebihan_rp=v["perkiraan_kelebihan_rp"],
                     kebijakan_sebenarnya=keb_rs.get(int(f)))
                for f, v in urut4],
        }
        nakal4 = [1 if keb_rs.get(int(f), 0) > 0 else 0 for f, _ in urut4]
        catatan["k4_sebaya"]["presisi_sepuluh_teratas"] = (
            round(float(np.mean(nakal4)), 3) if nakal4 else None)
        # berapa porsi faskes nakal yang ada di daftar peringkat teratas
        semua_nakal = sum(1 for f in div if keb_rs.get(int(f), 0) > 0)
        catatan["k4_sebaya"]["n_faskes_nakal_sebenarnya"] = semua_nakal
    else:
        catatan["k4_sebaya"] = {
            "status": "dilewat, faskes pada himpunan uji terlalu sedikit",
            "n_faskes": len(faskes_list)}

    # --- 11b. kepala K3 integritas episode -------------------------------
    print("[8b] kepala K3 integritas episode", flush=True)
    from nalar import tpp

    a_tr, d_tr, m_tr, ada_tr = tpp.susun_pasangan(eps, idx_latih)
    H_tr = tpp.representasi(model, arr, a_tr, dev)
    kepala_waktu = tpp.KepalaWaktu(H_tr.shape[1]).to(dev)
    riwayat_k3 = tpp.latih(kepala_waktu, H_tr, d_tr, m_tr, ada_tr, dev,
                           langkah=500, seed=a.seed)

    a_te, d_te, m_te, ada_te = tpp.susun_pasangan(eps, idx_te)
    H_te = tpp.representasi(model, arr, a_te, dev)
    p_lama = kepala_waktu.peluang_lebih_lama(
        H_te.to(dev), torch.from_numpy(d_te).to(dev))
    p_tanda = kepala_waktu.peluang_tanda(H_te.to(dev))

    # Skor K3 dalam rupiah, satuan yang sama dengan K2 supaya bisa
    # diperingkat bersama. Peluang pasangan ini sebenarnya satu episode,
    # dikali rupiah yang didapat dari memecahnya.
    posisi_te = {int(i): j for j, i in enumerate(idx_te)}
    skor_k3 = np.zeros(len(idx_te), dtype=np.float64)
    urut_pasien: dict[int, list[int]] = {}
    for i in idx_te:
        urut_pasien.setdefault(int(eps[i]["peserta_id"]), []).append(int(i))
    for daftar in urut_pasien.values():
        daftar.sort(key=lambda i: eps[i]["hari"])
    berikut = {}
    for daftar in urut_pasien.values():
        for x, y in zip(daftar, daftar[1:]):
            berikut[x] = y
    for j, i in enumerate(a_te):
        if ada_te[j] != 1:
            continue
        b_ = berikut.get(int(i))
        if b_ is None:
            continue
        rp = tpp.rupiah_dipertaruhkan(eps, int(i), b_)
        if rp <= 0:
            continue
        peluang = float(p_lama[j]) * float(p_tanda[j][tpp.TANDA_LANJUT])
        k = posisi_te.get(int(i))
        if k is not None:
            skor_k3[k] = peluang * rp

    catatan["k3_waktu"] = {
        "riwayat_rugi": riwayat_k3,
        "n_pasangan_latih": int(len(a_tr)),
        "n_pasangan_uji": int(len(a_te)),
        "n_klaim_berskor": int((skor_k3 > 0).sum()),
        "rupiah_tertimbang_total": round(float(skor_k3.sum())),
    }

    # --- 12. pelaku yang beradaptasi -------------------------------------
    print("[9] pelaku yang beradaptasi", flush=True)
    from nalar.adversarial import bandingkan as bandingkan_pelaku

    tabel_lokal = tabel

    def penskor_klaim(daftar):
        """Skor NALAR untuk sekumpulan klaim yang belum ada di array."""
        a = bangun_array(daftar, pen)
        ix = np.arange(len(daftar))
        k1x = skor_kejutan(model, V, a, ix, ["TRF"], dev)
        kun = np.array([f"{r['dxp']}|{r['rawat_inap']}" for r in daftar])
        k1n = normalkan_terhadap_sejenis(k1x, kun)
        _, _, _, psx, ssx = selisih_tarif(model, V, a, ix, daftar,
                                          tabel_lokal, dev)
        return psx * np.clip(ssx, 0, None)

    kal2 = Kalibrator(alpha=0.02).pasang(skor_kal, kel_kal)
    catatan["adversarial"] = bandingkan_pelaku(
        eps, idx_te, penskor_klaim, kal2.ambang_global, seed=a.seed)

    # metrik ulang dengan K3 ikut serta
    penskor2 = dict(penskor)
    penskor2["nalar_k3_saja"] = skor_k3
    penskor2["nalar_k2_plus_k3"] = skor_nalar + skor_k3
    penskor2["nalar_semua"] = (skor_nalar + skor_k3
                               + np.clip(k7_selisih, 0, None))
    hasil2 = metrik.kurva(penskor2, sel_te, cur_te, daftar_k)
    for nama in ("nalar_k3_saja", "nalar_k2_plus_k3", "nalar_semua"):
        hasil2[nama]["peningkatan_atas_aturan"] = metrik.peningkatan_atas(
            hasil2, nama, "mesin_aturan", daftar_k)
        # Peningkatan atas garis dasar urutkan menurut nilai klaim. Inilah
        # pembanding yang paling jujur untuk sistem yang keluarannya rupiah,
        # karena mengurutkan klaim termahal lebih dulu itu gratis dan tidak
        # butuh model sama sekali.
        hasil2[nama]["peningkatan_atas_nilai_klaim"] = metrik.peningkatan_atas(
            hasil2, nama, "nilai_klaim", daftar_k)
    catatan["metrik_dengan_k3"] = {
        k: v for k, v in hasil2.items()
        if k in ("nalar", "nalar_k3_saja", "nalar_k2_plus_k3", "nalar_semua",
                 "nalar_k7_saja", "mesin_aturan", "regresi_logistik",
                 "nilai_klaim")}

    # --- 13. keadilan per kepala, dan pada skor yang sebenarnya dipakai ---
    # Pengukuran keadilan sebelumnya hanya memakai skor K2, bukan skor
    # gabungan yang akan benar benar dipasang. Itu keliru dua arah: yang
    # dilaporkan bukan yang dipakai, dan ketimpangannya tidak bisa
    # diatribusikan ke kepala mana.
    print("[10] keadilan per kepala", flush=True)
    skor_semua = skor_nalar + skor_k3 + np.clip(k7_selisih, 0, None)
    for nama_kel, kel in (("kelas_faskes", kel_te),
                          ("daerah_tertinggal",
                           np.array([r["f_dtpk"] for r in eps_te]))):
        catatan.setdefault("keadilan_per_kepala", {})[nama_kel] =             metrik.urai_keadilan(
                {"K2": skor_nalar,
                 "K3": skor_k3,
                 "K7": np.clip(k7_selisih, 0, None),
                 "semua": skor_semua,
                 "nilai_klaim": penskor["nilai_klaim"],
                 "mesin_aturan": skor_aturan},
                kel, cur_te == 0, porsi=0.02)

    catatan["waktu_total_detik"] = round(time.time() - t_mulai, 1)
    os.makedirs(os.path.dirname(a.keluaran), exist_ok=True)
    with open(a.keluaran, "w", encoding="utf-8") as f:
        json.dump(catatan, f, indent=1, ensure_ascii=False)
    print(f"\nditulis ke {a.keluaran} ({catatan['waktu_total_detik']}s)")

    # ringkasan singkat ke layar
    print("\n=== RINGKAS ===")
    k = daftar_k[-1]
    for nama in ("nalar", "mesin_aturan", "regresi_logistik", "acak"):
        print(f"  {nama:20s} rupiah@{k}: "
              f"Rp {hasil[nama]['rupiah_pada_k'][k]/1e6:10.1f} juta   "
              f"presisi {hasil[nama]['presisi_pada_k'][k]:.3f}")
    print(f"  peningkatan nalar atas aturan: "
          f"{hasil['nalar']['peningkatan_atas_aturan']}")
    h2 = catatan["metrik_dengan_k3"]
    print(f"  K3 saja rupiah@{k}: "
          f"Rp {h2['nalar_k3_saja']['rupiah_pada_k'][k]/1e6:.1f} juta")
    print(f"  nilai klaim saja rupiah@{k}: "
          f"Rp {hasil['nilai_klaim']['rupiah_pada_k'][k]/1e6:.1f} juta")
    print(f"  K2+K3   rupiah@{k}: "
          f"Rp {h2['nalar_k2_plus_k3']['rupiah_pada_k'][k]/1e6:.1f} juta   "
          f"peningkatan atas aturan {h2['nalar_k2_plus_k3']['peningkatan_atas_aturan']}")
    print(f"  K7 saja rupiah@{k}: "
          f"Rp {hasil['nalar_k7_saja']['rupiah_pada_k'][k]/1e6:.1f} juta")
    print(f"  SEMUA   rupiah@{k}: "
          f"Rp {h2['nalar_semua']['rupiah_pada_k'][k]/1e6:.1f} juta")
    print(f"  SEMUA lift atas aturan     : "
          f"{h2['nalar_semua']['peningkatan_atas_aturan']}")
    print(f"  SEMUA lift atas nilai klaim: "
          f"{h2['nalar_semua']['peningkatan_atas_nilai_klaim']}")


if __name__ == "__main__":
    utama()
