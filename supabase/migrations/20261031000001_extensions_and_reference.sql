-- Fly Finder: extensions, shared helpers and reference data.
-- Safe to run on a fresh Supabase project. Non-destructive (no DROP statements).

create schema if not exists extensions;
create extension if not exists vector with schema extensions;   -- pgvector, visual similarity
create extension if not exists pg_trgm with schema extensions;  -- fuzzy name search

-- Keeps updated_at current on every UPDATE.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Life stages are a shared vocabulary. Which stages apply to each organism is modelled
-- in organism_life_stages, because a beetle, a mayfly and a shrimp use different ones.
create table public.life_stages (
  id uuid primary key default gen_random_uuid(),
  code text not null unique check (code ~ '^[a-z_]+$'),
  sort_order smallint not null,
  description text not null,
  created_at timestamptz not null default now()
);

insert into public.life_stages (code, sort_order, description) values
  ('egg',      10, 'Egg'),
  ('larva',    20, 'Larva (holometabolous insects, e.g. caddisflies, midges)'),
  ('nymph',    30, 'Nymph (hemimetabolous insects, e.g. mayflies, stoneflies)'),
  ('pupa',     40, 'Pupa'),
  ('emerger',  50, 'Emerger: transitioning at or near the surface'),
  ('subimago', 60, 'Subimago / dun (mayflies only)'),
  ('imago',    70, 'Imago / spinner (sexually mature adult mayfly)'),
  ('adult',    80, 'Adult'),
  ('juvenile', 90, 'Juvenile (fish, crustaceans and other non-insects)'),
  ('other',   100, 'Other stage not covered above'),
  ('unknown', 110, 'Stage not determined')
on conflict (code) do nothing;

-- Registry of image/data sources and their reuse conditions (see docs/IMAGE_LICENSES.md).
create table public.image_sources (
  code text primary key check (code ~ '^[a-z0-9_]+$'),
  name text not null,
  website text,
  commercial_use_policy text not null,
  requires_attribution boolean not null default true,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create trigger image_sources_updated_at before update on public.image_sources
  for each row execute function public.set_updated_at();

insert into public.image_sources (code, name, website, commercial_use_policy, requires_attribution, notes) values
  ('inaturalist', 'iNaturalist', 'https://www.inaturalist.org', 'per_image_license', true,
   'Each photo has its own license chosen by the observer. Only CC0, CC-BY and CC-BY-SA allow commercial reuse.'),
  ('gbif', 'GBIF occurrence media', 'https://www.gbif.org', 'per_image_license', true,
   'Media licenses are set by each publishing institution. Check every record.'),
  ('wikimedia_commons', 'Wikimedia Commons', 'https://commons.wikimedia.org', 'per_image_license', true, null),
  ('own_photo', 'Photographed by the Fly Finder team', null, 'allowed', false, null),
  ('licensed_partner', 'Licensed partner (tyer, manufacturer, store)', null, 'by_written_agreement', true,
   'Requires a signed permission covering commercial app use.'),
  ('demo', 'Fictional demo asset', null, 'not_applicable', false, 'Never shown outside DEMO mode.')
on conflict (code) do nothing;

-- AI models whose outputs are stored (embeddings) or referenced (vision analysis).
create table public.model_versions (
  model_key text primary key,
  purpose text not null check (purpose in ('vision_analysis', 'image_embedding')),
  provider text not null,
  model_name text not null,
  version text,
  embedding_dimension integer check (embedding_dimension is null or embedding_dimension > 0),
  license text,
  notes text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.model_versions (model_key, purpose, provider, model_name, version, embedding_dimension, license, notes) values
  ('open_clip:ViT-B-32:laion2b_s34b_b79k', 'image_embedding', 'open_clip', 'ViT-B-32', 'laion2b_s34b_b79k', 512,
   'MIT (open_clip code and laion/CLIP-ViT-B-32-laion2B-s34B-b79K weights)',
   'Embedding columns are vector(512). Changing dimension requires a migration and re-embedding.')
on conflict (model_key) do nothing;
