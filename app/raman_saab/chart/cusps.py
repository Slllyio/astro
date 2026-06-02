from __future__ import annotations

def _circ_mid(a: float, b: float) -> float:
    """Circular midpoint of two longitudes, going the short way."""
    diff = (b - a) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return (a + diff / 2.0) % 360.0

def sandhis_from_madhyas(madhyas: tuple[float, ...]) -> tuple[float, ...]:
    """sandhi[i] = junction *starting* bhava (i+1) = midpoint(madhya[i-1], madhya[i])."""
    n = len(madhyas)
    return tuple(_circ_mid(madhyas[i - 1], madhyas[i]) for i in range(n))

def _in_arc(x: float, start: float, end: float) -> bool:
    span = (end - start) % 360.0
    off = (x - start) % 360.0
    return off < span

def bhava_of(lon: float, sandhis: tuple[float, ...]) -> int:
    """Bhava (1..12) whose [sandhi_i, sandhi_{i+1}) arc contains lon."""
    n = len(sandhis)
    for i in range(n):
        if _in_arc(lon, sandhis[i], sandhis[(i + 1) % n]):
            return i + 1
    return 1  # unreachable for valid input

def is_on_sandhi(lon: float, sandhis: tuple[float, ...], *, orb: float = 1.0) -> bool:
    for s in sandhis:
        d = abs((lon - s + 180.0) % 360.0 - 180.0)
        if d < orb:
            return True
    return False
