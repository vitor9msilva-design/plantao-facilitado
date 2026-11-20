# CLAUDE.md: contexto para o Claude Code

Leia isto antes de qualquer alteração. O manual completo para o dono do projeto está em **LEIA-ME.md**, e o plano para virar produto em **ROADMAP-PRODUTO.md**.

## O projeto em uma frase
O **Plantão Facilitado** é um app web de pronto-socorro (prescrições, documentos, HDAs e prontuário com IA) do Dr. Vitor Machado da Silva (CRM-DF 36.322). Hoje é de uso pessoal, adaptado para colar no **Soul MV**. O objetivo agora é transformá-lo num **produto** para outros médicos.

## VERSÃO OFICIAL: só o site do Netlify
- **A única versão que deve ser modificada e publicada é o site do Netlify**: `https://vmsplantoes.netlify.app`, acessado pelo link com o código secreto depois do `#`. O código fica com o dono e **nunca** entra no projeto.
- Toda alteração é feita em `fonte/` e entregue como o build do Netlify (`prontos/netlify/`), mais a função `rapid-handler` quando ela mudar.
- **Não modificar nem republicar:** a versão do artifact do Claude (`prontos/versao-claude.html`, artifact 8LyrAGr3QPJqYdYAYbKCKi), a cópia compartilhada no Claude (CH45xWfoRvAXfQyqxmYbyp) e o arquivo `versao-compartilhar-sem-meus-dados.html`. Ficam congelados como estão.

## Arquivos que importam
| Caminho | O que é |
|---|---|
| `fonte/template.html` | O app inteiro (HTML + CSS + JS, cerca de 3.350 linhas). `__BASE__` é substituído pelo conteúdo do base.json |
| `fonte/base.json` | Conteúdo: 216 prescrições, 78 documentos, 77 HDAs, blocos, exame físico, `iaPrompt` (prompt do prontuário), `config` |
| `fonte/build_netlify.py` | Gera `prontos/netlify/` (dados no Supabase e IA pela função). Uso: `python3 fonte/build_netlify.py "<url supabase>" "<chave publishable>" ia rapid-handler` |
| `fonte/build_claude.py` | (congelado) gera a versão antiga do artifact do Claude: não usar |
| `supabase/funcao-rapid-handler/index.ts` | **A função de IA que está no ar e funcionando** (Edge Function `rapid-handler`). É a versão ajustada pelo Gemini em 20/11/2026; veja abaixo |
| `supabase/banco/criar-banco.sql` | Tabela `docs` e funções `ler` e `gravar` |
| `historico/funcao-versao-claude-17nov.ts` | Versão anterior da função, só para consulta |
| `testes/` | Testes de ponta a ponta (Playwright, Gemini simulado e a função rodando em Deno). Veja `testes/COMO-RODAR.md` |

**Nunca edite `prontos/`:** os arquivos ali são gerados. Edite `fonte/` e rode os builds.

## A função de IA em produção (versão de 20/11/2026)
- `POST` com `{cofre, messages, tier, nivel, stream}`. Ela confere `cofre === secret COFRE` e chama o Gemini.
- **Modelos com troca automática:**
  - Para `tier` padrão: `MODELO` (gemini-3.8-flash), depois `MODELO_RESERVA` (gemini-3.7-flash), depois gemini-2.5-flash e por fim gemini-2.0-flash.
  - Para `tier: "complex"` (revisor): gemini-3.1-pro-preview, depois gemini-2.5-pro e por fim gemini-1.5-pro.
  - Erro 404 pula para o modelo seguinte. Sobrecarga (429 ou 5xx) espera 600 ms, tenta de novo e depois troca de modelo.
- **Raciocínio:** `nivel` aceita minimal, low, medium ou high. Sem `nivel`, vale o secret `RACIOCINIO`; sem ele, `low` (o `complex` usa o padrão do modelo). Se o Gemini recusar o `thinkingConfig` (400 com "think"), a função repete sem ele.
- **Streaming:** com `stream: true`, ela repassa o fluxo SSE do Gemini sem mexer, com `text/event-stream`. O site extrai o texto em `textoDoEvento()`.
- `GEMINI_URL_BASE` serve só para testes locais.
- **Ao publicar no Supabase:** o arquivo precisa se chamar `index.ts`, a função se chama `rapid-handler` e o **Verify JWT precisa ficar desligado**.

## Como o site conversa com a IA (template.html)
- `aiSample` vale `claude.use('sample')` no artifact do Claude e `iaServidor()` no Netlify.
- `iaServidor()` tenta o streaming primeiro. Se o texto não começar em 25 s ou falhar, refaz sem streaming e grava `plantaorx:streamOff` (streaming desligado por 12 h naquele navegador). Também tenta de novo uma vez em queda de rede.
- O prontuário pede JSON `{caixa1..caixa4, receita}`. `jsonParcial()` preenche as caixas enquanto o texto chega, e `parseJsonLoose()` faz a leitura final.
- **Nível de raciocínio pedido:** `low` para escrita (prontuário, documentos, saída, passagem) e `medium` para clínica (decisão, discussão, Gerar receita, PS com IA). O revisor usa `modelTier: 'complex'`.

## Mapa do template.html (procure pelos comentários `/* ---------- … */`)
armazenamento (`store`: Claude db / Supabase RPC / local) · estado · filtro · render: cabeçalho e ficha · **exame físico direcionado** (`efPersonalizado`) · **prescrição No PS / Casa** (`rxPartes`, `separarRx`, `sugestaoPs`) · ações · modais · blocos rápidos · juntar receitas · **prontuário com IA** (`gerar`, `FORMATO`, `iaBase`) · pacientes no PS (`casos`, sync na nuvem `mesclarCasosRemotos`) · textos rápidos (imagem, reavaliação) · estilo · revisor · orientações · exames, contexto e internação · **gerar receita com IA** · pendências · escores · contexto (`contextoDe`) · apoio à decisão e discussão · alta a pedido e evasão · documentos do paciente (`abrirDocsPaciente`, `melhorModelo`) · passagem de plantão · barra lateral de pacientes · busca Ctrl+K · início.

## Regras do dono (não quebre)
- Português do Brasil e medicamentos **registrados no Brasil**, com nome comercial. AINE preferido: **Toragesic (cetorolaco) ou naproxeno**. Corticoide nasal: **Nasonex ou Dymista**.
- Toda receita gerada tem uma opção de **dor aguda intensa** (paracetamol + codeína ou tramadol).
- **Não alterar doses** das receitas dele sem aprovação. O que for escrito pela IA ou por você entra como rascunho, para revisão.
- **Conduta (caixa 4):** só o que o médico escreveu. Nada de exames, reavaliação ou orientações por conta própria.
- **Nunca deixar lacunas** ("[completar]", "___", colchetes) em textos gerados.
- Justificativa de imagem em **uma frase**. O pedido de internação tem cabeçalho fixo (veja `gerarInternacao`).
- **Privacidade:**
  - Pacientes só com **iniciais**, que nunca vão para a IA. São apagados 4 h após a entrada ou na alta.
  - Nunca colocar no código o cofre, a chave do Gemini ou qualquer outro segredo.
- **Direitos autorais:** os manuais comprados de terceiros (MedRoute/MedOpen) **não** podem ser copiados para o projeto.

## Como trabalhar aqui
1. Edite `fonte/template.html` ou `fonte/base.json`.
2. Rode `python3 fonte/build_netlify.py "https://rwlxqhpwneixapklovmn.supabase.co" "sb_publishable_3RbE169QpJSx4VFzXs7TaA_KwPJjQOp" ia rapid-handler`. Só o build do Netlify; o do Claude está congelado.
3. Rode os testes de `testes/` antes de entregar.
4. Para publicar, zipe o **conteúdo** de `prontos/netlify/` e arraste em Netlify → Deploys. Mudanças na função vão para Supabase → Edge Functions → rapid-handler → Code → Deploy.
5. Ao terminar, diga ao dono **o que mudou** e **se precisa mexer no Supabase**.
