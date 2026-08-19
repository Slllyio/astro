"""Rebuild htjah_h9_calibration.json — ch. XIII (9th house) worked charts 86-97."""
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
 row(86,"Karaka","Sun (exalt, 9th)",False,[P("kendra_trikona"),DIG("exalted"),CNJ(True),CNJ(True),KTR("papa")],"fairly strong"),
 row(87,"Lord","Moon (9L, 10th)",False,[P("kendra_trikona"),ASP(False),ASP(False),ASP(True),CNJ(False)],"weak"),
 row(87,"Karaka","Sun (exalt, 6th)",False,[P("dusthana"),DIG("exalted"),CNJ(False),ASP(False),ASP(False)],"weak"),
 row(88,"Lord","Mercury (9L exalt, 9th)",False,[P("kendra_trikona"),DIG("exalted"),CNJ(False),CNJ(False),CNJ(True),CNJ(False)],"moderately good"),
 row(88,"Karaka","Sun (9th)",False,[P("kendra_trikona"),CNJ(True),CNJ(False),CNJ(True),CNJ(False)],"moderate"),
 row(89,"Bhava","9th (Cancer)",True,[OCC(False),BASP(True)],"weak"),
 row(89,"Karaka","Sun (exalt, 6th)",False,[P("dusthana"),DIG("exalted"),CNJ(False),KTR("papa"),ASP(False)],"afflicted"),
 row(90,"Lord","Mercury (9L, 10th)",False,[P("kendra_trikona"),CNJ(False)],"moderately good"),
 row(90,"Karaka","Sun (debil, kendra)",False,[P("kendra_trikona"),DIG("debilitated")],"weak"),
 row(91,"Karaka","Sun (10th, papakartari)",False,[P("kendra_trikona"),CNJ(True),KTR("papa"),ASP(True)],"moderately good"),
 row(92,"Bhava","9th",True,[BASP(True),BASP(False)],"fairly good"),
 row(92,"Karaka","Sun (4th)",False,[P("kendra_trikona"),CNJ(True),CNJ(True),CNJ(True)],"fairly good"),
 row(93,"Bhava","9th",True,[],"moderately good"),
 row(93,"Lord","Venus (9L inimical, 7th)",False,[P("kendra_trikona"),DIG("inimical"),CNJ(False),CNJ(True),KTR("papa")],"weak"),
 row(94,"Bhava","9th (Libra)",True,[OCC(False),KTR("subha"),BASP(True)],"fairly strong"),
 row(94,"Lord","Venus (9L, 10th)",False,[P("kendra_trikona"),CNJ(True),ASP(True)],"fairly powerful"),
 row(94,"Karaka","Sun (9th, neechabhanga)",False,[P("kendra_trikona"),NB(),KTR("subha"),ASP(True)],"moderately good"),
 row(95,"Bhava","9th (Capricorn)",True,[OCC(True),OCC(False),BASP(False)],"fairly strong"),
 row(95,"Karaka","Sun (exalt, 12th)",False,[P("dusthana"),DIG("exalted"),CNJ(True),ASP(False)],"fairly good"),
 row(96,"Bhava","9th",True,[OCC(True)],"fairly good"),
 row(96,"Lord","Jupiter (9L, 4th, varg)",False,[P("kendra_trikona"),VG(),CNJ(False),ASP(False)],"moderate"),
 row(96,"Karaka","Sun (Lagna)",False,[P("kendra_trikona"),ASP(False)],"fairly good"),
 row(97,"Lord","Sun (9L+karaka, 12th)",False,[P("dusthana"),CNJ(True),ASP(True),KTR("papa")],"weak"),
]
out={"house":9,"chapter":"ch13 (Vol. II)","holdout_rule":"chart_no % 3 == 0","rows":rows}
Path("scratchpad/htjah_h9_calibration.json").write_text(json.dumps(out,indent=1))
print(f"h9: {len(rows)} rows")
