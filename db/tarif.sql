-- Tabel tarif resmi INA-CBG, salinan dari lampiran Permenkes 3 Tahun 2023.
--
-- Berkasnya sudah ikut di dalam paket Python, jadi peladen tidak perlu tabel
-- ini. Yang perlu fungsi tanpa peladen, karena ia tidak memuat paketnya dan
-- membawa berkas tujuh puluh tujuh ribu baris ke dalam fungsi berarti
-- memperlambat tiap pemanggilan dingin.
--
-- Dimuat utuh, bukan disaring sesuai klaim yang ada di peragaan. Menyaringnya
-- akan membuat alat cari_tarif menolak kode yang sebenarnya ada di lampiran,
-- dan penolakan palsu itu akan terbawa ke berkas perkara sebagai keterangan
-- bahwa tarifnya tidak tersedia.
--
-- Kuncinya sama dengan kunci di dalam kode: kode, regional, kelas rumah
-- sakit, dan kepemilikan. Kelas rawat tidak masuk kunci karena ketiganya
-- disimpan sebagai tiga kolom pada baris yang sama.
--
-- Pasang lewat SQL Editor Supabase, sekali saja.

create table if not exists nalar.tarif (
  kode          text    not null,
  regional      integer not null,
  kelas_rs      text    not null,
  kepemilikan   text    not null,
  tarif_kelas3  bigint  not null,
  tarif_kelas2  bigint  not null,
  tarif_kelas1  bigint  not null,
  primary key (kode, regional, kelas_rs, kepemilikan)
);

comment on table nalar.tarif is
  'Tarif INA-CBG Permenkes 3/2023, dipakai alat cari_tarif pada fungsi tanpa peladen.';

alter table nalar.tarif enable row level security;

drop policy if exists "baca tarif" on nalar.tarif;
create policy "baca tarif" on nalar.tarif for select using (true);
