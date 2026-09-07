-- Tabel berkas, isi mentah satu klaim seperti yang dikembalikan alat.
--
-- Alasannya satu dan sempit. Alat ambil_berkas membaca keadaan data di
-- dalam memori, dan keadaan itu menuntut proses Python besar yang tidak
-- muat di fungsi tanpa peladen. Tanpa tabel ini, Agen Berkas cuma bisa
-- jalan di mesin yang menyalakan peladen.
--
-- Medannya sengaja sama persis dengan keluaran alat, bukan disederhanakan.
-- Menyederhanakannya berarti mengubah apa yang dilihat model, dan seluruh
-- angka yang sudah diukur pada lima ratus berkas jadi tidak berlaku lagi.
-- Tabel yang lebih gemuk lebih murah daripada pengukuran ulang.
--
-- Terpisah dari tabel klaim dengan sengaja. Tabel klaim melayani layar dan
-- dibaca portal fasilitas kesehatan. Tabel ini melayani alat agen, dan
-- isinya rekam medis ringkas yang tidak perlu sampai ke peramban faskes.
--
-- Pasang lewat SQL Editor Supabase, sekali saja.

create table if not exists nalar.berkas (
  id                    text primary key,
  faskes                text        not null,
  kelas_faskes          text        not null,
  regional              integer     not null,
  daerah_tertinggal     boolean     not null,
  kelompok_tarif        text        not null,
  diagnosis_utama       text        not null,
  n_prosedur            integer     not null,
  n_obat                integer     not null,
  pemeriksaan_lab       text[]      not null,
  n_bahan_habis_pakai   integer     not null,
  rawat_inap            boolean     not null,
  kelas_rawat           integer     not null,
  lama_rawat            integer     not null,
  hari                  integer     not null,
  tarif_ditagihkan_rp   bigint      not null,
  tagihan_barang_rp     bigint      not null,
  dibuat_pada           timestamptz not null default now()
);

comment on table nalar.berkas is
  'Isi mentah klaim untuk alat ambil_berkas, supaya agen bisa jalan tanpa keadaan data di memori.';

alter table nalar.berkas enable row level security;

-- Sama seperti tabel lain: siapa pun boleh membaca, tidak ada yang boleh
-- menulis lewat kunci publik. Yang menulis skrip pemuat dengan kunci
-- layanan, dan kunci itu tidak pernah sampai ke peramban.
drop policy if exists "baca berkas" on nalar.berkas;
create policy "baca berkas" on nalar.berkas for select using (true);
