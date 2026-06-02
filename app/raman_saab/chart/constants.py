from __future__ import annotations
from typing import Final
import swisseph as swe

GRAHAS: Final[tuple[str, ...]] = (
    "Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu")

# Swiss Ephemeris ids for the 7 visible grahas (Rahu/Ketu handled via the node).
SWE_PLANETS: Final[dict[str, int]] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

SIGN_LORDS: Final[dict[int, str]] = {
    1:"Mars",2:"Venus",3:"Mercury",4:"Moon",5:"Sun",6:"Mercury",
    7:"Venus",8:"Mars",9:"Jupiter",10:"Saturn",11:"Saturn",12:"Jupiter"}

# Navamsa element start-signs (Fire->Aries, Earth->Cap, Air->Libra, Water->Cancer).
NAVAMSA_START: Final[tuple[int, ...]] = (1, 10, 7, 4)  # indexed by (sign-1) % 4
