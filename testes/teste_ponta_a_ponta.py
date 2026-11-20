"""Teste de ponta a ponta do site do Netlify + função de IA (Deno) + Gemini simulado.
Pré-requisitos: ver COMO-RODAR.md. Rode a partir da pasta testes/:  python3 teste_ponta_a_ponta.py
"""
import json, time, os, pathlib
from playwright.sync_api import sync_playwright
AQUI = pathlib.Path(__file__).resolve().parent
COFRE = 'abcdefghijklmnopqrstuvwxyz1234'
SITE = AQUI / '_site_teste.html'
src = (AQUI.parent / 'prontos' / 'netlify' / 'index.html').read_text(encoding='utf-8')
import re
src = re.sub(r"url:'https://[^']+'", "url:'http://127.0.0.1:8000'", src)
SITE.write_text(src, encoding='utf-8')
DB = {}
def rota(r):
    u = r.request.url
    if '/rest/v1/rpc/ler' in u: return r.fulfill(status=200, content_type='application/json', body=json.dumps([{'colecao':k[0],'id':k[1],'dados':v} for k,v in DB.items()]))
    if '/rest/v1/rpc/gravar' in u:
        b = json.loads(r.request.post_data); DB[(b['p_colecao'], b['p_id'])] = b['p_dados']; return r.fulfill(status=200, content_type='application/json', body='null')
    r.continue_()
def montar(pg, ini):
    pg.click('#sbNovo'); pg.wait_for_timeout(200); pg.fill('#pIni', ini); pg.fill('#pNotas', 'fem 34a cefaleia 5d, vomitos')
    if pg.locator('#pLocal').count(): pg.fill('#pLocal', 'HSLT')
    t0 = time.time(); pg.click('#pGo'); primeiro = None
    while time.time() - t0 < 60:
        if primeiro is None and pg.locator('#pC1').count() and pg.input_value('#pC1'): primeiro = time.time() - t0
        if pg.locator('.pwait').count() == 0 and pg.locator('#pC4').count(): break
        pg.wait_for_timeout(100)
    ok = pg.locator('#pC4').count() and pg.input_value('#pC4')
    return f"1º texto {primeiro and round(primeiro,1)} s · total {round(time.time()-t0,1)} s · {'OK' if ok else 'FALHOU'} {pg.locator('.perr').all_inner_texts()}"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or None); ctx = b.new_context(viewport={'width':1440,'height':900})
    ctx.route('**/rest/v1/**', rota); ctx.route('**/fonts.g*/**', lambda r: r.abort())
    pg = ctx.new_page(); erros = []; pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto(SITE.as_uri() + '#' + COFRE); pg.wait_for_timeout(1200)
    print('A) streaming normal       :', montar(pg, 'A.A'))
    trava = os.environ.get('TRAVA_ARQ', '/tmp/gem_trava'); open(trava, 'w').write('1')
    print('B) streaming travado      :', montar(pg, 'B.B'), '| plano B ativado:', pg.evaluate("!!localStorage.getItem('plantaorx:streamOff')"))
    print('C) depois, sem streaming  :', montar(pg, 'C.C'))
    os.remove(trava)
    print('Erros de JavaScript:', erros or 'nenhum'); b.close()
SITE.unlink()
