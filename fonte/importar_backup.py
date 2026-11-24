"""Grava no conteúdo base (fonte/base.json) as receitas, documentos e HDAs que o médico corrigiu no site.

O site guarda as edições no Supabase, por cima do base.json, separadas pelo código do link. Trazendo
as edições para o base.json, elas passam a valer em qualquer link, prévia ou versão futura.

Uso (a partir da raiz do projeto):
    python3 fonte/importar_backup.py caminho/do/plantao-backup.json          # só mostra o que vai mudar
    python3 fonte/importar_backup.py caminho/do/plantao-backup.json --gravar # grava no base.json

O backup sai do site em: Configurações → Backup → Gerar backup → Baixar arquivo (ou Copiar).
Não traz pacientes. Itens que o médico apagou no site NÃO são apagados do base.json; só são listados.
"""
import json, os, sys

aqui = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2:
    sys.exit(__doc__)
bk = json.load(open(sys.argv[1], encoding='utf-8'))
if bk.get('app') != 'plantao-rx' or 'itens' not in bk:
    sys.exit('Isso não parece um backup do Plantão Facilitado (falta "app": "plantao-rx" ou "itens").')
gravar = '--gravar' in sys.argv
base_arq = os.path.join(aqui, 'base.json')
base = json.load(open(base_arq, encoding='utf-8'))

trocados, novos, apagados = [], [], []
for chave, v in bk['itens'].items():
    if '--' not in chave:
        continue
    secao, iid = chave.split('--', 1)
    if secao not in ('prescricoes', 'documentos', 'hdas'):
        continue
    lista = base[secao]['itens']
    pos = next((i for i, x in enumerate(lista) if x['id'] == iid), None)
    if v.get('apagado'):
        apagados.append(f'{secao}: {iid}')
        continue
    item = v.get('item')
    if not item:
        continue
    item = {k: val for k, val in item.items() if not k.startswith('_')}
    if pos is None:
        lista.append(item); novos.append(f"{secao}: {item.get('nome', iid)}")
    elif lista[pos] != item:
        lista[pos] = item; trocados.append(f"{secao}: {item.get('nome', iid)}" + (' (revisado)' if not item.get('rascunho') else ''))

print(f'Backup de {bk.get("gerado", "?")}')
print(f'- {len(trocados)} itens corrigidos vão substituir o conteúdo base')
for t in trocados: print('    ' + t)
print(f'- {len(novos)} itens novos vão entrar no conteúdo base')
for t in novos: print('    ' + t)
if apagados:
    print(f'- {len(apagados)} itens apagados no site (continuam no base.json; apague à mão se quiser):')
    for t in apagados: print('    ' + t)
if gravar:
    raw = open(base_arq, encoding='utf-8').read()
    open(base_arq, 'w', encoding='utf-8').write(json.dumps(base, ensure_ascii=False, indent=None if '\n' not in raw.strip()[:2000] else 1))
    print('Gravado em fonte/base.json. Rode o build e os testes.')
else:
    print('Nada foi gravado. Para gravar, rode de novo com --gravar.')
