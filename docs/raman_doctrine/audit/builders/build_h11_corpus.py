"""Rebuild htjah_h11_calibration.json — ch. XV (11th house) worked charts 210-218."""
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
    return {"chart":chart,"role":role,"subject":subject,"additive":additive,
            "findings":findings,"expected":expected,"note":note}
rows=[
 row(210,"Lord","Moon (11L debil, 3rd)",False,[DIG("debilitated"),CNJ(False),CNJ(False),ASP(False,N)],"weak"),
 row(211,"Bhava","11th (Aries)",True,[OCC(False),OCC(True),KTR("papa")],"weak"),
 row(211,"Lord","Mars (11L, Lagna)",False,[P("kendra_trikona"),CNJ(True),ASP(False),DIG("exalted",N),ASP(True,N)],"fairly good"),
 row(212,"Bhava","11th (Libra)",True,[OCC(True),OCC(False),OCC(True),OCC(True)],"fairly strong"),
 row(212,"Lord","Venus (11L own, 11th)",False,[DIG("own"),CNJ(True),CNJ(False),CNJ(True),ASP(True,N)],"very strong"),
 row(213,"Bhava","11th",True,[],"moderate"),
 row(213,"Lord","Saturn (11L, 3rd)",False,[CNJ(False),ASP(True),ASP(False)],"moderate"),
 row(214,"Bhava","11th (Gemini)",True,[OCC(False),BASP(True),KTR("papa")],"weak"),
 row(215,"Bhava","11th (Cancer)",True,[OCC(False),OCC(True),BASP(False)],"moderate"),
 row(215,"Lord","Moon (11L own, 11th)",False,[DIG("own"),CNJ(False),ASP(False),CNJ(True,N,True),ASP(False,N)],"moderate"),
 row(216,"Bhava","11th (Pisces)",True,[],"moderate"),
 row(216,"Lord","Jupiter (11L debil, 9th)",False,[P("kendra_trikona"),NB(),CNJ(False),ASP(False)],"weak"),
 row(217,"Bhava","11th (Pisces)",True,[OCC(False),BASP(True),BASP(True)],"fairly strong"),
 row(217,"Lord","Jupiter (11L, 6th)",False,[P("dusthana"),DIG("inimical"),CNJ(False),DIG("own",N)],"moderately good"),
 row(218,"Bhava","11th (Leo)",True,[],"moderate"),
 row(218,"Lord","Sun (11L exalt, kendra)",False,[P("kendra_trikona"),DIG("exalted"),CNJ(False),CNJ(True)],"fairly strong"),
]
out={"house":11,"chapter":"ch15 (Vol. II)","holdout_rule":"chart_no % 3 == 0","rows":rows}
Path("scratchpad/htjah_h11_calibration.json").write_text(json.dumps(out,indent=1))
print(f"h11: {len(rows)} rows")
