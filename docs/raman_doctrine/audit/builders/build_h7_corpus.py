"""Rebuild htjah_h7_calibration.json — ch. XI (7th house) worked charts 1-16."""
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
 row(1,"Bhava","7th (Pisces)",True,[OCC(False)],"weak"),
 row(1,"Lord","Jupiter (7L)",False,[P("kendra_trikona"),VG(),DIG("own",R),DIG("own",N),ASP(True,R),ASP(False,R),ASP(False,N),ASP(False,N)],"very strong"),
 row(1,"Karaka","Venus",False,[P("kendra_trikona"),DIG("friendly",R),ASP(True,R),ASP(False,R)],"fairly strong"),
 row(2,"Bhava","7th (Aquarius)",True,[OCC(True),BASP(True),BASP(True),BASP(True)],"fairly powerful"),
 row(2,"Lord","Saturn (7L)",False,[P("kendra_trikona"),DIG("friendly",R),KTR("subha")],"fairly strong"),
 row(2,"Karaka","Venus",False,[DIG("friendly",R),CNJ(True,R),KTR("papa")],"moderately good"),
 row(3,"Bhava","7th",True,[BASP(True),BASP(True)],"fairly strong"),
 row(3,"Lord","Venus (7L, Lagna)",False,[P("kendra_trikona"),CNJ(True,R)],"fairly strong"),
 row(4,"Bhava","7th (Pisces)",True,[OCC(False),OCC(False),BASP(False),BASP(False)],"afflicted"),
 row(4,"Lord","Jupiter (7L)",False,[P("dusthana")],"weak"),
 row(4,"Karaka","Venus",False,[CNJ(False,R),CNJ(True,R),ASP(False,R)],"afflicted"),
 row(5,"Bhava","7th",True,[OCC(False),BASP(False)],"weak"),
 row(5,"Lord","Mercury (7L)",False,[DIG("friendly",R),KTR("papa")],"moderate"),
 row(5,"Karaka","Venus",False,[P("kendra_trikona"),DIG("inimical",R),ASP(False,R)],"weak"),
 row(6,"Bhava","7th (Virgo)",True,[OCC(True),BASP(False),BASP(False)],"moderate"),
 row(7,"Bhava","7th (Scorpio)",True,[],"moderate"),
 row(7,"Lord","Mars (7L)",False,[DIG("friendly",R),CNJ(False,R),ASP(True,R),ASP(True,R)],"fairly good"),
 row(7,"Karaka","Venus (8th)",False,[P("dusthana"),ASP(True,R)],"moderate"),
 row(8,"Bhava","7th (Leo)",True,[OCC(True),OCC(True),OCC(False)],"fairly good"),
 row(8,"Lord","Sun (6th)",False,[P("dusthana"),ASP(True,R),ASP(True,R)],"moderately good"),
 row(8,"Karaka","Venus (7th)",False,[P("kendra_trikona"),CNJ(False,R),CNJ(True,R)],"moderately good"),
 row(9,"Bhava","7th (Aries)",True,[OCC(True),OCC(False),BASP(False),BASP(False)],"weak"),
 row(9,"Lord","Mars (12th)",False,[P("dusthana"),CNJ(False,R),CNJ(True,R)],"weak"),
 row(9,"Karaka","Venus (12th)",False,[P("dusthana"),CNJ(False,R),CNJ(False,R)],"afflicted"),
 row(10,"Bhava","7th (Scorpio)",True,[],"moderate"),
 row(10,"Lord","Mars (3rd, debil)",False,[DIG("debilitated",R),CNJ(True,R)],"weak"),
 row(10,"Karaka","Venus (12th)",False,[P("dusthana"),CNJ(False,R),ASP(False,R),ASP(False,R)],"afflicted"),
 row(11,"Bhava","7th (Pisces)",True,[],"moderate"),
 row(11,"Lord","Jupiter (9th)",False,[P("kendra_trikona"),ASP(False,R)],"fairly strong"),
 row(11,"Karaka","Venus (4th)",False,[P("kendra_trikona"),CNJ(True,R),CNJ(False,R)],"fairly strong"),
 row(12,"Bhava","7th (Sagittarius)",True,[BASP(True),BASP(True),BASP(False)],"fairly strong"),
 row(12,"Karaka","Venus",False,[DIG("friendly",R),CNJ(False,R),ASP(True,R)],"moderately good"),
 row(13,"Bhava","7th (Cancer)",True,[],"moderate"),
 row(13,"Karaka","Venus (9th, debil)",False,[P("kendra_trikona"),NB(),KTR("papa")],"moderately good"),
 row(14,"Bhava","7th (Gemini)",True,[BASP(False)],"moderate"),
 row(14,"Lord","Mercury (11th)",False,[CNJ(True,R),CNJ(False,R)],"moderate"),
 row(14,"Karaka","Venus (Lagna)",False,[P("kendra_trikona"),ASP(False,R)],"moderately good"),
 row(15,"Bhava","7th (Pisces)",True,[OCC(False)],"weak"),
 row(15,"Lord","Jupiter (9th)",False,[P("kendra_trikona"),CNJ(False,R),ASP(True,R),ASP(False,R)],"fairly good"),
 row(15,"Karaka","Venus (5th)",False,[P("kendra_trikona"),ASP(True,R),ASP(True,R)],"fairly strong"),
 row(16,"Bhava","7th (Leo)",True,[BASP(True),BASP(True)],"fairly good"),
 row(16,"Lord","Sun (kendra, varg)",False,[P("kendra_trikona"),VG()],"fairly strong"),
 row(16,"Karaka","Venus (2nd, exalt+varg)",False,[DIG("exalted",R),VG(),DIG("exalted",N),CNJ(False,R),CNJ(True,R)],"very strong"),
]
out={"house":7,"chapter":"ch11 (Vol. II)","holdout_rule":"chart_no % 3 == 0","rows":rows}
Path("scratchpad/htjah_h7_calibration.json").write_text(json.dumps(out,indent=1))
print(f"h7: {len(rows)} rows")
