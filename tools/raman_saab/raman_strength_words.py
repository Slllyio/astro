"""Frozen word-miner (R1 gate 1, FIDELITY_FIXES_PREREG.md): Raman's own strong/weak words about
the house lord and karaka in each golden row's cited passage, vs the engine pillars.

Usage:
    python -m tools.raman_saab.raman_strength_words   (needs /tmp/claude-0/re/full.json row dump)
"""
import json,re,sys; sys.path.insert(0,'.')
from app.raman_saab.doctrine.sources import _resolve_file
R=json.load(open('/tmp/claude-0/re/full.json'))
G={}
for l in open('tests/fixtures/raman_goldens.jsonl',encoding='utf-8'):
    if l.strip() and not l.startswith('#'): r=json.loads(l); G[r['id']]=r
TXT={b:_resolve_file(b).read_text(encoding='utf-8').split('\n') for b in ('HTJAH-I','HTJAH-II','NH')}
ORD={1:'(?:first|1st|lagna|ascendant)',2:'(?:second|2nd)',3:'(?:third|3rd)',4:'(?:fourth|4th)',5:'(?:fifth|5th)',6:'(?:sixth|6th)',7:'(?:seventh|7th)',8:'(?:eighth|8th)',9:'(?:ninth|9th)',10:'(?:tenth|10th)',11:'(?:eleventh|11th)',12:'(?:twelfth|12th)'}
WEAK=r'\b(weak|weakened|powerless|afflicted|blemished|feeble|feebly|debilitated|not strong|not sufficiently strong|badly placed|ill.?disposed|not well|spoiled|spoilt|damaged|crippled)\b'
STRONG=r'\b(strong|strongly|powerful|powerfully|fortified|well.?disposed|well.?placed|well.?fortified|exalted|free from affliction|unafflicted|not afflicted|fairly good|quite good|very good|excellent)\b'
def read(book,lines,house,karaka):
    txt=' '.join(l.strip() for l in lines)
    sents=re.split(r'(?<=[.!?])\s+',txt)
    out={'lord':[], 'karaka':[]}
    lordpat=re.compile(r'(%s\s+lord|lord\s+of\s+(?:the\s+)?%s|lord\s+of\s+lagna|lagnadhipati|lagna\s+lord)'%(ORD[house],ORD[house]),re.I) if house!=1 else re.compile(r'(lord of lagna|lagnadhipati|lagna lord|ascendant lord|lord of the ascendant|first lord)',re.I)
    karpat=re.compile(r'(karaka|%s)'%karaka,re.I)
    for s in sents:
        w=bool(re.search(WEAK,s,re.I)); st=bool(re.search(STRONG,s,re.I))
        if not (w or st): continue
        lab='weak' if (w and not st) else 'strong' if (st and not w) else 'both'
        if lordpat.search(s): out['lord'].append((lab,s[:160]))
        if karpat.search(s): out['karaka'].append((lab,s[:160]))
    return out
rows=[]
for r in R:
    rid=r['key'].split(' ')[0]; g=G[rid]; book=g['book']
    cites=[c for c in g['citations'] if c.startswith(book+':')]
    if not cites: continue
    a=int(re.search(r':(\d+)',cites[0]).group(1)); b=int(cites[-1].split('-')[-1].split(':')[-1])
    lines=TXT[book][max(0,a-45):b+25]
    w=read(book,lines,r['house'],r['karaka'])
    def vote(items):
        labs=[x[0] for x in items if x[0]!='both']
        if not labs: return None
        return 'weak' if labs.count('weak')>labs.count('strong') else 'strong' if labs.count('strong')>labs.count('weak') else 'split'
    rows.append(dict(key=r['key'],book=book,raman=r['raman'],engine=r['engine'],lord_word=vote(w['lord']),lord_strong=r['lord_strong'],lord_disp=r['lord_disp'],lord_hard=r['lord_hard'],karaka_word=vote(w['karaka']),karaka_strong=r['karaka_strong'],karaka_disp=r['karaka_disp'],cast=r['cast'],ex_lord=w['lord'][:3],ex_kar=w['karaka'][:3]))
json.dump(rows,open('/tmp/claude-0/re/words.json','w'),indent=0)
import collections as C
def xt(name,a,b,rows):
    c=C.Counter((x[a],x[b]) for x in rows if x[a] is not None and x[b] is not None)
    print('\n##',name); 
    for k,v in sorted(c.items()): print('  ',k,v)
B=[x for x in rows if x['cast']=='birth']
print('rows with a lord word:',sum(1 for x in rows if x['lord_word']),'karaka word:',sum(1 for x in rows if x['karaka_word']))
xt('Raman lord word vs engine lord_strong (cast charts)','lord_word','lord_strong',B)
xt('Raman lord word vs engine lord disposition (cast)','lord_word','lord_disp',B)
xt('Raman lord word vs engine lord_hard (cast)','lord_word','lord_hard',B)
xt('Raman karaka word vs engine karaka_strong (cast)','karaka_word','karaka_strong',B)
xt('Raman karaka word vs karaka disposition (cast)','karaka_word','karaka_disp',B)
xt('Raman lord word vs Raman VERDICT','lord_word','raman',rows)
xt('Raman karaka word vs Raman VERDICT','karaka_word','raman',rows)
