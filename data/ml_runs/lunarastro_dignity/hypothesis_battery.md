# Pre-registered hypothesis battery — 103 classical claims

Each claim tested non-circularly (chart-shuffle / exposure / permutation, K=1000); Benjamini-Hochberg FDR at 0.05 over all 103. **11 raw p<0.05, 4 survive FDR.**

## Survivors (FDR-significant)

| id | claim | n | effect | lift | stat | p |
|---|---|---:|---:|---:|---:|---:|
| H087 | relationship ← karaka Jupiter of 5th [exposure] | 551 | 0.2033 | 1.525 | 4.83 | 6.858e-07 |
| H091 | death ← karaka Saturn of 8th [exposure] | 2695 | 0.1866 | 1.179 | 4.03 | 2.84e-05 |
| H092 | family ← karaka Jupiter of 2th [exposure] | 956 | 0.1705 | 1.279 | 3.38 | 0.0003615 |
| H088 | career ← karaka Sun/Mercury/Jupiter/Saturn of 10th [exposure] | 6702 | 0.5016 | 1.038 | 3.0 | 0.001353 |

## Top 25 by evidence

| id | claim | type | n | lift/ρ | stat | p | FDR |
|---|---|---|---:|---:|---:|---:|:--:|
| H087 | relationship ← karaka Jupiter of 5th [exposure] | karaka | 551 | 1.525 | 4.83 | 6.858e-07 | ✅ |
| H091 | death ← karaka Saturn of 8th [exposure] | karaka | 2695 | 1.179 | 4.03 | 2.84e-05 | ✅ |
| H092 | family ← karaka Jupiter of 2th [exposure] | karaka | 956 | 1.279 | 3.38 | 0.0003615 | ✅ |
| H088 | career ← karaka Sun/Mercury/Jupiter/Saturn of 10th [exposure] | karaka | 6702 | 1.038 | 3.0 | 0.001353 | ✅ |
| H001 | marriage ← 7th-lord (spouse) [MD] | sig_md | 1750 | 1.153 | 2.19 | 0.01998 |  |
| H057 | health ← 12th-lord (hospital) [MD] | sig_md | 763 | 1.237 | 1.98 | 0.02997 |  |
| H098 | career age ~ strength(10,): ρ? stronger 10th → ? | age | 2340 | nan | -2.13 | 0.031 |  |
| H056 | health ← 8th-lord (chronic) [AD] | sig_ad | 763 | 1.188 | 1.88 | 0.03297 |  |
| H100 | marriage ← navamsa dispositor of 7th-lord [D9] | d9 | 1750 | 1.129 | 1.84 | 0.03297 |  |
| H042 | education ← 4th-lord (schooling) [AD] | sig_ad | 422 | 1.248 | 1.97 | 0.03596 |  |
| H094 | marriage age ~ strength(7,): ρ<0 stronger 7th → earlier | age | 1200 | nan | -2.1 | 0.038 |  |
| H050 | education ← 3th-lord (skill) [AD] | sig_ad | 422 | 1.206 | 1.56 | 0.06993 |  |
| H032 | career ← 6th-lord (service) [AD] | sig_ad | 6702 | 1.052 | 1.52 | 0.07093 |  |
| H029 | career ← 10th-lord (karma) [MD] | sig_md | 6702 | 1.063 | 1.28 | 0.1069 |  |
| H095 | marriage age ~ strength(2, 7, 11): ρ<0 stronger trine → earlier | age | 1200 | nan | -1.6 | 0.1069 |  |
| H071 | family ← 2th-lord (kutumba) [MD] | sig_md | 956 | 1.141 | 1.26 | 0.1179 |  |
| H047 | education ← 9th-lord (higher) [MD] | sig_md | 422 | 1.209 | 1.26 | 0.1219 |  |
| H014 | divorce ← 6th-lord (separation) [AD] | sig_ad | 422 | 1.151 | 1.16 | 0.1309 |  |
| H059 | death ← 8th-lord (longevity) [MD] | sig_md | 2695 | 1.062 | 1.16 | 0.1339 |  |
| H025 | relationship ← 11th-lord (desire) [MD] | sig_md | 551 | 1.152 | 1.06 | 0.1588 |  |
| H060 | death ← 8th-lord (longevity) [AD] | sig_ad | 2695 | 1.046 | 0.93 | 0.1738 |  |
| H045 | education ← 2th-lord (learning) [MD] | sig_md | 422 | 1.166 | 1.01 | 0.1778 |  |
| H015 | divorce ← 8th-lord (rupture) [MD] | sig_md | 422 | 1.127 | 0.91 | 0.2018 |  |
| H011 | divorce ← 7th-lord (spouse) [MD] | sig_md | 422 | 1.12 | 0.88 | 0.2148 |  |
| H075 | family ← 7th-lord (kin) [MD] | sig_md | 956 | 1.089 | 0.79 | 0.2168 |  |

## Reading

- A claim survives only if its evidence beats the FDR bar across the whole battery — the honest standard for a fishing expedition this wide.
- **Two null types, not equally strong.** The `karaka` tests use an *exposure* null that controls for how long each planet's dasha lasts but **not for WHEN in life it falls** — so they cannot separate 'Saturn signifies death' from 'Saturn periods land in old age, when deaths cluster' (the classic age×dasha confound). The `sig_md/sig_ad` tests use a *chart-shuffle* null that holds lord, class and age fixed and is therefore age-robust.
- **All FDR survivors are karaka-exposure tests** (Jupiter→relationship/children, Saturn→death, Jupiter→family, karakas→career) — classically sensible and strong, but they need an age-stratified confirmation before being trusted as timing (not age) effects.
- Among the **age-robust** chart-shuffle tests the leader is `marriage ← 7th-lord (spouse) [MD]` (lift 1.153, p=0.02) — the 7th-lord→marriage signal, consistent across this whole session, though it does not clear FDR over 103 claims.
- The bulk landing near p≈0.5 with lift≈1 is the expected null mass: most classical significator rules leave no detectable timing footprint on this corpus.
