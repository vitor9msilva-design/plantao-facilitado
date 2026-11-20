-- Plantão Facilitado — recriar o banco no Supabase (SQL Editor > New query > colar > Run)
-- Use só se precisar montar um projeto Supabase NOVO. No projeto atual já está tudo criado.
-- Guarda: edições de receitas/documentos/HDAs (coleção "itens"), configurações, favoritos,
-- estilo aprendido e pacientes das últimas 4 h (coleção "meta"). Tudo separado pelo "cofre"
-- (o código secreto depois do # no seu link).

create table if not exists public.docs (
  cofre      text        not null,
  colecao    text        not null,
  id         text        not null,
  dados      jsonb       not null,
  atualizado timestamptz not null default now(),
  primary key (cofre, colecao, id)
);
alter table public.docs enable row level security;   -- sem políticas: ninguém lê a tabela direto

create or replace function public.ler(p_cofre text)
returns table (colecao text, id text, dados jsonb)
language sql security definer set search_path = public as $$
  select d.colecao, d.id, d.dados from public.docs d
  where d.cofre = p_cofre and length(p_cofre) >= 20;
$$;

create or replace function public.gravar(p_cofre text, p_colecao text, p_id text, p_dados jsonb)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_cofre is null or length(p_cofre) < 20 then raise exception 'cofre inválido'; end if;
  if p_dados is null then
    delete from public.docs where cofre = p_cofre and colecao = p_colecao and id = p_id;
  else
    insert into public.docs (cofre, colecao, id, dados, atualizado)
    values (p_cofre, p_colecao, p_id, p_dados, now())
    on conflict (cofre, colecao, id) do update set dados = excluded.dados, atualizado = now();
  end if;
end; $$;

grant execute on function public.ler(text) to anon;
grant execute on function public.gravar(text, text, text, jsonb) to anon;
