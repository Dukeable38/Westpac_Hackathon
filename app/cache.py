"""External-call boundary. Replay never evaluates a network callback."""
import hashlib,json,os,threading
from .seed import ROOT
CACHE=ROOT/'demo/cache'
_lock=threading.Lock()

class CacheMiss(RuntimeError): pass

def cached(provider,model,input_value,call,offline=None):
    raw=json.dumps([provider,model,input_value],sort_keys=True,ensure_ascii=False,separators=(',',':'))
    path=CACHE/(hashlib.sha256(raw.encode()).hexdigest()+'.json')
    mode=os.getenv('DEMO_MODE','replay')
    if mode=='replay':
        if path.exists(): return json.loads(path.read_text(encoding='utf-8'))['output']
        if offline is not None: return offline()
        raise CacheMiss(f'No replay evidence for {provider}; network disabled')
    if mode not in ['live','record']: raise ValueError('DEMO_MODE must be replay, record or live')
    value=call()
    if mode=='record':
        CACHE.mkdir(parents=True,exist_ok=True)
        # Only output is persisted: keys are hashes, never credentials or prompts.
        with _lock:
            temp=path.with_suffix('.tmp');temp.write_text(json.dumps({'provider':provider,'model':model,'output':value},ensure_ascii=False),encoding='utf-8');temp.replace(path)
    return value
