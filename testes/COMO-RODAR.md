# Testes de ponta a ponta

Este teste simula o caminho real **site do Netlify → função `rapid-handler` (Deno) → Gemini**, sem gastar créditos e sem internet para o Google.

## Pré-requisitos
- Python 3 com o Playwright (`pip install playwright && playwright install chromium`).
  (Se o Chromium já estiver instalado em outro lugar, aponte com `CHROMIUM=/caminho/do/chrome`.)
- Deno (`npm i deno`, ou https://deno.com).
- O site já gerado em `prontos/netlify/` (`python3 fonte/build_netlify.py …`).

## Como rodar (3 terminais, a partir da raiz do projeto)
```bash
# 1) Gemini simulado (porta 8790): responde ao prontuário, à decisão, ao Gerar receita e a texto livre;
#    trava o streaming quando existe o arquivo /tmp/gem_trava
python3 testes/gemini_simulado.py

# 2) A função de verdade, apontando para o simulado (porta 8000)
COFRE=abcdefghijklmnopqrstuvwxyz1234 GEMINI_API_KEY=teste GEMINI_URL_BASE=http://127.0.0.1:8790 \
  deno run --allow-net --allow-env supabase/funcao-rapid-handler/index.ts

# 3) O teste
python3 testes/teste_ponta_a_ponta.py
```
Resultado esperado (19/11/2026):
- **A)** O texto começa em cerca de 1,3 s e termina em cerca de 3 s.
- **B)** O plano B entra em cerca de 28 s e o streaming fica desligado.
- **C)** Cerca de 3 s, já sem streaming.
- Nenhum erro de JavaScript.
