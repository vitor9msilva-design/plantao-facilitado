"""Teste do aviso de 1 hora (conferir exames e medicação). Avança o relógio da página sem esperar.
Rode a partir da raiz do projeto, depois do build:  python3 testes/teste_aviso_conferir.py
"""
import os, pathlib, re, sys
from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
SITE = AQUI / '_site_teste_conferir.html'
src = (AQUI.parent / 'prontos' / 'netlify' / 'index.html').read_text(encoding='utf-8')
SITE.write_text(re.sub(r"url:'https://[^']+'", "url:'http://127.0.0.1:9'", src), encoding='utf-8')
falhas = []
def ok(cond, msg):
    print(('  ok   ' if cond else '  FALHOU ') + msg)
    if not cond: falhas.append(msg)
def rota(r):
    u = r.request.url
    if '/rest/v1/rpc/ler' in u: return r.fulfill(status=200, content_type='application/json', body='[]')
    if '/rest/v1/' in u or '/functions/v1/' in u: return r.fulfill(status=200, content_type='application/json', body='null')
    if 'fonts.g' in u: return r.abort()
    r.continue_()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or None)
    ctx = b.new_context(viewport={'width': 1100, 'height': 900}); ctx.route('**/*', rota)
    pg = ctx.new_page(); erros = []; pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.clock.install()
    pg.goto(SITE.as_uri() + '#abcdefghijklmnopqrstuvwxyz1234'); pg.clock.run_for(1500)
    pg.click('[data-sec="prontuario"]'); pg.clock.run_for(300)
    pg.fill('#pIni', 'A.B.'); pg.fill('#pNotas', 'fem 40a dor abdominal, aguarda exames e analgesia'); pg.clock.run_for(1000)

    print('1) Antes de 1 hora')
    ok(pg.locator('.sb-p.conferir').count() == 0, 'paciente sem destaque')
    ok('Conferir em' in pg.locator('.conf-chip').inner_text(), 'cabeçalho mostra quanto falta para conferir')

    print('2) Depois de 1 hora')
    pg.clock.run_for(61 * 60 * 1000); pg.clock.run_for(31000)
    ok(pg.locator('.sb-p.conferir').count() == 1, 'paciente muda de cor na barra lateral')
    ok('Conferir exames e medicação' in pg.locator('.sb-p.conferir').inner_text(), 'barra lateral diz o que conferir')
    ok(pg.locator('.conf-chip.on [data-conferido]').count() == 1, 'cabeçalho mostra o aviso com o botão Conferido')
    ok('1 hora de espera' in (pg.locator('.toast').inner_text() if pg.locator('.toast').count() else ''), 'aviso aparece uma vez na tela')
    ok('⏰' in pg.title() or '(1)' in pg.title(), 'título da aba mostra a contagem')

    print('3) Conferido')
    pg.click('.conf-chip.on [data-conferido]'); pg.clock.run_for(500)
    ok(pg.locator('.sb-p.conferir').count() == 0 and pg.locator('.conf-chip.on').count() == 0, 'cor volta ao normal')
    ok('Conferir em 1h' in pg.locator('.conf-chip').inner_text() or 'Conferir em 60' in pg.locator('.conf-chip').inner_text(), 'próximo aviso em 1 hora')
    pg.clock.run_for(61 * 60 * 1000); pg.clock.run_for(31000)
    ok(pg.locator('.sb-p.conferir').count() == 1, 'avisa de novo 1 hora depois')
    ok(pg.locator('.sb-p.conferir .sb-t.atras').count() == 1, 'com reavaliação também vencida (2 h), os dois avisos aparecem juntos')

    print('4) Outras seções e celular')
    pg.click('[data-sec="prescricoes"]'); pg.set_viewport_size({'width': 390, 'height': 844}); pg.clock.run_for(500)
    ok(pg.locator('#pbar .pchip.atras, #pbar .pchip.conferir').count() == 1, 'chip do paciente fica destacado fora do prontuário (celular)')
    print('Erros de JavaScript:', erros or 'nenhum')
    if erros: falhas.append('erros de JavaScript')
    b.close()
SITE.unlink()
print('\nRESULTADO:', 'TUDO OK' if not falhas else f'{len(falhas)} falha(s)')
sys.exit(1 if falhas else 0)
