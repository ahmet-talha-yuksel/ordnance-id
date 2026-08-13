# Evaluation Set v1 Statistics

| Family | Tier(s) | Samples | Small | Medium | Large |
|---|---|---:|---:|---:|---:|
| aviation_bomb | limited | 21 | 0 | 13 | 8 |
| cartridge | reportable | 10 | 7 | 3 | 0 |
| fuze | limited | 14 | 1 | 7 | 6 |
| grenade | reportable | 19 | 0 | 14 | 5 |
| landmine | insufficient | 2 | 0 | 1 | 1 |
| mortar | reportable | 19 | 0 | 7 | 12 |
| not_ordnance | distractor | 35 | 4 | 25 | 6 |
| projectile | reportable | 19 | 0 | 9 | 10 |
| rocket | limited | 13 | 0 | 12 | 1 |

## Composition and dimensions

- Positive crops: 117 (77.0%)
- Negative crops: 35 (23.0%)
- Short edge, min/median/max: 109 / 442.0 / 2044 px
- Distinct source images: 117

## Size buckets

| Bucket | Definition | Samples |
|---|---|---:|
| small | short edge <150 px | 12 |
| medium | short edge 150–600 px | 91 |
| large | short edge >600 px | 49 |

## Source concentration warnings

- `UXOs_3364.jpg` supplies 4 crops (>3).
- `UXOs_3375.jpg` supplies 4 crops (>3).
- `UXOs_3384.jpg` supplies 4 crops (>3).

## Confounding factors

- Seven of the 12 small crops belong to the `cartridge` family, so family effects cannot be separated from size effects in that slice.
- The `landmine` family has only two samples; no performance claim can be made for that family.
