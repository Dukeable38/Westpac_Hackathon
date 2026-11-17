import json
import pytest
from app import llm,cache

def test_replay_never_calls_network(monkeypatch):
    monkeypatch.setenv('DEMO_MODE','replay')
    def forbidden():raise AssertionError('Network callback executed')
    with pytest.raises(cache.CacheMiss):cache.cached('unrecorded-test','test','nothing',forbidden)

def test_openai_compatible_adapter(monkeypatch):
    monkeypatch.setenv('DEMO_MODE','live');monkeypatch.setenv('LLM_PROVIDER','openai_compatible')
    monkeypatch.setenv('LLM_BASE_URL','https://provider.example/v1');monkeypatch.setenv('LLM_MODEL','test')
    monkeypatch.setenv('LLM_API_KEY','mock-test-only')
    seen=[]
    class Response:
        status_code=200
        def raise_for_status(self):pass
        def json(self):return {'choices':[{'message':{'content':'{"choice":"NEW_BUSINESS"}'}}]}
    class Client:
        def __init__(self,**kw):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,url,**kw):seen.append((url,kw));return Response()
    monkeypatch.setattr(llm.httpx,'Client',Client)
    assert llm.classify('Claim?',['NEW_BUSINESS','NONE'],'new business')=='NEW_BUSINESS'
    assert seen[0][0]=='https://provider.example/v1/chat/completions'
    assert 'score' not in seen[0][1]['json']['messages'][1]['content']

def test_anthropic_adapter(monkeypatch):
    import anthropic
    from types import SimpleNamespace
    monkeypatch.setenv('DEMO_MODE','live');monkeypatch.setenv('LLM_PROVIDER','anthropic')
    monkeypatch.setenv('ANTHROPIC_API_KEY','mock-test-only')
    class Client:
        def __init__(self,**kwargs):self.messages=self
        def create(self,**kwargs):return SimpleNamespace(content=[SimpleNamespace(type='text',text='{"answer":"Active fictional entity"}')])
    monkeypatch.setattr(anthropic,'Anthropic',Client)
    assert llm.summarise('Status?','Fictional entity is active')=='Active fictional entity'

def test_extraction_retries_invalid_json(monkeypatch):
    monkeypatch.setenv('DEMO_MODE','live');monkeypatch.setenv('LLM_PROVIDER','anthropic')
    replies=iter(['invalid','{"abn":"88015795425"}'])
    monkeypatch.setattr(llm,'_complete',lambda prompt:next(replies))
    assert llm.extract('sanitised').abn=='88015795425'

def test_invalid_choice_rejected(monkeypatch):
    monkeypatch.setenv('DEMO_MODE','live');monkeypatch.setenv('LLM_PROVIDER','anthropic')
    monkeypatch.setattr(llm,'_complete',lambda prompt:'{"choice":"MAKE_SAFE"}')
    with pytest.raises(ValueError):llm.classify('Claim?',['NONE'],'untrusted')

def test_openai_compatible_backs_off_on_429_and_honours_retry_after(monkeypatch):
    monkeypatch.setenv('DEMO_MODE','live');monkeypatch.setenv('LLM_PROVIDER','openai_compatible')
    monkeypatch.setenv('LLM_BASE_URL','https://provider.example/v1');monkeypatch.setenv('LLM_MODEL','test-backoff')
    monkeypatch.setenv('LLM_API_KEY','mock-test-only');monkeypatch.setenv('LLM_TIMEOUT','45')
    sleeps=[];timeouts=[]
    monkeypatch.setattr(llm.time,'sleep',sleeps.append)
    statuses=iter([429,429,503,200])
    class Response:
        def __init__(self,code):self.status_code=code;self.headers={'retry-after':'7'} if code==429 and not sleeps else {}
        def raise_for_status(self):pass
        def json(self):return {'choices':[{'message':{'content':'{"choice":"NONE"}'}}]}
    class Client:
        def __init__(self,**kw):timeouts.append(kw.get('timeout'))
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,url,**kw):return Response(next(statuses))
    monkeypatch.setattr(llm.httpx,'Client',Client)
    assert llm.classify('Backoff?',['NEW_BUSINESS','NONE'],'plain text')=='NONE'
    assert timeouts==[45.0]
    assert sleeps==[7.0,4.0,8.0]


def test_replay_miss_for_real_provider_falls_back_offline(monkeypatch):
    """Demo safety: an unrecorded input in replay uses the offline reader instead of failing (and never calls out)."""
    from app import llm
    monkeypatch.setenv('DEMO_MODE', 'replay')
    monkeypatch.setenv('LLM_PROVIDER', 'openai_compatible')
    monkeypatch.setenv('LLM_MODEL', 'never-recorded/model')
    monkeypatch.setattr(llm, '_complete', lambda *a, **k: (_ for _ in ()).throw(AssertionError('network called')))
    assert llm.classify('Is this urgent?', ['urgent', 'not_urgent'], 'pay within 24 hours') in ('urgent', 'not_urgent')
