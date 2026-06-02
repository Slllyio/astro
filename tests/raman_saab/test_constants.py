from app.raman_saab.chart import constants as c

def test_sign_lords_complete():
    """All 12 signs have a lord; Aries->Mars, Leo->Sun, Pisces->Jupiter (BPHS rulerships)."""
    assert len(c.SIGN_LORDS) == 12
    assert c.SIGN_LORDS[1] == "Mars" and c.SIGN_LORDS[5] == "Sun" and c.SIGN_LORDS[12] == "Jupiter"

def test_grahas_are_nine():
    assert c.GRAHAS == ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu")
