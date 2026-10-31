-- Fly Finder: log of identifications performed by the app.
-- No account is required: anonymous installs are grouped by a salted hash of a random
-- client id generated on the device. User photos are not stored unless the product
-- setting allows it AND the user consented for that request (image_consent).

create table public.identifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  client_hash text,
  kind text not null check (kind in ('organism','fly')),
  status text not null default 'completed' check (status in ('completed','failed')),
  match_level text not null check (match_level in (
    'high_match','moderate_match','low_match','inconclusive','insufficient_image','not_compatible')),
  primary_label text,
  result jsonb not null,                -- response snapshot, for history and evaluation
  analysis_source text not null,        -- e.g. 'gemini+open_clip', 'open_clip', 'demo'
  ai_model text,
  embedding_model text,
  image_consent boolean not null default false,
  image_storage_path text,
  is_demo boolean not null default false,
  created_at timestamptz not null default now(),
  constraint identifications_image_requires_consent check (image_storage_path is null or image_consent)
);
create index identifications_client_idx on public.identifications (client_hash, created_at desc);
create index identifications_user_idx on public.identifications (user_id, created_at desc);

-- Ranked candidates, stored relationally so accuracy can be measured with SQL.
create table public.identification_candidates (
  id uuid primary key default gen_random_uuid(),
  identification_id uuid not null references public.identifications(id) on delete cascade,
  position smallint not null check (position >= 1),
  label text not null,
  organism_id uuid references public.organisms(id) on delete set null,
  fly_pattern_id uuid references public.fly_patterns(id) on delete set null,
  ai_confidence text check (ai_confidence in ('high','moderate','low','none')),
  visual_similarity real,
  created_at timestamptz not null default now(),
  constraint identification_candidates_unique unique (identification_id, position)
);
create index identification_candidates_organism_idx on public.identification_candidates (organism_id);
create index identification_candidates_fly_idx on public.identification_candidates (fly_pattern_id);
