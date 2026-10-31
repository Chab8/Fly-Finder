-- Fly Finder: scientific catalog (organisms) and fly pattern catalog, plus their relations.

-- ---------------------------------------------------------------- organisms
-- One row per taxon at whatever rank is justified (order, family, genus, species...).
-- A family-level record is a valid record: species is never required.
create table public.organisms (
  id uuid primary key default gen_random_uuid(),
  scientific_name text not null,
  taxonomic_rank text not null check (taxonomic_rank in (
    'kingdom','phylum','class','subclass','order','suborder','infraorder','superfamily',
    'family','subfamily','genus','species','subspecies','other')),
  taxonomic_identifier text,           -- name with authorship, e.g. 'Baetis Leach, 1815'
  gbif_taxon_id bigint unique,
  inaturalist_taxon_id bigint unique,
  kingdom text,
  phylum text,
  "class" text,
  "order" text,
  family text,
  genus text,
  species text,
  organism_group text not null check (organism_group in (
    'aquatic_insect','terrestrial_insect','crustacean','annelid','mollusc','fish','other')),
  habitats text[] not null default '{}' check (habitats <@ array[
    'freshwater_running','freshwater_still','estuarine','marine','terrestrial']::text[]),
  size_min numeric(7,2) check (size_min is null or size_min >= 0),
  size_max numeric(7,2) check (size_max is null or size_max >= 0),
  size_unit text check (size_unit in ('mm')),
  geographic_distribution text,
  data_source text not null default 'curated',
  verification_status text not null default 'unverified'
    check (verification_status in ('unverified','source_verified','expert_verified')),
  is_demo boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint organisms_size_range check (size_min is null or size_max is null or size_min <= size_max),
  constraint organisms_size_unit check ((size_min is null and size_max is null) or size_unit is not null),
  constraint organisms_species_binomial check (taxonomic_rank <> 'species' or scientific_name ~ '^\S+\s+\S+')
);
create unique index organisms_scientific_name_key on public.organisms (lower(scientific_name));
create index organisms_order_idx on public.organisms (lower("order"));
create index organisms_family_idx on public.organisms (lower(family));
create index organisms_genus_idx on public.organisms (lower(genus));
create index organisms_group_idx on public.organisms (organism_group);
create index organisms_name_trgm_idx on public.organisms using gin (scientific_name extensions.gin_trgm_ops);
create trigger organisms_updated_at before update on public.organisms
  for each row execute function public.set_updated_at();

create table public.organism_life_stages (
  organism_id uuid not null references public.organisms(id) on delete cascade,
  life_stage_id uuid not null references public.life_stages(id) on delete restrict,
  notes text,
  created_at timestamptz not null default now(),
  primary key (organism_id, life_stage_id)
);
create index organism_life_stages_stage_idx on public.organism_life_stages (life_stage_id);

-- Common names are language data, kept apart from scientific data.
create table public.common_names (
  id uuid primary key default gen_random_uuid(),
  organism_id uuid not null references public.organisms(id) on delete cascade,
  language text not null check (language ~ '^[a-z]{2}$'),
  name text not null check (length(trim(name)) > 0),
  is_primary boolean not null default false,
  region text,                         -- optional ISO country/region where the name is used
  created_at timestamptz not null default now()
);
create unique index common_names_unique_idx on public.common_names (organism_id, language, lower(name));
create unique index common_names_one_primary_idx on public.common_names (organism_id, language) where is_primary;
create index common_names_name_trgm_idx on public.common_names using gin (name extensions.gin_trgm_ops);

create table public.organism_texts (
  organism_id uuid not null references public.organisms(id) on delete cascade,
  language text not null check (language ~ '^[a-z]{2}$'),
  description text,
  fishing_notes text,
  updated_at timestamptz not null default now(),
  primary key (organism_id, language)
);
create trigger organism_texts_updated_at before update on public.organism_texts
  for each row execute function public.set_updated_at();

create table public.taxonomic_synonyms (
  id uuid primary key default gen_random_uuid(),
  organism_id uuid not null references public.organisms(id) on delete cascade,
  synonym text not null,
  source text,
  created_at timestamptz not null default now()
);
create unique index taxonomic_synonyms_unique_idx on public.taxonomic_synonyms (organism_id, lower(synonym));
create index taxonomic_synonyms_lookup_idx on public.taxonomic_synonyms (lower(synonym));

create table public.organism_images (
  id uuid primary key default gen_random_uuid(),
  organism_id uuid not null references public.organisms(id) on delete cascade,
  image_url text,
  storage_path text,
  source text not null references public.image_sources(code),
  source_id text,
  source_url text,
  license text not null,
  attribution text not null,
  commercial_use_allowed boolean not null,
  permission_status text not null default 'pending' check (permission_status in ('approved','pending','rejected')),
  image_view text,
  life_stage_id uuid references public.life_stages(id),
  embedding_model text references public.model_versions(model_key),
  embedding extensions.vector(512),
  created_at timestamptz not null default now(),
  constraint organism_images_location check (image_url is not null or storage_path is not null),
  constraint organism_images_embedding_model check ((embedding is null) = (embedding_model is null))
);
create unique index organism_images_unique_idx
  on public.organism_images (organism_id, source, coalesce(source_id, image_url, storage_path));
create index organism_images_organism_idx on public.organism_images (organism_id);
create index organism_images_embedding_idx
  on public.organism_images using hnsw (embedding extensions.vector_cosine_ops);

-- -------------------------------------------------------------- fly patterns
create table public.fly_patterns (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name text not null,
  alternate_names text[] not null default '{}',
  category text not null check (category in (
    'dry_fly','nymph','emerger','wet_fly','streamer','terrestrial','saltwater','attractor','other')),
  imitation_type text not null default 'not_specified' check (imitation_type in (
    'exact_imitation','general_imitation','suggestive_imitation','attractor','not_specified')),
  hook_size_min text check (hook_size_min ~ '^\d{1,2}(/0)?$'),   -- smallest hook of usual range
  hook_size_max text check (hook_size_max ~ '^\d{1,2}(/0)?$'),   -- largest hook of usual range
  colors text[] not null default '{}',
  habitats text[] not null default '{}' check (habitats <@ array[
    'freshwater_running','freshwater_still','estuarine','marine','terrestrial']::text[]),
  fishing_environments text[] not null default '{}' check (fishing_environments <@ array[
    'freshwater','saltwater','brackish']::text[]),
  difficulty text check (difficulty in ('beginner','intermediate','advanced')),
  data_source text not null default 'curated',
  verification_status text not null default 'unverified'
    check (verification_status in ('unverified','source_verified','expert_verified')),
  is_demo boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index fly_patterns_name_key on public.fly_patterns (lower(name));
create index fly_patterns_category_idx on public.fly_patterns (category);
create index fly_patterns_alt_names_idx on public.fly_patterns using gin (alternate_names);
create index fly_patterns_colors_idx on public.fly_patterns using gin (colors);
create index fly_patterns_name_trgm_idx on public.fly_patterns using gin (name extensions.gin_trgm_ops);
create trigger fly_patterns_updated_at before update on public.fly_patterns
  for each row execute function public.set_updated_at();

create table public.fly_pattern_texts (
  fly_pattern_id uuid not null references public.fly_patterns(id) on delete cascade,
  language text not null check (language ~ '^[a-z]{2}$'),
  description text,
  usage_notes text,
  updated_at timestamptz not null default now(),
  primary key (fly_pattern_id, language)
);
create trigger fly_pattern_texts_updated_at before update on public.fly_pattern_texts
  for each row execute function public.set_updated_at();

create table public.fly_pattern_materials (
  id uuid primary key default gen_random_uuid(),
  fly_pattern_id uuid not null references public.fly_patterns(id) on delete cascade,
  component text not null,             -- hook, thread, tail, body, rib, wing, hackle, head...
  material text not null,
  sort_order smallint not null default 0,
  created_at timestamptz not null default now()
);
create index fly_pattern_materials_pattern_idx on public.fly_pattern_materials (fly_pattern_id, sort_order);

create table public.fly_pattern_variants (
  id uuid primary key default gen_random_uuid(),
  fly_pattern_id uuid not null references public.fly_patterns(id) on delete cascade,
  name text not null,
  description text,
  created_at timestamptz not null default now()
);
create unique index fly_pattern_variants_unique_idx on public.fly_pattern_variants (fly_pattern_id, lower(name));

create table public.fly_images (
  id uuid primary key default gen_random_uuid(),
  fly_pattern_id uuid not null references public.fly_patterns(id) on delete cascade,
  image_url text,
  storage_path text,
  source text not null references public.image_sources(code),
  source_id text,
  source_url text,
  license text not null,
  attribution text not null,
  commercial_use_allowed boolean not null,
  permission_status text not null default 'pending' check (permission_status in ('approved','pending','rejected')),
  image_view text,
  embedding_model text references public.model_versions(model_key),
  embedding extensions.vector(512),
  created_at timestamptz not null default now(),
  constraint fly_images_location check (image_url is not null or storage_path is not null),
  constraint fly_images_embedding_model check ((embedding is null) = (embedding_model is null))
);
create unique index fly_images_unique_idx
  on public.fly_images (fly_pattern_id, source, coalesce(source_id, image_url, storage_path));
create index fly_images_pattern_idx on public.fly_images (fly_pattern_id);
create index fly_images_embedding_idx on public.fly_images using hnsw (embedding extensions.vector_cosine_ops);

-- -------------------------------------------------- organism <-> fly relations
-- The core knowledge of the product. Never filled automatically: every row comes from
-- a curated source and records whether an expert verified it.
create table public.fly_organism_matches (
  id uuid primary key default gen_random_uuid(),
  organism_id uuid not null references public.organisms(id) on delete cascade,
  fly_pattern_id uuid not null references public.fly_patterns(id) on delete cascade,
  life_stage_id uuid not null references public.life_stages(id),
  match_type text not null check (match_type in (
    'exact_imitation','general_imitation','suggestive_imitation','attractor','not_specified')),
  biological_compatibility text not null check (biological_compatibility in ('high','medium','low','unknown')),
  expert_verified boolean not null default false,
  verification_source text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint fly_organism_matches_unique unique (organism_id, fly_pattern_id, life_stage_id),
  constraint fly_organism_matches_verified_source check (not expert_verified or verification_source is not null)
);
create index fly_organism_matches_fly_idx on public.fly_organism_matches (fly_pattern_id);
create index fly_organism_matches_stage_idx on public.fly_organism_matches (life_stage_id);
create trigger fly_organism_matches_updated_at before update on public.fly_organism_matches
  for each row execute function public.set_updated_at();
