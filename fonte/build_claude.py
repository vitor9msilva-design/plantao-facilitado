# Gera a versão do Claude (com IA própria do Claude) a partir de template.html + base.json
# Uso: python3 build_claude.py   -> cria ../prontos/versao-claude.html
import os
aqui = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(aqui, 'template.html'), encoding='utf-8').read()
base = open(os.path.join(aqui, 'base.json'), encoding='utf-8').read().replace('</', '<\\/')
saida = os.path.join(aqui, '..', 'prontos', 'versao-claude.html')
open(saida, 'w', encoding='utf-8').write(s.replace('__BASE__', base))
print('ok ->', os.path.normpath(saida))
