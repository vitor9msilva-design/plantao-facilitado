# Fluxo de trabalho do Plantão Facilitado

Como uma ideia vira mudança no ar, como o conteúdo médico é revisado e o que conferir antes de publicar. Vale para o Dr. Vitor e para o Claude Code.

## 1. Mudança no site (código ou conteúdo)

```
Pedido do Dr. Vitor
   → Claude cria um branch (ex.: melhorias-revisao-cid)
   → edita fonte/ e roda o build
   → roda os testes (seção 4)
   → abre um pull request no GitHub, dizendo o que mudou e se mexe no Supabase
   → o Netlify gera um LINK DE PRÉVIA no pull request
   → Dr. Vitor testa a prévia no celular e no computador do hospital
   → "pode publicar" → Claude junta ao main → o Netlify publica em cerca de 1 minuto
```

- **Nada vai para o `main` sem o "pode publicar".** O `main` é o site do plantão.
- **A prévia usa os seus dados reais** (o mesmo Supabase). O que você editar ou revisar lá fica valendo.
- **Desfazer uma publicação:** Netlify → Deploys → escolha o deploy anterior → **Publish deploy**. Volta na hora, sem precisar do Claude.
- **Mudança na função de IA** (`supabase/funcao-rapid-handler/index.ts`) não é publicada sozinha: Supabase → Edge Functions → rapid-handler → Code → colar → Deploy. O pull request avisa quando for preciso.

## 2. Conteúdo médico: rascunho → revisado

| Estado | O que significa | Onde aparece |
|---|---|---|
| **rascunho** | Escrito por IA (Claude ou Gemini) e ainda não conferido | Selo amarelo "rascunho", faixa no topo da receita, aviso ao copiar |
| **conferir dose** | A revisão de doses apontou algo (`fonte/revisao.json`) | Selo vermelho/amarelo, quadro com o apontamento e a sugestão |
| **revisado** | O Dr. Vitor conferiu (data gravada em `revisadoEm`) | Selo verde "✓ Revisado em dd/mm/aaaa" |

**Regras:**
- O Claude **nunca altera dose sem aprovação.** Ele aponta e sugere; quem decide é o médico.
- Todo item novo escrito por IA entra como **rascunho**.
- Para revisar: **Prescrições → ▶ Revisar um por um**. Abre os críticos primeiro.
  - **Revisado, próximo:** conferi; se precisava, já corrigi no Editar.
  - **Pular:** volto depois.
  - **Editar:** corrigir agora.
- **Ritmo sugerido:** 10 itens por plantão. Os 156 pendentes de hoje acabam em cerca de 16 plantões; os 7 críticos, antes do próximo.
- **Revisão de doses completa uma vez por ano**, ou quando uma bula, protocolo do MS ou diretriz mudar. O Claude gera um novo `fonte/revisao.json` com outra data. Os itens voltam para a fila só se tiverem apontamento novo.

## 3. Onde fica cada coisa (e por que importa)

- **`fonte/base.json`**: conteúdo base, igual para todo mundo que usar o app.
- **Supabase** (`itens` e `meta`): as suas edições, favoritos e revisões. **Elas vencem o base.json.**
  - Consequência: uma correção feita por você no site fica só na sua conta. Para entrar no produto (outros médicos), ela precisa ir também para o `base.json`.
  - A cada mês, ou antes de abrir para outros médicos: ⚙️ Configurações → Backup → Gerar backup, e mande ao Claude para incorporar ao base.json.
- **Um documento que você já editou** continua com a sua versão. Por isso ele não recebe as novidades do modelo, como o CID automático. Para receber: abra o documento no Editar e use "restaurar original", ou acrescente a linha `CID: {cid}`.

## 4. Antes de publicar (checklist do Claude)

1. `python3 fonte/build_netlify.py "https://rwlxqhpwneixapklovmn.supabase.co" "sb_publishable_3RbE169QpJSx4VFzXs7TaA_KwPJjQOp" ia rapid-handler`
2. `python3 testes/teste_revisao_cid.py` (revisão, CID e documentos; não precisa de IA)
3. Teste de ponta a ponta da IA (`testes/COMO-RODAR.md`): streaming, plano B e modo sem streaming.
4. Capturas de tela no computador (1440 px) e no celular (390 px).
5. No pull request:
   - o que mudou;
   - se mexe no Supabase;
   - se mexe em conteúdo médico (e se entrou como rascunho);
   - resultado dos testes.

## 5. Regras que não mudam

As regras do dono estão no `CLAUDE.md` (medicamentos registrados no Brasil, sem lacunas, conduta só do médico, privacidade). Também:
- **Pacientes:** só iniciais, que não vão para a IA, apagados em 4 h.
- **CID em atestado ou declaração:** só com autorização do paciente (Resolução CFM 1.658/2002). O app nunca preenche sozinho; o médico acrescenta.
- **Segredos** (cofre, chave do Gemini) nunca entram no repositório.
