"""Exploratory: KP marriage verdicts and the Saturn-delay flag for people known to have married.

Same spent Astro-Databank marriages. Every person married, so a working promise rule should say
DENIED rarely; compared with the verdicts for random clock times on the same birth date.

Usage:
    PYTHONPATH=. python tools/kp/adb_verdict_check.py
"""
import json,random,statistics,swisseph as swe
from concurrent.futures import ProcessPoolExecutor
from app.kp.chart import cast
from app.kp.judgment import judge
from app.kp.selection import select
from tools.kp.adb_timing_diagnostics import YEAR,_birth
def one(a):
    rec,jd=a; rng=random.Random('v'+rec['id'])
    b=_birth(rec); c=cast(b)
    v=judge(b,'marriage').verdict
    others=[]
    for _ in range(10):
        b2=_birth(dict(rec,hour=rng.randrange(24),minute=rng.randrange(60)))
        others.append((judge(b2,'marriage').verdict, select(cast(b2),'marriage').delay))
    return {'age':(jd-c.jd_ut)/YEAR,'v':v,'delay':select(c,'marriage').delay,'others':others}
L=json.load(open('data/private/kp_outcomes/adb_locked.json')); births={p['id']:p['birth_jd'] for p in L['people']}
G={r['id']:r for r in json.load(open('data/private/kp_outcomes/adb_gated.json'))}
jobs=[]
for e in json.load(open('data/private/kp_outcomes/adb_events.json')):
    if e['matter']=='marriage':
        y,m,d=map(int,e['date'].split('-')); jd=swe.julday(y,m,d,12.0)
        if 16<=(jd-births[e['id']])/YEAR<60: jobs.append((G[e['id']],jd))
with ProcessPoolExecutor(4) as ex: R=list(ex.map(one,jobs,chunksize=4))
from collections import Counter
print('n',len(R)); print('own verdicts',Counter(r['v'] for r in R))
print('same-day random-time verdicts',Counter(v for r in R for v,_ in r['others']))
d=[r['age'] for r in R if r['delay']]; nd=[r['age'] for r in R if not r['delay']]
print('Saturn delay: n',len(d),'median age',round(statistics.median(d),1),'| no delay n',len(nd),'median',round(statistics.median(nd),1))
print('share delay own',round(len(d)/len(R),3),'same-day',round(sum(x for r in R for _,x in r['others'])/(10*len(R)),3))
