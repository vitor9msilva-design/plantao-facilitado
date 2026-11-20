import os
import http.server, json, time, socketserver, sys
OUT0 = OUT = json.dumps({"caixa1":"===\nDEPARTAMENTO DE EMERGÊNCIA - HSLT\n===\n\n#História da Doença Atual:\nPaciente feminina, 34 anos, refere cefaleia holocraniana há 5 dias, com piora hoje, associada a náuseas e vômitos. Nega febre.","caixa2":"# Exame físico:\n- BEG, lúcida.\n- Neuro: Glasgow 15, sem rigidez de nuca.","caixa3":"# Hipóteses diagnósticas:\n1. Enxaqueca sem aura (?) pelo padrão da dor.","caixa4":"# CONDUTAS:\n- Prescrevo dipirona e metoclopramida EV.","receita":None}, ensure_ascii=False)
class H(http.server.BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*a): sys.stderr.write('GEMINI '+self.path+'\n')
    def do_POST(self):
        n=int(self.headers.get('content-length',0)); body=json.loads(self.rfile.read(n))
        prompt=' '.join(p.get('text','') for c in body.get('contents',[]) for p in c.get('parts',[]))
        global OUT
        if '"destino"' in prompt: OUT=json.dumps({"destino":"observacao","confianca":"media","resumo":"Cefaleia com vômitos, sem sinais de alarme.","motivos":["dor controlada"],"sinais_de_gravidade":[],"exames":[{"exame":"TC de crânio","motivo":"afastar causa secundária","prioridade":"agora"}],"escores_uteis":[],"mudaria_destino":["déficit focal"]},ensure_ascii=False)
        elif '"alta"' in prompt and '"ps"' in prompt: OUT=json.dumps({"titulo":"Cefaleia","ps":"USO ENDOVENOSO\n\n1) Dipirona 1 g EV","alta":"USO ORAL\n\n1) Naproxeno 500 mg","obs":""},ensure_ascii=False)
        elif '"caixa1"' in prompt: OUT=OUT0
        else: OUT='Texto livre de teste: paciente V.M.S, 34 anos, cefaleia. Documento pronto sem lacunas.'
        sys.stderr.write('  cfg '+json.dumps(body.get('generationConfig'))+'\n')
        import os
        if 'streamGenerateContent' in self.path and os.path.exists(os.environ.get('TRAVA_ARQ','/tmp/gem_trava')):
            time.sleep(40); return
        if 'streamGenerateContent' in self.path:
            self.send_response(200); self.send_header('content-type','text/event-stream'); self.send_header('Transfer-Encoding','chunked'); self.end_headers()
            def w(b): self.wfile.write(f"{len(b):x}\r\n".encode()+b+b"\r\n"); self.wfile.flush()
            time.sleep(1.0)
            w(b'data: '+json.dumps({"candidates":[{"content":{"parts":[{"thought":True,"text":"pensando"}]}}]}).encode()+b'\r\n\r\n')
            for i in range(0,len(OUT),40):
                time.sleep(0.15); w(b'data: '+json.dumps({"candidates":[{"content":{"parts":[{"text":OUT[i:i+40]}]}}]},ensure_ascii=False).encode('utf-8')+b'\r\n\r\n')
            self.wfile.write(b"0\r\n\r\n"); self.wfile.flush(); return
        time.sleep(3.0)
        d=json.dumps({"candidates":[{"content":{"parts":[{"text":OUT}]},"finishReason":"STOP"}],"usageMetadata":{"totalTokenCount":10}}).encode()
        self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(d))); self.end_headers(); self.wfile.write(d)
class S(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads=True
S(('127.0.0.1',8790),H).serve_forever()
