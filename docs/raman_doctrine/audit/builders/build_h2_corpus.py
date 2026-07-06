"""Reconstruct htjah_h2_calibration.json — ch. V (2nd house) worked charts 40-48."""
import json
from pathlib import Path
R, N, B = "Rasi", "Navamsa", "both"
def P(w): return {"type":"placement","where":w,"why":f"placed ({w})"}
def VG(): return {"type":"vargottama","frame":B,"why":"vargottama"}
def NB(): return {"type":"neechabhanga","why":"neechabhanga"}
def DIG(s,fr=R): return {"type":"dignity","state":s,"frame":fr,"why":f"{s} ({fr})"}
def ASP(b,fr=R): return {"type":"aspect","benefic":b,"frame":fr,"why":f"aspect ({fr})"}
def BASP(b): return {"type":"bhava_aspect","benefic":b,"why":"house aspect"}
def OCC(b): return {"type":"occupant","benefic":b,"why":"occupant"}
def CNJ(b,fr=R,ex=False): return {"type":"conjunct","benefic":b,"frame":fr,"exalted":ex,"why":f"conjunct ({fr})"}
def KTR(k): return {"type":"kartari","kind":k,"why":f"{k}kartari"}
def row(chart,role,subject,additive,findings,expected,note=""):
    return {"chart":chart,"role":role,"subject":subject,"additive":additive,"findings":findings,"expected":expected,"note":note}
rows=[
 # Chart 40 (TRAIN)
 row(40,"Bhava","2nd (4 planets, cancellations)",True,[OCC(False),OCC(False),OCC(False),OCC(True),BASP(True)],"very strong",
     "own-sign Mars + neechabhanga Moon + exalted-Jupiter aspect = 'very strongly situated'; occupant cancellations unseen by scheme"),
 row(40,"Lord","Mars (2L own, 2nd)",False,[DIG("own"),CNJ(True),ASP(True)],"very strong"),
 row(40,"Dhana","Jupiter (exalt, 10th)",False,[P("kendra_trikona"),DIG("exalted"),ASP(True)],"very strong"),
 # Chart 41 (TRAIN)
 row(41,"Bhava","2nd (Rajayoga, 3 planets)",True,[OCC(False),OCC(True),OCC(False)],"fairly strong",
     "Sun/Mercury/Mars Rajayoga -> 'strong'; Rajayoga occupancy unseen"),
 row(41,"Lord","Saturn (2L, Lagna)",False,[P("kendra_trikona"),CNJ(False,N)],"moderately good",
     "Raman 'moderately powerful'; kendra placement over-scores"),
 row(41,"Dhana","Jupiter (12th, vargottama)",False,[P("dusthana"),CNJ(False),VG()],"moderate"),
 # Chart 42 (HOLDOUT)
 row(42,"Bhava","2nd (Mars in, Jupiter asp)",True,[OCC(False),BASP(False)],"weak"),
 row(42,"Lord","Saturn (2L, 3rd)",False,[DIG("inimical",N)],"weak"),
 row(42,"Dhana","Jupiter (8th)",False,[P("dusthana"),ASP(False)],"weak"),
 # Chart 43 (TRAIN)
 row(43,"Bhava","2nd (Aries, clean)",True,[],"fairly strong",
     "'not aspected by any planet, hence fairly strong' -- clean house UNDER-scored"),
 row(43,"Lord","Mars (2L own, 9th)",False,[P("kendra_trikona"),DIG("own"),CNJ(True,N),CNJ(False,N)],"moderately good",
     "trikona+own -> very powerful; Raman 'moderately good'"),
 row(43,"Dhana","Jupiter (11th debil, NB)",False,[NB()],"fairly good"),
 # Chart 44 (TRAIN)
 row(44,"Bhava","2nd (Virgo)",True,[OCC(False),BASP(False)],"moderate",
     "Sun occupant + Saturn aspect -> 'ordinarily disposed'"),
 row(44,"Lord","Mercury (2L, 3rd)",False,[CNJ(False)],"moderate"),
 row(44,"Dhana","Jupiter (4th, w/ Mars YK)",False,[P("kendra_trikona"),CNJ(True)],"fairly strong"),
 # Chart 45 (HOLDOUT)
 row(45,"Bhava","2nd (Libra, clean)",True,[BASP(True)],"fairly good",
     "'free from affliction ... fairly well disposed' -- clean house"),
 row(45,"Lord","Venus (2L, 5th, 3 malefics)",False,[P("kendra_trikona"),DIG("friendly"),CNJ(False),CNJ(False),CNJ(False),ASP(True),DIG("friendly",N),ASP(True,N),CNJ(False,N)],"weak",
     "Venus joined by Sun+Moon+Rahu -> 'feebly strong'; optimistic combine over-rescues"),
 # Chart 46 (TRAIN)
 row(46,"Bhava","2nd (Saturn in, Jupiter asp)",True,[OCC(False),BASP(True)],"moderate",
     "'ordinarily situated'"),
 row(46,"Dhana","Jupiter (8th)",False,[P("dusthana")],"weak"),
 # Chart 48 (HOLDOUT)
 row(48,"Bhava","2nd (Virgo, Saturn asp)",True,[BASP(True)],"moderately good",
     "aspected by neutral Saturn -> 'moderately good'"),
 row(48,"Lord","Mercury (2L, 3rd, friendly)",False,[DIG("friendly"),CNJ(True),DIG("own",N)],"moderately good"),
 row(48,"Dhana","Jupiter (inimical, Navamsa lord)",False,[DIG("inimical"),CNJ(True),P("kendra_trikona"),DIG("friendly",N)],"moderately good"),
]
out={"house":2,"chapter":"ch5 (Vol. I)","holdout_rule":"chart_no % 3 == 0","rows":rows}
Path("scratchpad/htjah_h2_calibration.json").write_text(json.dumps(out,indent=1))
print(f"h2: {len(rows)} rows; HOLDOUT={sum(1 for r in rows if r['chart']%3==0)}")
