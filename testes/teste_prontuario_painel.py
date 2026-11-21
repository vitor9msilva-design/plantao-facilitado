"""Teste do prontuário com IA simulada: modelo de HDA no pedido, trava de exames inventados,
aviso de internação e painel lateral em sanfona. Não precisa da função nem do Gemini.
Rode a partir da raiz do projeto, depois do build:  python3 testes/teste_prontuario_painel.py
"""
import json, os, pathlib, re, sys
from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
SITE = AQUI / '_site_teste_pront.html'
src = (AQUI.parent / 'prontos' / 'netlify' / 'index.html').read_text(encoding='utf-8')
SITE.write_text(re.sub(r"url:'https://[^']+'", "url:'http://127.0.0.1:9'", src), encoding='utf-8')
COFRE = 'abcdefghijklmnopqrstuvwxyz1234'
falhas, pedidos = [], []
def ok(cond, msg):
    print(('  ok   ' if cond else '  FALHOU ') + msg)
    if not cond: falhas.append(msg)

RESPOSTA = {
    "caixa1": "===\nDEPARTAMENTO DE EMERGÊNCIA - HSLT\n===\n\n#História da Doença Atual:\nPaciente masculino, 72 anos, com tosse produtiva há 3 dias, febre e dispneia.",
    "caixa2": "# Exame físico:\n- REG, taquipneico.\n- AR: estertores em base direita.\n\n# Exames complementares:\n>> Exames laboratoriais: Hb 12,5 | Leuco 10.900 | Plaq 521.000\n>> Exames de imagem:\n- TC de Crânio: sem alterações",
    "caixa3": "# Hipóteses diagnósticas:\n1. Pneumonia comunitária.\n\n# Escores:\n- CURB-65: 3 (idade ≥ 65 anos, FR ≥ 30, PAS < 90); ureia não informada.",
    "caixa4": "# CONDUTAS:\n- Dipirona 1 g EV.\n- Hemograma, PCR, ureia, creatinina, sódio e potássio.\n- Radiografia de tórax PA e perfil.\n- Atenção: CURB-65 = 3, indicação de internação.",
    "gravidade": {"destino": "internacao", "motivo": "CURB-65 = 3 com hipotensão e taquipneia em idoso."},
    "receita": None}

ADAPT = {"ps": "USO ENDOVENOSO\n\n1) Ondansetrona 4 mg/2 mL [Vonau®] ------------------------ 01 ampola\nAplicar 4 mg, via endovenosa lenta.", "casa": "USO NASAL\n\n1) Furoato de mometasona 50 mcg/jato [Nasonex®] ------------------------ 01 frasco\nAplicar 2 jatos em cada narina, 1 vez ao dia.", "obs": "Retirada a dipirona; incluída mometasona com a dose das suas receitas."}

def rota(r):
    u = r.request.url
    if '/rest/v1/rpc/ler' in u: return r.fulfill(status=200, content_type='application/json', body='[]')
    if '/rest/v1/' in u: return r.fulfill(status=200, content_type='application/json', body='null')
    if '/functions/v1/' in u:
        if r.request.method != 'POST': return r.fulfill(status=200, body='{}')
        b = json.loads(r.request.post_data or '{}'); txt = ' '.join(m.get('content', '') for m in b.get('messages', []) if isinstance(m.get('content'), str))
        pedidos.append(txt)
        if not b.get('stream'):  # modo sem streaming: a função responde {"text": ...}
            corpo = RESPOSTA if '"caixa1"' in txt else ADAPT if 'AJUSTAR a receita' in txt else 'ok'
            return r.fulfill(status=200, content_type='application/json', body=json.dumps({'text': corpo if isinstance(corpo, str) else json.dumps(corpo, ensure_ascii=False)}, ensure_ascii=False))
        if 'AJUSTAR a receita' in txt: return r.fulfill(status=200, content_type='text/plain; charset=utf-8', body=json.dumps(ADAPT, ensure_ascii=False))
        if '"caixa1"' in txt: return r.fulfill(status=200, content_type='text/plain; charset=utf-8', body=json.dumps(RESPOSTA, ensure_ascii=False))
        return r.fulfill(status=200, content_type='text/plain; charset=utf-8', body='ok')
    r.continue_()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or None)
    ctx = b.new_context(viewport={'width': 1100, 'height': 900})
    ctx.route('**/*', rota)
    pg = ctx.new_page(); erros = []; pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto(SITE.as_uri() + '#' + COFRE); pg.wait_for_timeout(1200)
    pg.click('[data-sec="prontuario"]'); pg.wait_for_timeout(300)

    print('1) Painel lateral em sanfona')
    ok(pg.locator('#prontSide .rail').count() == 1, 'painel escuro aparece')
    ok(pg.locator('.rail-qi').count() == 0, 'sem ícones no topo do painel')
    ok(pg.locator('#prontSide .rail-btn[data-painel="imagem"]').count() == 0 and pg.locator('#prontMain .img-h').count() == 1, 'pedido de imagem fica na coluna central')
    caixa = pg.evaluate("(() => { const r = document.querySelector('#prontSide').getBoundingClientRect(); return [Math.round(r.right), innerWidth, Math.round(document.querySelector('#prontMain').getBoundingClientRect().width)]; })()")
    ok(abs(caixa[0] - caixa[1]) <= 20 and caixa[2] >= 540, f'painel encostado à direita e centro largo (direita {caixa[0]}/{caixa[1]} px, centro {caixa[2]} px)')
    ok(pg.locator('.rail-it.open').count() == 1, 'só uma seção aberta')
    pg.click('.rail-btn[data-painel="reav"]'); pg.wait_for_timeout(200)
    ok(pg.locator('#painel-reav.open .rail-body').count() == 1 and pg.locator('.rail-it.open').count() == 1, 'abrir Reavaliação fecha a anterior')
    pg.click('.img-h'); pg.wait_for_timeout(300)
    ok(pg.locator('#painel-imagem.open #tEx').count() == 1 and pg.locator('.rail-it.open').count() == 0, 'abrir pedido de imagem fecha a seção do painel')
    pg.click('.rail-btn[data-painel="escores"]'); pg.wait_for_timeout(300)
    ok(pg.locator('#painel-escores.open').count() == 1 and pg.locator('#painel-imagem.open').count() == 0, 'abrir Escores fecha o pedido de imagem')
    pg.click('.rail-btn[data-painel="escores"]'); pg.wait_for_timeout(200)
    ok(pg.locator('.rail-it.open').count() == 0, 'clicar no nome aberto fecha a seção')
    ok(pg.locator('#prontMain .tools-paper').count() == 0, 'textos rápidos saíram da coluna principal')

    print('2) Prontuário com IA')
    pg.fill('#pIni', 'J.S.'); pg.fill('#pLocal', 'HSLT')
    pg.fill('#pNotas', 'masc 72a tosse produtiva 3d, febre, dispneia, FR 32, PA 85x50, estertores base D. sintomaticos, exames lab e imagem')
    pg.click('#pGo'); pg.wait_for_timeout(1500)
    pr = next((t for t in pedidos if '"caixa1"' in t), '')
    ok('MODELO DE HDA DESTE MÉDICO' in pr, 'pedido à IA leva o modelo de HDA da biblioteca')
    ok('NUNCA podem aparecer' in pr and '"gravidade"' in pr and '# Escores:' in pr and 'DETALHE cada item' in pr, 'pedido leva as regras novas (exames, escores, conduta, gravidade)')
    c2 = pg.input_value('#pC2')
    ok('Hb 12,5' not in c2 and 'Exames complementares' not in c2 and 'estertores' in c2, 'exames que o médico não informou são removidos (exame físico fica)')
    ok('CURB-65: 3' in pg.input_value('#pC3'), 'escore calculado aparece nas hipóteses')
    ok(pg.locator('.alerta-int').count() == 1, 'aviso de indicação de internação aparece sozinho')
    ok(pg.locator('.rail-btn[data-painel="internacao"] .rail-n.alerta').count() == 1, 'Pedido de internação ganha alerta no painel')
    pg.click('.alerta-int [data-painel="internacao"]'); pg.wait_for_timeout(300)
    ok(pg.locator('#painel-internacao.open [data-intern]').count() == 1, '"Pedido de internação" abre o painel certo')

    print('3) Com exames informados, a trava não apaga')
    pg.fill('#pNotas', 'masc 72a tosse 3d, Hb 12,5 Leuco 10900, rx torax com consolidacao em base D'); pg.click('#pGo'); pg.wait_for_timeout(1500)
    ok('Hb 12,5' in pg.input_value('#pC2'), 'exames informados permanecem')

    print('4) Adaptar a receita por texto')
    rx = pg.locator('#pRx option', has_text='Síndrome gripal').first.get_attribute('value')
    pg.select_option('#pRx', rx); pg.wait_for_timeout(400)
    antes_casa = pg.input_value('#pRxCasa')
    ok(pg.locator('#pRxAdapt').count() == 1, 'campo "Adaptar a receita" aparece junto da receita')
    pg.fill('#pRxAdapt', 'adicione mometasona; retire a dipirona'); pg.press('#pRxAdapt', 'Enter'); pg.wait_for_timeout(1500)
    ped = next((t for t in reversed(pedidos) if 'AJUSTAR a receita' in t), '')
    ok('Nasonex' in ped and 'LINHAS DAS RECEITAS DO MÉDICO' in ped, 'pedido leva a linha de mometasona das suas receitas')
    ok('adicione mometasona; retire a dipirona' in ped and antes_casa[:40] in ped, 'pedido leva o que mudar e a receita atual')
    ok('Nasonex' in pg.input_value('#pRxCasa') and 'Ondansetrona' in pg.input_value('#pRxPs'), 'caixas No PS e Para casa são atualizadas')
    ok(pg.locator('.ptag', has_text='ajustada pela IA').count() >= 1 and 'Retirada a dipirona' in pg.locator('.adapt-obs').inner_text(), 'mostra o selo "ajustada pela IA" e o que mudou')
    pg.click('#pRxDesfazer'); pg.wait_for_timeout(300)
    ok(pg.input_value('#pRxCasa') == antes_casa, '"Desfazer" volta a receita anterior')

    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(300)
    ok(pg.locator('#prontSide .rail').is_visible(), 'painel aparece no celular')
    print('Erros de JavaScript:', erros or 'nenhum')
    if erros: falhas.append('erros de JavaScript')
    b.close()
SITE.unlink()
print('\nRESULTADO:', 'TUDO OK' if not falhas else f'{len(falhas)} falha(s)')
sys.exit(1 if falhas else 0)
