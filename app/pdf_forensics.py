"""Inspect PDF drawing/text evidence before sending any text to the LLM."""
import io
import re
import unicodedata
import pdfplumber
from pdfplumber.utils import extract_text
from pypdf import PdfReader

def _white(c):
    color=c.get('non_stroking_color')
    return color == 1 or isinstance(color,(tuple,list)) and bool(color) and all(v>=0.97 for v in color)

def _hidden(c,p):
    dark_background=any(r.get('fill') and not _white(r) and r['x0']<=c['x0'] and r['x1']>=c['x1'] and r['top']<=c['top'] and r['bottom']>=c['bottom'] for r in p.rects+p.curves)
    return c['size'] < 3 or (_white(c) and not dark_background) or c['x0'] < 0 or c['x1'] > p.width+1 or c['top'] < 0 or c['bottom'] > p.height+1

def _bank(text):
    b=re.findall(r'BSB\s*(\d{3}[- ]?\d{3})',text,re.I)
    a=re.findall(r'Acc?ount\s+(\d[\d ]{5,15})',text,re.I)
    return (b[-1],re.sub(r'\s','',a[-1])) if b and a else None

def analyse(data):
    if not data.startswith(b'%PDF-') or len(data)>10*1024*1024:
        raise ValueError('Upload a PDF smaller than 10 MB')
    reader=PdfReader(io.BytesIO(data))
    if reader.is_encrypted or len(reader.pages)>20:
        raise ValueError('Encrypted PDFs and PDFs over 20 pages are not supported')
    for page in reader.pages:
        content=page.get_contents()
        if content:
            # Refuse unsupported invisible-rendering documents rather than risk
            # passing their hidden glyphs to an extraction model.
            if any(op==b'Tr' and args and int(args[0]) in (3,7) for args,op in content.operations):
                raise ValueError('Invisible text rendering requires manual review; PDF not sent to AI')
    ends=[m.end() for m in re.finditer(rb'%%EOF',data)]
    prior=None
    if len(ends)>1:
        try:
            prior=pdfplumber.open(io.BytesIO(data[:ends[0]]))
        except Exception:
            prior=None
    hidden=[]; texts=[]; original=None; tampered=False; overlay=False
    revision_unknown=len(ends)>1 and prior is None
    with pdfplumber.open(io.BytesIO(data)) as doc:
        for i,p in enumerate(doc.pages):
            visible=[c for c in p.chars if not _hidden(c,p)]
            hidden.extend(c['text'] for c in p.chars if _hidden(c,p))
            text=extract_text(visible) or ''
            if prior and i<len(prior.pages):
                pp=prior.pages[i]
                old=extract_text([c for c in pp.chars if not _hidden(c,pp)]) or ''
                oldbank=_bank(old)
                # Appended content is painted after earlier content. Compare the drawing
                # sequence, not the filename, and keep the later payment block legible.
                prefix=len(pp.chars)
                same=all(a['text']==b['text'] and abs(a['x0']-b['x0'])<0.1 for a,b in zip(p.chars[:prefix],pp.chars))
                if not same:revision_unknown=True
                added=p.chars[prefix:] if same else []
                added_visible=[c for c in added if not _hidden(c,p)]
                addedtext=extract_text(added_visible) or ''
                newbank=_bank(addedtext)
                if oldbank and newbank and oldbank!=newbank:
                    original=oldbank; tampered=True
                    bankchars=[c for c in added_visible if c['text'].isdigit()]
                    overlay=any(abs(a['top']-b['top'])<2 and abs(a['x0']-b['x0'])<2 for a in bankchars for b in pp.chars if b['text'].isdigit())
                    ymin=min(c['top'] for c in added_visible); ymax=max(c['bottom'] for c in added_visible)
                    xmin=min(c['x0'] for c in added_visible); xmax=max(c['x1'] for c in added_visible)
                    remaining=[c for c in p.chars[:prefix] if not _hidden(c,p) and not (ymin-1<=c['top']<=ymax+1 and xmin-1<=c['x0']<=xmax+1)]
                    text=(extract_text(remaining) or '')+'\n'+addedtext
            texts.append(text)
    if prior: prior.close()
    text='\n'.join(texts)
    invisible=[c for c in text if unicodedata.category(c)=='Cf']
    text=''.join(c for c in text if unicodedata.category(c)!='Cf')
    mixed=[]
    def strip_mixed(match):
        token=match.group()
        scripts={unicodedata.name(c,'').split(' ')[0] for c in token if c.isalpha()}
        if 'LATIN' in scripts and scripts.intersection({'GREEK','CYRILLIC'}):
            mixed.append(token);return '[mixed-script identifier removed]'
        return token
    text=re.sub(r'[^\s]+',strip_mixed,text)
    suspicious=bool(hidden or invisible or mixed)
    return {'text':text,'hidden':suspicious,'hidden_instruction':bool(re.search(r'AI|assistant|ignore|mark as|LOW RISK',''.join(hidden),re.I)), 'revisions':len(ends),'revision_unknown':revision_unknown,'tampered':tampered,'overlay':overlay,'original':original,'metadata':{str(k):str(v) for k,v in (reader.metadata or {}).items()}}
