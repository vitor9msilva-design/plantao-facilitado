# Roteiro para transformar o Plantão Facilitado em produto

Hoje o app é um arquivo HTML único, de um médico só, com acesso por link secreto. Para vender a outros médicos e serviços, a ordem sugerida está abaixo. Cada fase deixa o app utilizável.

## Fase 1: base técnica (antes de qualquer cliente)
- **Separar o código em módulos.** O `template.html` tem cerca de 3.350 linhas.
  - Migrar para um projeto **Vite + TypeScript**, mantendo o HTML/CSS atual.
  - Módulos sugeridos: `store/`, `ia/`, `prontuario/`, `prescricoes/`, `documentos/`, `escores/`, `ui/`.
  - O resultado continua sendo um site estático, que o Netlify publica.
- **Conteúdo fora do código:** `base.json` vira uma tabela de conteúdo versionada (prescrições, documentos e HDAs por especialidade), com flag de revisão médica.
- **Testes automáticos:**
  - Transformar `testes/` em suíte Playwright com `npm test`.
  - Cobrir o prontuário, a separação No PS / Casa (as 216 receitas), os documentos, a sincronização e o plano B do streaming.
  - Rodar no GitHub Actions a cada mudança.
- **Repositório no GitHub** com `CLAUDE.md` na raiz. Deploy no Netlify ligado ao repositório, sem arrastar zip.

## Fase 2: contas e vários usuários
- **Login de verdade** com Supabase Auth: e-mail com link mágico, ou Google.
  - O "cofre" do link secreto vira o `user_id`, e o RLS (row level security) do Postgres libera só os dados de cada um.
  - Manter um modo "link de plantão" de acesso rápido, mas atrelado à conta.
- **Perfil do médico:** nome, CRM/UF, cidade, hospital e sistema de prontuário (Soul MV, Tasy, MV PEP…).
- **Tabelas novas:** `usuarios`, `edicoes` (o que hoje é `itens` e `meta`), `pacientes_temp` (TTL de 4 h, apagados por um job agendado do Supabase), `uso_ia` (tokens e custo por usuário).
- **IA por usuário:**
  - A função valida o JWT do usuário e não mais o cofre.
  - Limite de uso por plano, com contagem de tokens a partir de `usageMetadata`.
  - Nenhum dado de paciente é guardado nos logs.

## Fase 3: produto clínico
- **Adaptadores de prontuário:** formatos de saída para **Soul MV** (atual) e **Tasy**, com campos e quebras de linha no padrão de cada um, escolhidos no perfil.
- **Biblioteca por especialidade:** clínica, pediatria (doses por peso exigem validação e revisão própria), ortopedia, GO.
- **Revisão médica do conteúdo:** fluxo "rascunho → revisado por CRM X", com data, visível no app.
- **Sinais vitais estruturados** que alimentam escores e exame físico. Alertas de alergia e interação na receita.
- **Ditado por voz** (Web Speech API) para as anotações.
- **PWA instalável** no celular e no PC do hospital, com modo offline para prescrições e documentos.

## Fase 4: negócio e conformidade
- **LGPD:**
  - Política de privacidade, termo de uso e registro do tratamento de dados.
  - Dados de pacientes mínimos (iniciais), temporários e criptografados.
  - DPA com os provedores de IA (Google ou Anthropic), usando planos pagos que não treinam com os dados.
  - Avaliar se é preciso enquadramento como software de apoio à decisão clínica.
- **CFM:** deixar claro que o conteúdo gerado é apoio e que a decisão e a assinatura são do médico. Nenhuma prescrição sai sem revisão humana.
- **Pagamentos:** assinatura mensal com Stripe ou Mercado Pago, com plano gratuito limitado e plano pessoal com cota de IA. Para hospitais, um plano institucional com vários médicos.
- **Página de venda**, onboarding guiado (perfil → primeiro prontuário em 2 minutos) e suporte.
- **Métricas sem dados sensíveis:** tempo economizado por atendimento, prontuários por plantão e satisfação.

## Decisões técnicas já tomadas (e por quê)
- **Edge Function intermediária:** a chave da IA nunca fica no navegador, e o hospital bloqueia sites de IA mas libera o Supabase.
- **Gemini Flash como padrão, com troca automática de modelo:** custo cerca de 10× menor que modelos maiores, e a troca evita ficar fora do ar.
- **Streaming com plano B:** o texto aparece rápido, e se o fluxo travar o site cai sozinho no modo comum.
- **Pacientes só com iniciais e apagados em 4 h:** reduz o risco de LGPD a quase zero e não substitui o prontuário oficial.
- **Edições do usuário em camada separada do conteúdo base:** atualizar a biblioteca nunca apaga o que o médico personalizou.

## Primeiro pedido sugerido no Claude Code
> Leia CLAUDE.md, LEIA-ME.md e este ROADMAP. Comece a Fase 1: crie um projeto Vite + TypeScript que gere exatamente o mesmo site que `fonte/template.html` + `fonte/base.json` geram hoje. Separe o JavaScript em módulos sem mudar o comportamento, mantenha os dois builds (Netlify e Claude) e transforme os testes de `testes/` em `npm test`. Não altere conteúdo médico nem doses.
