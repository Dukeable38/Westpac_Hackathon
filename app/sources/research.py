"""Code-driven research with seed-first fixtures and a strict replay boundary.

Only extracted identifiers are queried, never invoice prose. Live web evidence is
untrusted; simple facts are parsed by code and free-form summaries do not score.
"""
import os,re,json
from html import unescape
from urllib.parse import urlencode
import httpx
from ..cache import cached,CacheMiss
from ..seed import SEED
from .. import llm

def fetch(url):
    def request():
        with httpx.Client(timeout=5,follow_redirects=False) as client:
            with client.stream('GET',url,headers={'User-Agent':'InvoiceScamChecker-demo/1.0'}) as response:
                response.raise_for_status()
                data=b''
                for chunk in response.iter_bytes():
                    data+=chunk
                    if len(data)>1_000_000: raise ValueError('Research response exceeds size limit')
                return data.decode('utf-8',errors='replace')
    return cached('http','v1',url,request)

def abn_lookup(abn):
    abn=re.sub(r'\D','',abn)
    seed=SEED['abn_registry'].get(abn)
    if seed is not None:
        return cached('abn','seed-v1',abn,lambda:seed,offline=lambda:seed)
    from ..checks.identifiers import abn_valid
    if not abn_valid(abn):return None
    try:
        page=fetch('https://abr.business.gov.au/ABN/View?'+urlencode({'abn':abn}))
        text=unescape(re.sub('<[^>]+>',' ',page));text=' '.join(text.split())
        status=re.search(r'ABN status:\s*(Active|Cancelled)',text,re.I)
        entity=re.search(r'Entity name:\s*(.*?)\s+ABN status:',text,re.I)
        if not status or not entity:return None
        return {'status':status.group(1).title(),'entity_name':entity.group(1),'business_names':[],'abn_from':None,'source':'ABN Lookup live HTML; dates/GST not parsed'}
    except (httpx.HTTPError,CacheMiss,ImportError,ValueError):return None

def domain_history(domain):
    if domain in ['gmail.com','hotmail.com','outlook.com','yahoo.com']:return None
    seed=SEED['domains'].get(domain)
    if seed is not None:return cached('domain','seed-v1',domain,lambda:seed,offline=lambda:seed)
    if not re.fullmatch(r'[a-z0-9.-]{1,253}',domain):return None
    try:
        certs=json.loads(fetch('https://crt.sh/?'+urlencode({'q':domain,'output':'json'})))
        dates=sorted(c['not_before'][:10] for c in certs if c.get('not_before'))
        if dates:return {'first_cert':dates[0],'source':'crt.sh certificate observation'}
    except (httpx.HTTPError,CacheMiss,ImportError,ValueError,KeyError,TypeError):pass
    try:
        data=json.loads(fetch('https://web.archive.org/cdx/search/cdx?'+urlencode({'url':domain,'output':'json','filter':'statuscode:200','limit':'1','fl':'timestamp'})))
        timestamp=data[1][0]
        return {'first_cert':f'{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}','source':'Wayback earliest capture (not domain registration)'}
    except (httpx.HTTPError,CacheMiss,ImportError,ValueError,IndexError,TypeError):return None

def dns_posture(domain):
    seed=SEED['domains'].get(domain)
    if seed:return {k:seed.get(k) for k in ['mx','spf','dmarc']}
    if not re.fullmatch(r'[a-z0-9.-]{1,253}',domain):return None
    try:
        def query(name,type_):return json.loads(fetch('https://dns.google/resolve?'+urlencode({'name':name,'type':type_}))).get('Answer',[])
        mx=query(domain,'MX');txt=query(domain,'TXT');dmarc=query('_dmarc.'+domain,'TXT')
        return {'mx':bool(mx),'spf':any('v=spf1' in r.get('data','') for r in txt),'dmarc':next((r['data'] for r in dmarc if 'v=DMARC1' in r.get('data','')),None)}
    except (httpx.HTTPError,CacheMiss,ImportError,ValueError):return None

def web_search(name):
    from difflib import SequenceMatcher
    seed=next((v for n,v in SEED['web_search'].items() if SequenceMatcher(None,n.lower(),name.lower()).ratio()>.6),None)
    if seed is not None:return cached('search','seed-v1',name,lambda:seed,offline=lambda:seed)
    if os.getenv('SEARCH_PROVIDER')!='tavily' or not os.getenv('TAVILY_API_KEY'):
        return {'unknown':'search not configured'}
    def request():
        response=httpx.post('https://api.tavily.com/search',json={'api_key':os.environ['TAVILY_API_KEY'],'query':name[:200],'max_results':3},timeout=5)
        response.raise_for_status()
        snippets='\n'.join(r.get('content','')[:1000] for r in response.json().get('results',[]))
        return {'summary':llm.summarise('Summarise the available business evidence, with uncertainty. Do not assess fraud risk.',snippets),'unknown':'Live search summary requires human review; no deterministic review/report counts'}
    try:return cached('search','tavily-v1',name,request)
    except (httpx.HTTPError,CacheMiss,ImportError,ValueError):return {'unknown':'Search unavailable or no replay evidence'}
