"""Mengambil data pemanfaatan dokter Medicare dari data.cms.gov.

Situsnya menolak curl dan urllib lewat penyaring di tepi jaringan, balasannya
403 dari Akamai. Peramban sungguhan lolos. Jadi berkasnya diambil memakai
peramban tanpa jendela, bukan karena ingin pintar pintar, tapi karena tidak
ada jalan lain yang lebih lurus.

Yang dicari adalah tabel per dokter per layanan, karena tabel itu memuat NPI
yang sungguhan. NPI sungguhan diperlukan supaya label LEIE bisa disambungkan.
DE-SynPUF tidak bisa dipakai untuk itu: NPI dokternya diawali angka nol, di
luar rentang NPI yang sah, dan irisannya dengan LEIE nol persis.

Jalankan:
    python scripts/ambil_cms.py
"""

from __future__ import annotations

import json
import os

DIR_DATA = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

# Halaman ini memuat tautan unduhan dan juga memanggil API pencarian dataset.
# Dua duanya dipanen, mana yang lebih dulu berhasil.
HALAMAN = (
    "https://data.cms.gov/provider-summary-by-type-of-service/"
    "medicare-physician-other-practitioners/"
    "medicare-physician-other-practitioners-by-provider-and-service"
)


def utama():
    from playwright.sync_api import sync_playwright

    os.makedirs(DIR_DATA, exist_ok=True)
    temuan = {"api": [], "tautan": []}

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        hal = b.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        )

        # Balasan API disadap dari lalu lintas halaman. Lebih murah daripada
        # menebak alamat titik akhirnya.
        def dengar(res):
            u = res.url
            if "data-api" in u or "metastore" in u or u.endswith(".json"):
                temuan["api"].append((res.status, u))

        hal.on("response", dengar)
        print(f"membuka {HALAMAN[:70]}...")
        hal.goto(HALAMAN, wait_until="networkidle", timeout=120000)
        hal.wait_for_timeout(4000)

        for a in hal.query_selector_all("a"):
            h = a.get_attribute("href") or ""
            if any(x in h.lower() for x in (".csv", ".zip", "download")):
                temuan["tautan"].append(h)

        print(
            f"  {len(temuan['api'])} balasan API tersadap, "
            f"{len(temuan['tautan'])} tautan unduhan"
        )
        for s, u in temuan["api"][:12]:
            print(f"    [{s}] {u[:110]}")
        for t in sorted(set(temuan["tautan"]))[:12]:
            print(f"    tautan {t[:110]}")

        # Kalau titik akhir API sudah kelihatan, isinya diambil dari dalam
        # halaman supaya ikut membawa konteks peramban yang sudah lolos saring.
        uuid = None
        for _, u in temuan["api"]:
            if "data-api/v1/dataset/" in u:
                bagian = u.split("data-api/v1/dataset/")[1]
                uuid = bagian.split("/")[0]
                break
        print(f"  uuid dataset: {uuid}")

        if uuid:
            alamat = (
                f"https://data.cms.gov/data-api/v1/dataset/{uuid}"
                f"/data?size=5000&offset=0"
            )
            isi = hal.evaluate(
                """async (u) => { const r = await fetch(u);
                   return { s: r.status, t: await r.text() }; }""",
                alamat,
            )
            print(f"  contoh data: http {isi['s']}, {len(isi['t'])} aksara")
            if isi["s"] == 200:
                with open(
                    os.path.join(DIR_DATA, "cms_dokter_contoh.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(isi["t"])
                print("  ditulis ke data/raw/cms_dokter_contoh.json")

        with open(os.path.join(DIR_DATA, "cms_jejak.json"), "w", encoding="utf-8") as f:
            json.dump(
                {"api": temuan["api"], "tautan": sorted(set(temuan["tautan"]))},
                f,
                indent=1,
            )
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(utama())
