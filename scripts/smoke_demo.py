"""Bounded offline integration smoke. Starts and always stops its own server."""
import json,os,socket,subprocess,sys,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]

def main():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env=dict(os.environ,DEMO_MODE='replay',LLM_PROVIDER='fake',DEMO_DELAY_MS='0')
    base=f'http://127.0.0.1:{port}'
    with (ROOT/'smoke-server.log').open('w') as log:
        process=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log)
        try:
            with httpx.Client(base_url=base,timeout=20,trust_env=False) as client:
                for _ in range(100):
                    if process.poll() is not None: raise RuntimeError('Server exited; see smoke-server.log')
                    try:
                        if client.get('/health').status_code==200: break
                    except httpx.ConnectError: pass
                    time.sleep(.1)
                else: raise RuntimeError('Server not ready in 10 seconds')
                ui=client.get('/');assert ui.status_code==200 and '<html' in ui.text.lower()
                results=[]
                for path,band in zip(sorted((ROOT/'demo/invoices').glob('*.pdf')),['genuine','high_risk','high_risk','check']):
                    with path.open('rb') as f: response=client.post('/api/check',files={'file':(path.name,f,'application/pdf')},data={'customer_id':'cust_greenline'})
                    response.raise_for_status();result=response.json();assert result['band']==band,(path.name,result['band'])
                    results.append(result);print(path.name,result['score'],result['band'])
                check=results[3]['check_id']
                with client.stream('GET',f'/api/check/{check}/events') as response:
                    response.raise_for_status();lines=list(response.iter_lines())
                assert 'event: complete' in lines and 'event: tier_start' in lines and 'event: signal' in lines
                chat=client.post(f'/api/check/{check}/chat',json={'message':'Yes, new business, I met the owner at the expo and ordered this'})
                chat.raise_for_status();assert chat.json()['band']=='genuine'
                decision=client.post(f'/api/check/{check}/decision',json={'decision':'hold'})
                decision.raise_for_status();assert decision.json()['sha256']==results[3]['sha256']
                print('PASS: UI, four PDFs, SSE to completion, chat, receipt')
        finally:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill();process.wait(timeout=5)
    return 0

if __name__=='__main__': raise SystemExit(main())
