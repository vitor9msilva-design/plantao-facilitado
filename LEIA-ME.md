# Plantão Facilitado: backup completo e manual

> **Abrindo no Claude Code?** Ele lê sozinho o **CLAUDE.md** (contexto técnico e regras). O plano para virar produto está em **ROADMAP-PRODUTO.md**. Atualizado em 20/11/2026.

Backup gerado em 16/11/2026. Ele tem tudo o que é preciso para reconstruir, publicar e alterar o site: código, dados, função de IA, banco de dados e este manual.

**Para continuar com o Claude (ou outra IA):** abra uma conversa nova, anexe este .zip e cole o pedido da seção 9.

---

## 1. O que é

O site pessoal de pronto-socorro do **Dr. Vitor Machado da Silva (CRM-DF 36.322, Brasília)**, adaptado para colar no **Soul MV**. Tem quatro partes:

- **Prescrições**: 216 doenças. Cada uma tem HDA, exame físico dirigido, hipótese diagnóstica e prescrição separada em **No PS (EV/IM)** e **Para casa**.
- **Documentos**: 78 modelos de atestados, declarações, encaminhamentos, pedidos de exame e de imagem, receitas, termos do PS e relatórios.
- **HDAs**: 77 modelos.
- **Prontuário com IA**: as 4 caixas no formato do seu prompt, mais uma série de ferramentas:
  - Revisor, pedido de internação, justificativas, exames, escores e reavaliação de 2 h.
  - Pendências, apoio à decisão (alta, observação, internação ou UTI) e discussão do caso.
  - Passagem de plantão, documentos por paciente, alta a pedido e evasão.

## 2. Onde está cada versão

> **Desde 20/11/2026, a única versão oficial, que recebe mudanças, é a do Netlify (vmsplantoes.netlify.app, com o seu código depois do `#`).** As versões do Claude e o arquivo de compartilhar ficam congelados como estão.


| Versão | Endereço | IA | Onde guarda os dados |
|---|---|---|---|
| **Netlify** (hospital) | https://vmsplantoes.netlify.app + seu código secreto depois do `#` | Gemini, pela função `rapid-handler` do Supabase | Supabase |
| **Claude** | https://claude.ai/artifact/8LyrAGr3QPJqYdYAYbKCKi | Claude (da sua conta) | Armazenamento do próprio artifact |
| **Cópia compartilhada** (amiga) | https://claude.ai/artifact/CH45xWfoRvAXfQyqxmYbyp | Claude (da conta dela) | Espaço privado de cada usuário |
| **Arquivo para compartilhar** | `prontos/versao-compartilhar-sem-meus-dados.html` | Não | Só no navegador de quem abre |

As versões **não compartilham dados entre si**. Para levar as suas edições de uma para outra, use ⚙️ Configurações → Backup → **Gerar backup** numa e **Restaurar backup** na outra.

## 3. Contas e segredos (NÃO estão neste arquivo, de propósito)

| O quê | Onde fica | Observação |
|---|---|---|
| Código secreto (cofre) | No seu link do Netlify, depois do `#` | Quem tem o link acessa seus dados e gasta seus créditos. Não compartilhe. |
| Chave do Gemini (`AIza…`) | Supabase → Edge Functions → Secrets → `GEMINI_API_KEY` | Criada no aistudio.google.com, com faturamento ativo |
| `COFRE` | Supabase → Edge Functions → Secrets | Igual ao código depois do `#` |
| Supabase | Projeto `rwlxqhpwneixapklovmn` (URL `https://rwlxqhpwneixapklovmn.supabase.co`) | A chave *publishable* já vai dentro do site (é pública por natureza) |
| Netlify | Site `vmsplantoes` | Atualiza-se arrastando o zip em Deploys |

Secrets opcionais da função: `RACIOCINIO` (low/medium/high), `MODELO` (padrão `gemini-3.8-flash`), `MODELO_COMPLEXO` (padrão `gemini-3.1-pro-preview`), `MODELO_RESERVA` (padrão `gemini-3.7-flash`), `PROVEDOR` = `claude` (exige `ANTHROPIC_API_KEY`).

## 4. Arquivos deste backup

```
LEIA-ME.md                         este manual
fonte/
  template.html                    o site inteiro (HTML + CSS + JavaScript); "__BASE__" recebe os dados
  base.json                        conteúdo: prescrições, documentos, HDAs, blocos, exame físico, prompt da IA, config
  build_claude.py                  gera prontos/versao-claude.html
  build_netlify.py                 gera prontos/netlify/ (index.html + robots.txt)
prontos/
  versao-claude.html               pronto para publicar no artifact do Claude
  netlify/index.html, robots.txt   pronto para o Netlify (zipe a pasta e arraste em Deploys)
  versao-compartilhar-sem-meus-dados.html   sem nome/CRM/cidade, sem IA, sem Supabase
supabase/
  funcao-rapid-handler/index.ts    a função de IA QUE ESTÁ NO AR (versão de 20/11/2026, ajustada pelo Gemini)
  banco/criar-banco.sql            tabela e funções ler/gravar, para recriar o banco do zero
historico/funcao-versao-claude-17nov.ts   versão anterior da função (só consulta)
testes/                            teste de ponta a ponta: site + função (Deno) + Gemini simulado (COMO-RODAR.md)
CLAUDE.md                          contexto e regras para o Claude Code
ROADMAP-PRODUTO.md                 fases para transformar em produto
```

## 5. Como restaurar ou republicar

**Netlify (o mais comum):**
1. Gere o site, se mudou algo: `python3 fonte/build_netlify.py "https://rwlxqhpwneixapklovmn.supabase.co" "sb_publishable_3RbE169QpJSx4VFzXs7TaA_KwPJjQOp" ia rapid-handler`
2. Zipe o **conteúdo** da pasta `prontos/netlify/` (o index.html precisa ficar na raiz do zip).
3. Netlify → seu site → **Deploys** → arraste o zip → espere "Published".

**Função de IA (se o Supabase for recriado):**
1. Supabase → Edge Functions → Deploy a new function → Via Editor.
2. Deixe só o arquivo `index.ts`, cole `supabase/funcao-rapid-handler/index.ts` e escolha o nome **antes** de publicar. Se o nome não for `rapid-handler`, troque o 4º argumento do build.
3. Em Settings, desligue **Verify JWT** e salve.
4. Em Secrets, cadastre `GEMINI_API_KEY` e `COFRE`.
5. Teste: abrir `https://<projeto>.supabase.co/functions/v1/rapid-handler` deve mostrar `{"erro":"Método não permitido"}`.

**Banco (só se for um projeto Supabase novo):** SQL Editor → cole `supabase/banco/criar-banco.sql` → Run. Depois troque URL e chave no comando do build.

**Versão do Claude:** peça ao Claude que republique `prontos/versao-claude.html` no artifact `8LyrAGr3QPJqYdYAYbKCKi`, com as capabilities `db` e `sample`.

**Sem nada disso:** `prontos/versao-compartilhar-sem-meus-dados.html` abre direto no navegador e funciona offline, sem IA.

## 6. Seus dados pessoais (edições, favoritos, estilo)

O que você editou, favoritou ou ensinou ao site **não fica no base.json**. Fica no Supabase (Netlify) ou no artifact (Claude), por cima do conteúdo base. Por isso:

- **Faça um backup das edições de vez em quando:** ⚙️ Configurações → Backup → **Gerar backup** → **Copiar**, e guarde num arquivo junto deste zip.
- Para restaurar, cole o texto no mesmo lugar e use **Restaurar backup**.
- O backup não inclui os pacientes em atendimento, que são temporários.

## 7. Como o site funciona (para quem for alterar)

- **Um arquivo só:** `template.html` tem tudo. Os dados entram no lugar de `__BASE__` como JSON (`<script type="application/json" id="base">`).
- **Camadas:** o conteúdo base vem do `base.json`, e as edições do usuário ficam no armazenamento, nas coleções `itens` (receitas, documentos e HDAs editados) e `meta` (configurações, favoritos, categorias, exame físico por doença `ex_<id>`, estilo, pacientes `casos`). O que o usuário salva sempre vence o base, então atualizar o base.json não apaga edições.
- **Armazenamento (`store`):**
  - No Claude, `claude.use('db')`.
  - No Netlify, o Supabase pelas funções `ler(p_cofre)` e `gravar(p_cofre, p_colecao, p_id, p_dados)`, com fila local quando está offline e nova leitura a cada 60 s e ao voltar para a aba.
  - Na cópia compartilhada (`window.PLANTAO_PESSOAL`), cada usuário grava em `data/users/<id>/pf/`.
- **IA (`aiSample`):**
  - No Claude, `claude.use('sample')`.
  - No Netlify, `iaServidor()` chama `/functions/v1/<fn>` com `{cofre, messages, tier}`.
  - `tier: 'complex'` (revisor) usa o modelo mais forte.
- **Pacientes:**
  - Ficam em `casos`, com só as iniciais. São apagados 4 h após a entrada ou na alta.
  - São sincronizados na nuvem em `meta/casos` (lista + `apagados`); a versão mais recente de cada caso vence, pelo campo `atualizado`.
  - As iniciais nunca vão para a IA.
- **Prescrição No PS / Casa:**
  - `rxPartes()` usa a aba "No PS" quando existe. Senão, `separarRx()` separa pela via (EV/IM/SC vs oral, nasal, tópica) e pelas marcações "No PS" / "Receita de alta".
  - Sem parte de PS, `sugestaoPs()` monta sintomáticos com as suas próprias linhas de dose: dipirona, Toragesic, ondansetrona, Plasil, SF, Polaramine, hidrocortisona e, na dor intensa, tramadol.
- **Exame físico dirigido:** `efPersonalizado()` acrescenta ao seu modelo o exame do sistema da doença (por palavra-chave do nome e por categoria).
- **Layout "Console clínico":** menu lateral escuro (seções e pacientes), fonte IBM Plex Sans/Mono, cor petróleo `#0B5C55`, e tema escuro automático ou pelo botão da lua.

## 8. Suas preferências (regras que qualquer alteração deve respeitar)

- Português do Brasil. Medicamentos só registrados no Brasil, com nome comercial.
- Anti-inflamatório preferido: **Toragesic (cetorolaco) ou naproxeno**. Corticoide nasal: **Nasonex ou Dymista**.
- Toda receita gerada deve ter uma opção de **dor aguda intensa** (por exemplo, paracetamol + codeína ou tramadol).
- Justificativa de imagem em **uma frase** (ex.: "TC de crânio sem contraste para afastar causas secundárias de cefaleia, como hemorragia intracraniana, lesão expansiva ou hidrocefalia, em paciente com cefaleia de 5 dias de evolução, com piora hoje e acompanhada de vômitos.").
- Pedido de internação com o cabeçalho "DEPARTAMENTO DE EMERGÊNCIA - <local> / PEDIDO DE INTERNAÇÃO / ##IDENTIFICAÇÃO: Nome / Idade".
- Textos de documentos, alta a pedido e evasão: **diretos, sem lacunas**, adaptados ao caso. Nunca escrever "[completar]".
- **Conduta só com o que o médico escreveu**: não acrescentar exames, reavaliação ou orientações por conta própria.
- Raciocínio do Gemini: **baixo** para escrita (prontuário, documentos), **médio** para diagnóstico e conduta (decisão, discussão, gerar receita, PS com IA). O site manda `nivel` à função.
- Documentos: o médico escreve o pedido ("parecer da cardiologia", "TC de abdome") e a IA monta com a história do paciente.
- **Não alterar as doses das receitas dele sem aprovação.** O que o Claude escreveu vem marcado como "rascunho" (140 itens "A revisar").
- Dados de pacientes: só iniciais, apagados em 4 h. Nunca nome, CPF ou número de prontuário.
- Os manuais comprados de terceiros (MedRoute/MedOpen) **não** podem ser copiados para o site.
- Sistema pensado para o **Soul MV**. Uma versão para o **Tasy** fica para outro momento.

## 8b. A função de IA que está funcionando (20/11/2026)
Esta é a versão que você colou no Supabase, ajustada pelo Gemini. Ela é a referência a partir de agora.

- **Troca automática de modelo:**
  - No dia a dia: gemini-3.8-flash, depois gemini-3.7-flash, gemini-2.5-flash e por fim gemini-2.0-flash.
  - No revisor: gemini-3.1-pro-preview, depois gemini-2.5-pro e por fim gemini-1.5-pro.
  - Se um modelo não existir (erro 404), a função pula na hora para o seguinte. Se estiver sobrecarregado, espera 0,6 s, tenta de novo e depois troca de modelo.
- **Raciocínio:** aceita minimal, low, medium ou high, pedidos pelo site. Se o Gemini recusar, a função repete sem esse ajuste.
- **Streaming:** repassa o fluxo do Gemini direto ao site. O site tem plano B: se o texto não começar em 25 s, refaz sem streaming.
- **Para publicar:** Supabase → Edge Functions → **rapid-handler** → Code → colar → Deploy. O **Verify JWT** precisa ficar desligado.

## 8c. Continuar no Claude Code
1. Descompacte este backup numa pasta e abra essa pasta no Claude Code. Se puder, crie um repositório no GitHub com ela; o `.gitignore` já impede que segredos sejam enviados.
2. Ele lê o **CLAUDE.md** automaticamente.
3. Peça, por exemplo, o "Primeiro pedido sugerido" do final do **ROADMAP-PRODUTO.md**.
4. Os segredos (cofre do link e chave do Gemini) **não** estão no projeto. Para testar localmente, use os valores de teste de `testes/COMO-RODAR.md`.

## 9. Pedido pronto para colar numa conversa nova

> Este é o backup do meu site Plantão Facilitado (anexo). Leia o LEIA-ME.md inteiro antes de mexer. Os arquivos de trabalho são `fonte/template.html` e `fonte/base.json`; gere as versões com os scripts `build_*.py`. Respeite as regras da seção 8. Quero fazer esta alteração: …
> Ao terminar, me devolva o zip do Netlify (conteúdo de `prontos/netlify/`), diga se precisa mexer no Supabase e, se tiver acesso ao artifact do Claude, republique a versão do Claude.

## 10. Histórico do que foi construído

- **Base:** prescrições, documentos e HDAs editáveis, favoritos, busca, categorias, modo Editar, blocos rápidos, juntar receitas, quantidades, próximo campo, backup e tema escuro.
- **IA:**
  - Prontuário em 4 caixas, receita sugerida, Gerar receita por sintomas e justificativas.
  - Exames (laboratório e imagem, digitados ou colados), pedido de internação com cabeçalho e revisor do prontuário.
  - Aprender o seu estilo de escrita e orientações ao paciente em linguagem simples.
- **Plantão:** relógio de reavaliação de 2 h, pendências, escores (CURB-65, HEART, Wells, PERC, qSOFA, Glasgow, CHA₂DS₂-VASc, Cockcroft-Gault, dose por peso), apoio à decisão com semáforo, discussão do caso, passagem de plantão SBAR e busca Ctrl+K.
- **17/11/2026 (noite):** streaming refeito: a função repassa o fluxo SSE do Gemini sem mexer e o site extrai o texto; se o fluxo não começar em 25 s, o site refaz sem streaming e desliga o streaming por 12 h naquele navegador (`plantaorx:streamOff`). Cronômetro nas esperas, nova tentativa automática em queda de rede, função mantida acordada (GET a cada 4 min), repetição sem `thinkingConfig` se o Gemini recusar o nível. Para testar a função localmente: secret/variável `GEMINI_URL_BASE` aponta para um Gemini simulado.
- **17/11/2026:** respostas em tempo real (streaming), raciocínio por tarefa, conduta livre, documentos por pedido em texto.
- **Novembro de 2026:**
  - Netlify com IA (Gemini via Supabase) e layout Console clínico.
  - Exame físico dirigido por doença e pacientes sincronizados entre computadores.
  - Alta a pedido e evasão, documentos por paciente e prescrição separada em No PS e Casa.
