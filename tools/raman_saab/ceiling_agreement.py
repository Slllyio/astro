import json,random
key=json.load(open('docs/raman_saab/ceiling_check/blind_key.json'))
C=json.load(open('docs/raman_saab/ceiling_check/labels_C.json')); D=json.load(open('/tmp/claude-0/blind/labels_D.json'))
ids=sorted(key)
ORD={'favourable':0,'mixed':1,'afflicted':2}
def kappa(a,b,w=False):
    cats=['favourable','mixed','afflicted','none']
    n=len(a)
    def wt(x,y):
        if x==y: return 1.0
        if not w or x=='none' or y=='none': return 0.0
        return 1-abs(ORD[x]-ORD[y])/2
    po=sum(wt(x,y) for x,y in zip(a,b))/n
    pa={c:a.count(c)/n for c in cats}; pb={c:b.count(c)/n for c in cats}
    pe=sum(pa[x]*pb[y]*wt(x,y) for x in cats for y in cats)
    return (po-pe)/(1-pe) if pe<1 else 1.0
def stats(sel):
    g=[key[i]['gold'] for i in sel]; c=[C[i]['label'] for i in sel]; d=[D[i]['label'] for i in sel]; e=[key[i]['E'] or 'none' for i in sel]
    acc=lambda x,y: sum(p==q for p,q in zip(x,y))/len(x)
    return {'n':len(sel),'C_vs_gold':acc(c,g),'D_vs_gold':acc(d,g),'C_vs_D':acc(c,d),'engine_vs_gold':acc(e,g),
            'k_C_gold':kappa(c,g),'k_D_gold':kappa(d,g),'k_C_D':kappa(c,d),
            'kw_C_gold':kappa(c,g,True),'kw_D_gold':kappa(d,g,True),'kw_C_D':kappa(c,d,True)}
def boot(sel,f,n=10000):
    rnd=random.Random(20261030); v=sorted(f(stats([rnd.choice(sel) for _ in sel])) for _ in range(n)); return round(v[250],3),round(v[9749],3)
prim=stats(ids); A=(prim['C_vs_gold']+prim['D_vs_gold'])/2
print('PRIMARY',{k:round(v,3) for k,v in prim.items()}); print(' A=',round(A,3),'CI',boot(ids,lambda s:(s['C_vs_gold']+s['D_vs_gold'])/2),'C-D CI',boot(ids,lambda s:s['C_vs_D']))
sec=[i for i in ids if not (C[i]['label']=='none' and D[i]['label']=='none')]
s2=stats(sec); print('SECONDARY (drop both-none)',{k:round(v,3) for k,v in s2.items()})
s3=[i for i in ids if C[i]['label']!='none' and D[i]['label']!='none']
s3s=stats(s3); print('TERTIARY (both gave a label)',{k:round(v,3) for k,v in s3s.items()}, 'A=',round((s3s['C_vs_gold']+s3s['D_vs_gold'])/2,3))
import collections
print('both-agree-but-differ-from-gold:',[(i,key[i]['key'],key[i]['gold'],C[i]['label']) for i in s3 if C[i]['label']==D[i]['label']!=key[i]['gold']])
print('pairs C,gold',collections.Counter((C[i]['label'],key[i]['gold']) for i in ids).most_common())
