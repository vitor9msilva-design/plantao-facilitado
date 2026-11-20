# Gera a versão do Netlify (dados no Supabase, IA pela função do Supabase)
# Uso: python3 build_netlify.py "<URL do Supabase>" "<chave publishable>" ia rapid-handler
#  - 3º argumento "ia" liga as abas de IA; omita para gerar sem IA
#  - 4º argumento = nome (slug) da função de IA no Supabase (padrão plantao-ia)
# Resultado: ../prontos/netlify/index.html + robots.txt -> zipe a pasta e arraste em Netlify > Deploys
import sys, os
aqui = os.path.dirname(os.path.abspath(__file__))
url, key = sys.argv[1], sys.argv[2]
ia = 'true' if (len(sys.argv) > 3 and sys.argv[3] == 'ia') else 'false'
fn = sys.argv[4] if len(sys.argv) > 4 else 'plantao-ia'
s = open(os.path.join(aqui, 'template.html'), encoding='utf-8').read()
base = open(os.path.join(aqui, 'base.json'), encoding='utf-8').read().replace('</', '<\\/')
rev_arq = os.path.join(aqui, 'revisao.json')  # apontamentos da revisão de doses (tela "Revisar um por um")
rev = open(rev_arq, encoding='utf-8').read().replace('</', '<\\/') if os.path.exists(rev_arq) else '{}'
s = s.replace('__BASE__', base).replace('__REVISAO__', rev).replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
cfg = f'<meta name="robots" content="noindex,nofollow"><script>window.PLANTAO_CFG={{url:{url!r},key:{key!r},ia:{ia},fn:{fn!r}}};</script>'
i = s.index('<title>'); s = s[:i] + cfg + s[i:]
pasta = os.path.join(aqui, '..', 'prontos', 'netlify'); os.makedirs(pasta, exist_ok=True)
open(os.path.join(pasta, 'index.html'), 'w', encoding='utf-8').write(s)
open(os.path.join(pasta, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')
print('ok ->', os.path.normpath(pasta), len(s), 'bytes')
