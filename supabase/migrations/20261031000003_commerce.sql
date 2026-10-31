-- Fly Finder: stores and commercial products, kept separate from the pattern catalog.
-- Prices are stored in their own currency and never converted.

create table public.stores (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name text not null,
  website text not null check (website ~ '^https?://'),
  country text not null check (country ~ '^[A-Z]{2}$'),          -- ISO 3166-1 alpha-2
  currency text not null check (currency ~ '^[A-Z]{3}$'),        -- ISO 4217
  description text,
  affiliate_program boolean not null default false,
  shipping_countries text[] not null default '{}',              -- ISO codes or 'WORLDWIDE'
  active boolean not null default true,
  is_demo boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index stores_country_idx on public.stores (country);
create index stores_shipping_idx on public.stores using gin (shipping_countries);
create trigger stores_updated_at before update on public.stores
  for each row execute function public.set_updated_at();

create table public.products (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete restrict,
  external_id text not null,                                     -- store SKU / handle
  name text not null,
  brand text,
  description text,
  product_url text not null check (product_url ~ '^https?://'),
  affiliate_url text check (affiliate_url ~ '^https?://'),
  price numeric(12,2) check (price is null or price >= 0),
  currency text check (currency ~ '^[A-Z]{3}$'),
  availability_status text not null default 'unknown' check (availability_status in (
    'in_stock','out_of_stock','preorder','discontinued','unknown')),
  country text check (country ~ '^[A-Z]{2}$'),
  last_verified_at timestamptz,
  active boolean not null default true,
  is_demo boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint products_store_external_unique unique (store_id, external_id),
  constraint products_price_currency check (price is null or currency is not null),
  constraint products_price_verified check (price is null or last_verified_at is not null)
);
create index products_store_idx on public.products (store_id);
create index products_active_idx on public.products (active) where active;
create trigger products_updated_at before update on public.products
  for each row execute function public.set_updated_at();

-- One product can be a specific variant (size/colour) of a pattern.
create table public.product_patterns (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  fly_pattern_id uuid not null references public.fly_patterns(id) on delete cascade,
  size text,
  color text,
  variant text,
  created_at timestamptz not null default now()
);
create unique index product_patterns_unique_idx
  on public.product_patterns (product_id, fly_pattern_id, coalesce(size, ''), coalesce(color, ''));
create index product_patterns_pattern_idx on public.product_patterns (fly_pattern_id);
