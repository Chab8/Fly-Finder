-- Fly Finder: Row Level Security and Storage buckets.
--
-- The mobile app never talks to Supabase directly: it calls the FastAPI backend, which
-- uses a server-side connection. These policies are defence in depth so that the public
-- anon key, if ever used, can only READ public catalog data and never write anything.

alter table public.life_stages enable row level security;
alter table public.image_sources enable row level security;
alter table public.model_versions enable row level security;
alter table public.organisms enable row level security;
alter table public.organism_life_stages enable row level security;
alter table public.common_names enable row level security;
alter table public.organism_texts enable row level security;
alter table public.taxonomic_synonyms enable row level security;
alter table public.organism_images enable row level security;
alter table public.fly_patterns enable row level security;
alter table public.fly_pattern_texts enable row level security;
alter table public.fly_pattern_materials enable row level security;
alter table public.fly_pattern_variants enable row level security;
alter table public.fly_images enable row level security;
alter table public.fly_organism_matches enable row level security;
alter table public.stores enable row level security;
alter table public.products enable row level security;
alter table public.product_patterns enable row level security;
alter table public.identifications enable row level security;
alter table public.identification_candidates enable row level security;

-- Public, read-only catalog.
create policy "catalog read" on public.life_stages for select to anon, authenticated using (true);
create policy "catalog read" on public.image_sources for select to anon, authenticated using (true);
create policy "catalog read" on public.model_versions for select to anon, authenticated using (true);
create policy "catalog read" on public.organisms for select to anon, authenticated using (true);
create policy "catalog read" on public.organism_life_stages for select to anon, authenticated using (true);
create policy "catalog read" on public.common_names for select to anon, authenticated using (true);
create policy "catalog read" on public.organism_texts for select to anon, authenticated using (true);
create policy "catalog read" on public.taxonomic_synonyms for select to anon, authenticated using (true);
create policy "catalog read" on public.fly_patterns for select to anon, authenticated using (true);
create policy "catalog read" on public.fly_pattern_texts for select to anon, authenticated using (true);
create policy "catalog read" on public.fly_pattern_materials for select to anon, authenticated using (true);
create policy "catalog read" on public.fly_pattern_variants for select to anon, authenticated using (true);
create policy "catalog read" on public.fly_organism_matches for select to anon, authenticated using (true);

-- Only images with explicit permission are publicly readable.
create policy "approved images read" on public.organism_images for select to anon, authenticated
  using (permission_status = 'approved');
create policy "approved images read" on public.fly_images for select to anon, authenticated
  using (permission_status = 'approved');

-- Only active commerce records are publicly readable.
create policy "active stores read" on public.stores for select to anon, authenticated using (active);
create policy "active products read" on public.products for select to anon, authenticated using (active);
create policy "product patterns read" on public.product_patterns for select to anon, authenticated using (
  exists (select 1 from public.products p where p.id = product_id and p.active)
);

-- Signed-in users (future) can read only their own identifications. Anonymous history is
-- served by the backend, filtered by client hash. No client-side writes anywhere.
create policy "own identifications read" on public.identifications for select to authenticated
  using ((select auth.uid()) = user_id);
create policy "own identification candidates read" on public.identification_candidates for select to authenticated
  using (exists (
    select 1 from public.identifications i
    where i.id = identification_id and i.user_id = (select auth.uid())
  ));

-- ------------------------------------------------------------------ Storage
-- catalog-images: public read (licensed catalog photos). Writes only via service role.
-- user-uploads:   private. Only the backend (service role) can read or write.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('catalog-images', 'catalog-images', true, 10485760, array['image/jpeg','image/png','image/webp']),
  ('user-uploads', 'user-uploads', false, 12582912, array['image/jpeg'])
on conflict (id) do nothing;
