-- Keluaran Agen Pola: perkara yang dibuka karena pola sebuah faskes bergeser.
--
-- Satu baris ringkasan selalu ada, dan daftar perkaranya boleh kosong. Kosong
-- adalah jawaban yang sah dan yang paling sering benar, jadi ia disimpan
-- sebagai keadaan, bukan sebagai ketiadaan baris. Tabel yang kosong tidak
-- bisa dibedakan dari agen yang belum pernah dijalankan.
--
-- Pasang lewat SQL Editor Supabase, sekali saja.

create table if not exists nalar.pola_ringkas (
  id                     integer primary key default 1,
  n_faskes_diuji         integer     not null,
  n_perkara              integer     not null,
  n_lolos_tanpa_koreksi  integer     not null,
  sebab_kosong           text        not null default '',
  fdr                    real        not null,
  batas_p                real        not null,
  minimal_klaim          integer     not null,
  dibuat_pada            timestamptz not null default now()
);

create table if not exists nalar.pola (
  faskes             text primary key,
  kelas_faskes       text        not null,
  hari_ganti         integer     not null,
  rata_sebelum_rp    bigint      not null,
  rata_sesudah_rp    bigint      not null,
  geser_rp           bigint      not null,
  p                  real        not null,
  n_klaim            integer     not null,
  n_sesudah          integer     not null,
  berkas_penyumbang  text[]      not null,
  catatan            text        not null
);

alter table nalar.pola_ringkas enable row level security;
alter table nalar.pola enable row level security;

drop policy if exists "baca pola ringkas" on nalar.pola_ringkas;
create policy "baca pola ringkas" on nalar.pola_ringkas
  for select to anon, authenticated using (true);

drop policy if exists "baca pola" on nalar.pola;
create policy "baca pola" on nalar.pola
  for select to anon, authenticated using (true);

grant select on nalar.pola_ringkas, nalar.pola to anon, authenticated;

-- Fungsi pengosong harus ikut menyebut keduanya, kalau tidak pemuatan
-- berikutnya bentrok kunci utama.
create or replace function nalar.kosongkan()
returns void
language plpgsql
security definer
set search_path = nalar, public
as $$
begin
  truncate table
    nalar.antrean,
    nalar.pengandaian,
    nalar.penjelasan,
    nalar.perkara,
    nalar.pola,
    nalar.pola_ringkas,
    nalar.penandaan,
    nalar.antrean_ringkas,
    nalar.ringkas,
    nalar.keadilan,
    nalar.profil_faskes,
    nalar.perubahan,
    nalar.pilihan,
    nalar.terbitan,
    nalar.klaim
  cascade;
end;
$$;
