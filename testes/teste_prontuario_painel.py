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
    "perguntas": ["Faz uso de anticoagulante ou antiagregante?", "Teve episódio de confusão mental ou queda?"],
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

    print('1) Painel lateral só com ícones (computador)')
    ok(pg.locator('#prontSide .rail-i .ri-btn').count() == 7, '7 ícones no painel (sem o pedido de imagem)')
    ok(pg.locator('.ri-btn[data-tip="Reavaliação"]').count() == 1, 'cada ícone tem o nome para mostrar ao passar o mouse')
    ok(pg.locator('.flyout').count() == 0, 'começa fechado, sem ocupar espaço')
    caixa = pg.evaluate("(() => { const r = document.querySelector('#prontSide').getBoundingClientRect(); return [Math.round(r.right), innerWidth, Math.round(r.width), Math.round(document.querySelector('#prontMain').getBoundingClientRect().width)]; })()")
    ok(abs(caixa[0] - caixa[1]) <= 20 and caixa[2] <= 60 and caixa[3] >= 760, f'painel estreito colado à direita e centro largo (painel {caixa[2]} px, centro {caixa[3]} px)')
    pg.hover('.ri-btn[data-painel="escores"]'); pg.wait_for_timeout(250)
    op = pg.evaluate("getComputedStyle(document.querySelector('.ri-btn[data-painel=\"escores\"]'), '::after').opacity")
    ok(op == '1', 'nome aparece ao passar o mouse')
    pg.click('.ri-btn[data-painel="reav"]'); pg.wait_for_timeout(250)
    ok(pg.locator('.flyout#painel-reav .rail-body').count() == 1, 'clicar abre a seção numa janela ao lado')
    pg.click('.ri-btn[data-painel="escores"]'); pg.wait_for_timeout(250)
    ok(pg.locator('.flyout').count() == 1 and pg.locator('.flyout#painel-escores').count() == 1, 'abrir outra fecha a anterior')
    pg.click('.img-h'); pg.wait_for_timeout(300)
    ok(pg.locator('#painel-imagem.open #tEx').count() == 1 and pg.locator('.flyout').count() == 0, 'pedido de imagem (centro) fecha a janela do painel')
    pg.click('.ri-btn[data-painel="pend"]'); pg.wait_for_timeout(250)
    pg.click('.fly-x'); pg.wait_for_timeout(250)
    ok(pg.locator('.flyout').count() == 0, '× fecha a janela')
    pg.click('.ri-btn[data-painel="pend"]'); pg.wait_for_timeout(250); pg.keyboard.press('Escape'); pg.wait_for_timeout(250)
    ok(pg.locator('.flyout').count() == 0, 'Esc fecha a janela')
    ok(pg.locator('#prontMain .tools-paper').count() == 0, 'textos rápidos não ficam na coluna principal')

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
    ok(pg.locator('.ri-btn[data-painel="internacao"] .ri-dot.alerta').count() == 1, 'ícone de internação ganha alerta')
    ok(pg.locator('.perg-card .perg').count() == 2, 'perguntas sugeridas aparecem ao lado da HDA')
    ok(pg.locator('.hda-duo #pC1').count() == 1 and pg.locator('.hda-duo [data-act="cbox-copy"][data-target="pC1"]').count() == 1, 'HDA continua com o botão Copiar')
    pg.click('.perg-x >> nth=1'); pg.wait_for_timeout(250)
    ok(pg.locator('.perg-card .perg').count() == 1, 'Ignorar tira a pergunta')
    ok(pg.locator('[data-perg-incluir]').is_disabled(), 'sem resposta, o botão de acrescentar fica desligado')
    pg.fill('[data-perg-r="0"]', 'nega uso de anticoagulante'); pg.wait_for_timeout(100)
    n0 = len(pedidos); pg.click('[data-perg-incluir]'); pg.wait_for_timeout(1500)
    ok(any('Acrescente à HDA' in t and 'nega uso de anticoagulante' in t for t in pedidos[n0:]), 'resposta vai para a IA acrescentar à HDA')
    pg.click('[data-perg-ign="todas"]'); pg.wait_for_timeout(250)
    ok(pg.locator('.perg-card').count() == 0 and pg.locator('#pC1').count() == 1, '"Ignorar todas" some com o quadro e a HDA fica')
    pg.click('.alerta-int [data-painel="internacao"]'); pg.wait_for_timeout(300)
    ok(pg.locator('.flyout#painel-internacao [data-intern]').count() == 1, '"Pedido de internação" abre a janela certa')

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
    ok(pg.locator('#prontSide .rail').is_visible() and pg.locator('.ri-btn').count() == 0, 'no celular continua a lista em sanfona')
    print('Erros de JavaScript:', erros or 'nenhum')
    if erros: falhas.append('erros de JavaScript')
    b.close()
SITE.unlink()
print('\nRESULTADO:', 'TUDO OK' if not falhas else f'{len(falhas)} falha(s)')
sys.exit(1 if falhas else 0)
