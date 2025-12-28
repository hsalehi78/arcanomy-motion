# Concept Ledger (Supabase) — v2

Without this, dedupe is fake.

## What the ledger must store

- `date`
- `blog_slug`
- `day_n`
- `claim_id`
- `primary_tag`
- `core_stat_hash`
- `takeaway_sentence`
- `hook_premise`
- `clips_used[]` (including source windows)
- `music_used`
- `chart_used` (template + data)
- `assets_version` (so you can reproduce)

## Minimal SQL (example)

Assumptions (based on your answers):
- **Auth model**: user-auth (Supabase Auth)
- **Scope**: keep it simple (solo) → ledger only for MVP
- **RLS**: enable (recommended with user-auth)

`TODO(V2): confirm your Supabase project ref + whether you want schema/table name exactly as below`

```sql
create table if not exists public.concept_ledger (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),

  owner_user_id uuid not null default auth.uid() references auth.users(id),

  run_id text not null,
  date date not null,
  blog_identifier text not null,
  blog_slug text not null,
  day_n int not null,

  claim_id text not null,
  claim_text text not null,
  primary_tag text not null,
  core_stat_hash text,

  takeaway_sentence text not null,
  hook_premise text not null,

  clips_used jsonb not null,       -- [{clip_id, path, source_in, source_out, beat_id}, ...]
  music_used jsonb,                -- {track_id, path}
  chart_used jsonb,                -- {template, props} or null

  assets_version text not null,

  unique (owner_user_id, run_id)
);

create index if not exists concept_ledger_blog_slug_date_idx
  on public.concept_ledger (blog_slug, date desc);

create index if not exists concept_ledger_core_stat_hash_idx
  on public.concept_ledger (core_stat_hash);

alter table public.concept_ledger enable row level security;

create policy "ledger_select_own"
  on public.concept_ledger
  for select
  using (auth.uid() = owner_user_id);

create policy "ledger_insert_own"
  on public.concept_ledger
  for insert
  with check (auth.uid() = owner_user_id);

create policy "ledger_update_own"
  on public.concept_ledger
  for update
  using (auth.uid() = owner_user_id)
  with check (auth.uid() = owner_user_id);
```

## RLS + auth

Chosen: **user-auth**. With that, RLS should be **on** and scoped to `owner_user_id`.

## Dedupe queries (MVP)

- “last 7 reels for this blog_slug”
- “last 14 reels (global) by core_stat_hash”
- “exclude clips used in last 14 days”
- “exclude music used in last 7 days”

