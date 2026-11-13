-- Floor Record accounts. Paste this whole file into the Supabase SQL Editor and press Run. Safe to run more than once.
-- One row per person: who represents them, what they follow, and whether they want the newsletter. Nothing else is kept.

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  zip text,
  state text,
  rep_id text,
  rep_name text,
  topics jsonb not null default '[]'::jsonb,
  bills jsonb not null default '[]'::jsonb,
  newsletter boolean not null default true,
  unsub_token uuid not null default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- A signed-in person can see and change their own row, and nobody else's.
drop policy if exists "read own row" on public.profiles;
create policy "read own row" on public.profiles for select to authenticated using (auth.uid() = id);
drop policy if exists "add own row" on public.profiles;
create policy "add own row" on public.profiles for insert to authenticated with check (auth.uid() = id);
drop policy if exists "change own row" on public.profiles;
create policy "change own row" on public.profiles for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);

-- The email on a row is always the address the person proved they own by signing in, never one typed into a form.
create or replace function public.profiles_stamp() returns trigger language plpgsql security definer set search_path = '' as $$
begin
  new.email := (select u.email from auth.users u where u.id = new.id);
  new.updated_at := now();
  if tg_op = 'UPDATE' then new.unsub_token := old.unsub_token; new.created_at := old.created_at; end if;
  return new;
end $$;
drop trigger if exists profiles_stamp on public.profiles;
create trigger profiles_stamp before insert or update on public.profiles for each row execute function public.profiles_stamp();

-- "Delete My Account": removes the sign-in and, with it, the row above.
create or replace function public.delete_me() returns void language sql security definer set search_path = '' as $$
  delete from auth.users where id = auth.uid();
$$;
revoke all on function public.delete_me() from public, anon;
grant execute on function public.delete_me() to authenticated;

-- The unsubscribe link in every email: works without signing in, and can only turn the newsletter off.
create or replace function public.unsubscribe(token uuid) returns boolean language plpgsql security definer set search_path = '' as $$
begin
  update public.profiles set newsletter = false where unsub_token = token;
  return found;
end $$;
grant execute on function public.unsubscribe(uuid) to anon, authenticated;
