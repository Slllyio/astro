"""Spike C — confirm computing all 16 D-charts is cheap vs only the 10 used (per spec Section 16)."""
from __future__ import annotations
import time

from app.core.shodashavarga import (
    SHODASHAVARGA_DIVISORS,
    calculate_divisional_longitude,
)

USED = (1, 2, 3, 4, 7, 9, 10, 12, 24, 60)  # spec divisional_readings + D24 ★NEW
ALL16 = tuple(SHODASHAVARGA_DIVISORS)

# 9 representative planet sidereal longitudes (Bangalore baseline approximations)
positions = [
    113.0,  # Sun in Cancer
    344.0,  # Moon in Pisces (Revati)
    25.0,   # Mars
    99.0,   # Mercury
    87.0,   # Jupiter
    149.0,  # Venus
    296.0,  # Saturn
    270.0,  # Rahu
    90.0,   # Ketu
]

def measure(divisors: tuple[int, ...], n_charts: int = 1000) -> float:
    start = time.perf_counter()
    for _ in range(n_charts):
        for lon in positions:
            for d in divisors:
                _ = calculate_divisional_longitude(lon, d)
    return time.perf_counter() - start

print("Spike C: Shodashavarga 16-varga marginal cost")
print("=" * 70)
print(f"SHODASHAVARGA_DIVISORS: {ALL16}")
print(f"USED (per spec): {USED}")
print()

t_used = measure(USED)
t_all = measure(ALL16)

print(f"USED  ({len(USED):2d} divisors): {t_used*1000:7.1f}ms per 1000 charts")
print(f"ALL16 ({len(ALL16):2d} divisors): {t_all*1000:7.1f}ms per 1000 charts")
print(f"Delta: {(t_all-t_used)*1000:.1f}ms ({((t_all/t_used)-1)*100:.0f}% increase)")
print(f"Per-chart marginal: {(t_all-t_used):.3f}ms")
