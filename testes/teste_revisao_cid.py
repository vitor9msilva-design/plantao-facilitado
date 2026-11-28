"""Teste da revisão de doses ("Revisar um por um") e do CID nos documentos.
Não precisa da função nem do Gemini: o Supabase é simulado aqui mesmo.
Rode a partir da raiz do projeto, depois do build:  python3 testes/teste_revisao_cid.py
(Se o Chromium estiver em outro lugar: CHROMIUM=/caminho/do/chrome python3 testes/teste_revisao_cid.py)
"""
import json, os, pathlib, re, sys
from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
SITE = AQUI / '_site_teste_revisao.html'
src = (AQUI.parent / 'prontos' / 'netlify' / 'index.html').read_text(encoding='utf-8')
# simula uma revisão de doses NOVA (data posterior): todos os apontamentos voltam a ficar pendentes,
# mesmo que o médico já tenha revisado tudo no conteúdo base
src = src.replace('"data": "2026-11-20"', '"data": "2099-01-01"', 1)
SITE.write_text(re.sub(r"url:'https://[^']+'", "url:'http://127.0.0.1:9'", src), encoding='utf-8')
COFRE = 'abcdefghijklmnopqrstuvwxyz1234'
DB = {}
falhas = []
def ok(cond, msg):
    print(('  ok   ' if cond else '  FALHOU ') + msg)
    if not cond: falhas.append(msg)

def rota(r):
    u = r.request.url
    if '/rest/v1/rpc/ler' in u:
        return r.fulfill(status=200, content_type='application/json', body=json.dumps([{'colecao': k[0], 'id': k[1], 'dados': v} for k, v in DB.items()]))
    if '/rest/v1/rpc/gravar' in u:
        b = json.loads(r.request.post_data); DB[(b['p_colecao'], b['p_id'])] = b['p_dados']
        return r.fulfill(status=200, content_type='application/json', body='null')
    if '/functions/v1/' in u:  # sem IA neste teste
        return r.fulfill(status=503, content_type='application/json', body='{"erro":"sem IA no teste"}')
    r.continue_()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or None)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.route('**/rest/v1/**', rota); ctx.route('**/functions/v1/**', rota); ctx.route('**/fonts.g*/**', lambda r: r.abort())
    pg = ctx.new_page(); erros = []; pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto(SITE.as_uri() + '#' + COFRE); pg.wait_for_timeout(1200)

    print('1) Revisão um por um (Prescrições)')
    chip = pg.locator('[data-revstart]')
    ok(chip.count() == 1, 'botão "Revisar um por um" aparece')
    ok('crítico' in chip.inner_text(), 'botão mostra quantos são críticos')
    n0 = int(pg.locator('[data-cat="rascunhos"] .n').inner_text())
    chip.click(); pg.wait_for_timeout(300)
    ok(pg.locator('.revbar').count() == 1, 'barra de revisão aparece')
    ok(pg.locator('.ap.crit').count() >= 1, 'primeiro item tem apontamento crítico')
    primeiro = pg.locator('#detail h2').inner_text()
    pg.locator('#detail [data-act="copy"], #detail [data-copy-field], #detail [data-act="cbox-copy"], #detail [data-act="combo-copyall"]').first.click(); pg.wait_for_timeout(200)
    ok('apontamento crítico' in pg.locator('.toast').inner_text(), 'copiar receita com apontamento crítico avisa')
    ok(pg.locator('[data-apcorr]').count() >= 2, 'cada apontamento tem "Confirmar mudança"')
    pg.locator('.apont-acts [data-apcorr]').click(); pg.wait_for_timeout(400)
    ok('editada por você' in pg.locator('.toast').inner_text() and not [1 for (c, k), v in DB.items() if c == 'itens' and v.get('item', {}).get('nome') == primeiro],
       'receita já corrigida à mão: "Confirmar" não mexe e avisa')
    pg.click('[data-act="rev-ok"]'); pg.wait_for_timeout(400)
    segundo = pg.locator('#detail h2').inner_text()
    ok(segundo != primeiro, f'"Revisado, próximo" avança ({primeiro} → {segundo})')
    gravado = [v for (c, k), v in DB.items() if c == 'itens' and v.get('item', {}).get('nome') == primeiro]
    ok(gravado and gravado[0]['item'].get('revisadoEm') and gravado[0]['item'].get('apontOk'), 'revisão gravada na nuvem com data')
    pg.click('[data-act="rev-pular"]'); pg.wait_for_timeout(300)
    ok(pg.locator('#detail h2').inner_text() != segundo, '"Pular" avança')
    pg.click('[data-act="rev-sair"]'); pg.wait_for_timeout(300)
    ok(pg.locator('.revbar').count() == 0, '"Sair" fecha a revisão')
    ok(int(pg.locator('[data-cat="rascunhos"] .n').inner_text()) == n0 - 1, 'contador "A revisar" caiu 1')
    # item revisado mostra o selo e os apontamentos recolhidos
    pg.click('[data-cat="todas"]'); pg.fill('#q', primeiro); pg.wait_for_timeout(300); pg.locator('#list .card').first.click(); pg.wait_for_timeout(300)
    ok(pg.locator('.badge.ok').count() == 1, 'selo "Revisado em" aparece')
    ok(pg.locator('details.apont.ok').count() == 1, 'apontamentos ficam recolhidos depois de conferidos')
    pg.fill('#q', ''); pg.wait_for_timeout(200)

    pg.fill('#q', 'Crise aguda de gota'); pg.wait_for_timeout(300); pg.locator('#list .card').first.click(); pg.wait_for_timeout(300)
    pg.locator('[data-apcorr]').first.click(); pg.wait_for_timeout(400)
    salvo = [v['item'] for (c, k), v in DB.items() if c == 'itens' and v.get('item', {}).get('nome') == 'Crise aguda de gota']
    txt = ' '.join(a['texto'] for a in salvo[0]['abas']) if salvo else ''
    ok('Colchicina 0,5 mg' in txt and 'Colchicina 0,6 mg' not in txt, '"Confirmar mudança" aplica a correção na receita (colchicina)')
    ok(pg.locator('.ap-feita').count() == 1 or pg.locator('details.apont.ok').count() == 1, 'apontamento aparece como aplicado')
    pg.fill('#q', ''); pg.wait_for_timeout(200)

    print('2) CID na aba Documentos')
    pg.click('[data-sec="documentos"]'); pg.wait_for_timeout(300)
    pg.fill('#q', 'Laboratório dor torácica'); pg.wait_for_timeout(300); pg.locator('#list .card').first.click(); pg.wait_for_timeout(300)
    ok(pg.input_value('#docCid') == 'R07.4', 'CID sugerido do modelo (R07.4)')
    ok('CID: R07.4' in pg.input_value('#rx'), 'CID entra no texto do pedido')
    pg.fill('#docCid', 'i20.0 · angina'); pg.press('#docCid', 'Enter'); pg.locator('#rx').click(); pg.wait_for_timeout(300)
    ok('CID: I20.0' in pg.input_value('#rx') and 'R07.4' not in pg.input_value('#rx'), 'trocar o CID atualiza o texto (I20.0)')
    pg.fill('#q', 'Tomografia de crânio'); pg.wait_for_timeout(300); pg.locator('#list .card').first.click(); pg.wait_for_timeout(300)
    ok(pg.input_value('#docCid') == '' and 'CID: ________' in pg.input_value('#rx'), 'sem CID, o campo fica em branco para preencher')
    pg.fill('#q', 'Atestado de afastamento (dias)'); pg.wait_for_timeout(300); pg.locator('#list .card').first.click(); pg.wait_for_timeout(300)
    ok(pg.locator('#docCid').count() == 0 and pg.locator('.cid-aviso').count() == 1, 'atestado: sem CID automático e com aviso do CFM')
    pg.fill('#q', ''); pg.wait_for_timeout(200)

    print('3) CID nos documentos do paciente (Prontuário)')
    pg.click('[data-sec="prontuario"]'); pg.wait_for_timeout(300)
    pg.click('#sbNovo'); pg.wait_for_timeout(200)
    pg.fill('#pIni', 'T.C.'); pg.fill('#pNotas', 'masc 50a dor toracica em aperto ha 2h, PA 150x90')
    rx = pg.locator('#pRx option', has_text='Síndrome gripal').first.get_attribute('value')
    pg.select_option('#pRx', rx); pg.wait_for_timeout(400)
    pg.locator('[data-docpac]').first.click(); pg.wait_for_timeout(300)
    pg.fill('#dpQ', 'tomografia de crânio'); pg.wait_for_timeout(200); pg.locator('[data-dpdoc]').first.click(); pg.wait_for_timeout(800)
    ok(pg.input_value('#dpCid') == 'J11', 'documento do paciente usa o CID da doença ligada ao caso (J11)')
    ok('CID: J11' in pg.input_value('#dpTxt'), 'CID do paciente no texto')
    pg.fill('#dpCid', 'R51'); pg.press('#dpCid', 'Tab'); pg.wait_for_timeout(200)
    ok('CID: R51' in pg.input_value('#dpTxt') and 'J11' not in pg.input_value('#dpTxt'), 'trocar o CID atualiza o documento do paciente')
    pg.click('#dpVoltar'); pg.wait_for_timeout(200)
    pg.fill('#dpQ', 'atestado de afastamento'); pg.wait_for_timeout(200); pg.locator('[data-dpdoc]').first.click(); pg.wait_for_timeout(800)
    ok(pg.locator('#dpCid').count() == 0 and 'J11' not in pg.input_value('#dpTxt'), 'atestado do paciente não recebe CID sozinho')

    print('Erros de JavaScript:', erros or 'nenhum')
    if erros: falhas.append('erros de JavaScript')
    b.close()
SITE.unlink()
print('\nRESULTADO:', 'TUDO OK' if not falhas else f'{len(falhas)} falha(s)')
sys.exit(1 if falhas else 0)
