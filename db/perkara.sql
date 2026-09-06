-- Tabel berkas perkara, keluaran lapisan agen untuk verifikator.
--
-- Ini berkas skema pertama yang masuk repositori. Tabel yang lebih dulu ada
-- dibuat lewat papan Supabase dan tidak pernah tertulis di mana pun, dan itu
-- kesalahan yang tidak diulang di sini: skema yang hanya hidup di papan tidak
-- bisa ditinjau, tidak bisa dibalik, dan tidak bisa dipasang ulang oleh orang
-- yang bukan pembuatnya.
--
-- Terpisah dari tabel penjelasan dengan sengaja. Portal fasilitas kesehatan
-- membaca penjelasan, jadi apa pun yang ditaruh di sana sampai ke peramban
-- pihak yang sedang diperiksa, sekalipun antarmukanya tidak menampilkannya.
-- Berkas perkara menyebut modus yang paling dekat dengan bentuk selisihnya,
-- dan itu keterangan untuk yang memeriksa, bukan untuk yang diperiksa.
--
-- Pasang lewat SQL Editor Supabase, sekali saja:
--   https://supabase.com/dashboard/project/<ref>/sql/new

create table if not exists nalar.perkara (
  klaim_id       text primary key,
  teks           text        not null,
  -- "aturan" atau "agen". Versi aturan deterministik dan tidak menuntut
  -- model bahasa menyala, dan itu yang dilayani peragaan.
  sumber         text        not null default 'aturan',
  n_panggilan    integer     not null,
  alat           text[]      not null,
  -- Sidik rantai jejak. Satu baris jejak yang disunting belakangan membuat
  -- sidik ini berubah, jadi angka pada berkas perkara bisa dibuktikan
  -- berasal dari pemanggilan alat yang tercatat.
  sidik_akhir    text        not null,
  a1_lulus       boolean     not null,
  dibuat_pada    timestamptz not null default now()
);

alter table nalar.perkara enable row level security;

-- Sama seperti tabel lain: aplikasi hanya boleh membaca. Yang menulis
-- scripts/muat_db.py dengan kunci service_role, di luar jalur permintaan.
drop policy if exists "baca perkara" on nalar.perkara;
create policy "baca perkara"
  on nalar.perkara for select
  to anon, authenticated
  using (true);

grant usage on schema nalar to anon, authenticated;
grant select on nalar.perkara to anon, authenticated;
