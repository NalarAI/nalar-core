"""Mengukur seberapa sering agen di situs yang sudah terpasang berhasil.

Bukan mengukur ulang lapisan agennya. Yang diukur jalur yang benar benar
dipakai pengunjung: satu permintaan HTTP ke fungsi tanpa peladen, dengan
jatah model yang sebenarnya, dari luar.

Jedanya lima puluh lima detik. Jatah delapan ribu token per menit dan satu
berkas memakai sekitar tujuh ribu, jadi menembak lebih cepat berarti
mengukur batas lajunya, bukan mengukur agennya.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

ALAMAT = os.environ.get("ALAMAT_WEB", "https://nalar-six.vercel.app")
N = int(os.environ.get("N", "10"))
JEDA = float(os.environ.get("JEDA", "55"))


def db(jalur):
    u = os.environ["SUPABASE_URL"].rstrip("/")
    k = os.environ["SUPABASE_ANON"]
    r = urllib.request.Request(
        f"{u}/rest/v1/{jalur}",
        headers={
            "apikey": k,
            "Authorization": f"Bearer {k}",
            "Accept-Profile": "nalar",
            "User-Agent": "nalar/1.0",
        },
    )
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())


def minta(kid):
    r = urllib.request.Request(
        f"{ALAMAT}/api/perkara",
        data=json.dumps({"id": kid}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(r, timeout=90) as h:
        return json.loads(h.read().decode())


ids = [x["klaim_id"] for x in db(f"perkara?select=klaim_id&order=klaim_id&limit={N}")]
print(f"{len(ids)} berkas lewat {ALAMAT}, jeda {JEDA:.0f} detik\n")

baris = []
for i, kid in enumerate(ids, 1):
    t = time.time()
    try:
        d = minta(kid)
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        d = {"sumber": "galat", "sebab_mundur": str(e)}
    dt = time.time() - t
    sumber = d.get("sumber", "?")
    a1 = (d.get("a1") or {}).get("lulus")
    n_angka = (d.get("a1") or {}).get("n_angka_diperiksa", 0)
    sebab = (d.get("sebab_mundur") or "").strip()
    print(
        f"{i:3}/{len(ids)}  {kid}  {sumber:7} {dt:5.1f}s  a1={a1}  angka={n_angka}"
        + (f"  {sebab[:64]}" if sebab else "")
    )
    sys.stdout.flush()
    baris.append({"id": kid, "sumber": sumber, "detik": dt, "sebab": sebab, "a1": a1})
    if i < len(ids):
        time.sleep(JEDA)

n_agen = sum(1 for b in baris if b["sumber"] == "agen")
n_a1 = sum(1 for b in baris if b["a1"])
sebab = {}
for b in baris:
    if b["sumber"] != "agen":
        k = (
            "jatah model habis"
            if "429" in b["sebab"] or "Too Many" in b["sebab"]
            else "angka kurang"
            if "angka" in b["sebab"]
            else "saringan"
            if "saringan" in b["sebab"]
            else "lain"
        )
        sebab[k] = sebab.get(k, 0) + 1

print()
print("=" * 62)
print(f"disusun agen        : {n_agen}/{len(baris)}")
print(f"A1 lulus            : {n_a1}/{len(baris)}")
print(f"lama rata rata      : {sum(b['detik'] for b in baris) / len(baris):.1f} detik")
for k, v in sorted(sebab.items(), key=lambda x: -x[1]):
    print(f"  mundur, {k:18}: {v}")

jalur = os.environ.get("KELUAR", "runs/ukur_hidup.json")
os.makedirs(os.path.dirname(jalur) or ".", exist_ok=True)
with open(jalur, "w", encoding="utf-8") as f:
    json.dump(
        {"alamat": ALAMAT, "n": len(baris), "n_agen": n_agen, "baris": baris},
        f,
        ensure_ascii=False,
        indent=2,
    )
print(f"\nRinciannya di {jalur}")
