# Family-level discriminativeness

Positive observations only: **n=117**.
`None` is represented as the categorical value `unobserved`.
Mutual information is empirical MI in natural-log units (nats).

## Sample sizes

| Family | n | Status |
|---|---:|---|
| aviation_bomb | 21 | descriptive |
| cartridge | 10 | descriptive |
| fuze | 14 | descriptive |
| grenade | 19 | descriptive |
| landmine | 2 | no inference |
| mortar | 19 | descriptive |
| projectile | 19 | descriptive |
| rocket | 13 | descriptive |

## 1. Mutual information with family label

| Rank | Field | MI (nats) |
|---:|---|---:|
| 1 | body_shape | 0.4920 |
| 2 | surface_condition | 0.3466 |
| 3 | driving_band_visible | 0.2505 |
| 4 | fins_or_tail_visible | 0.2438 |
| 5 | fuze_visible | 0.1820 |
| 6 | embedded_in_ground | 0.0959 |
| 7 | markings_visible | 0.0898 |
| 8 | looks_manufactured | 0.0701 |
| 9 | image_quality_sufficient | 0.0279 |

## 2. Pairwise family TVD

Reportable and limited families only. Values range from 0 (same empirical distribution) to 1 (disjoint empirical distributions).

### Requested family pairs

| Pair | Field | TVD |
|---|---|---:|
| cartridge vs fuze | image_quality_sufficient | 0.029 |
| cartridge vs fuze | body_shape | 0.614 |
| cartridge vs fuze | fins_or_tail_visible | 0.100 |
| cartridge vs fuze | fuze_visible | 0.471 |
| cartridge vs fuze | driving_band_visible | 0.100 |
| cartridge vs fuze | markings_visible | 0.214 |
| cartridge vs fuze | surface_condition | 0.500 |
| cartridge vs fuze | embedded_in_ground | 0.257 |
| cartridge vs fuze | looks_manufactured | 0.157 |
| grenade vs projectile | image_quality_sufficient | 0.000 |
| grenade vs projectile | body_shape | 0.684 |
| grenade vs projectile | fins_or_tail_visible | 0.105 |
| grenade vs projectile | fuze_visible | 0.579 |
| grenade vs projectile | driving_band_visible | 0.421 |
| grenade vs projectile | markings_visible | 0.158 |
| grenade vs projectile | surface_condition | 0.632 |
| grenade vs projectile | embedded_in_ground | 0.053 |
| grenade vs projectile | looks_manufactured | 0.053 |
| mortar vs projectile | image_quality_sufficient | 0.000 |
| mortar vs projectile | body_shape | 0.579 |
| mortar vs projectile | fins_or_tail_visible | 0.632 |
| mortar vs projectile | fuze_visible | 0.474 |
| mortar vs projectile | driving_band_visible | 0.316 |
| mortar vs projectile | markings_visible | 0.316 |
| mortar vs projectile | surface_condition | 0.526 |
| mortar vs projectile | embedded_in_ground | 0.158 |
| mortar vs projectile | looks_manufactured | 0.000 |

### Heatmaps

- [image_quality_sufficient](../reports/figures/family_tvd_image_quality_sufficient.png)
- [body_shape](../reports/figures/family_tvd_body_shape.png)
- [fins_or_tail_visible](../reports/figures/family_tvd_fins_or_tail_visible.png)
- [fuze_visible](../reports/figures/family_tvd_fuze_visible.png)
- [driving_band_visible](../reports/figures/family_tvd_driving_band_visible.png)
- [markings_visible](../reports/figures/family_tvd_markings_visible.png)
- [surface_condition](../reports/figures/family_tvd_surface_condition.png)
- [embedded_in_ground](../reports/figures/family_tvd_embedded_in_ground.png)
- [looks_manufactured](../reports/figures/family_tvd_looks_manufactured.png)

## 3. Length-to-width ratio

| Family | n filled | Q1 | Median | Q3 | Status |
|---|---:|---:|---:|---:|---|
| aviation_bomb | 15 | 2.80 | 3.50 | 3.50 | descriptive |
| cartridge | 3 | 3.50 | 3.50 | 4.00 | indicative only (filled n<10) |
| fuze | 13 | 2.20 | 2.50 | 2.50 | descriptive |
| grenade | 16 | 1.45 | 1.60 | 1.80 | descriptive |
| landmine | 1 | 1.10 | 1.10 | 1.10 | no inference |
| mortar | 16 | 3.50 | 3.50 | 4.50 | descriptive |
| projectile | 14 | 3.50 | 3.50 | 3.50 | descriptive |
| rocket | 11 | 3.00 | 3.50 | 4.50 | descriptive |

IQR overlap is intersection-over-union of the two family IQR intervals. Empirical overlap is 1−TVD over the exact observed ratio values.

| Family pair | IQR overlap | Empirical overlap |
|---|---:|---:|
| cartridge vs mortar | 0.500 | 0.750 |
| aviation_bomb vs projectile | 0.000 | 0.671 |
| cartridge vs projectile | 0.000 | 0.667 |
| aviation_bomb vs cartridge | 0.000 | 0.667 |
| aviation_bomb vs rocket | 0.294 | 0.612 |
| mortar vs rocket | 0.667 | 0.608 |
| aviation_bomb vs mortar | 0.000 | 0.567 |
| cartridge vs rocket | 0.333 | 0.545 |
| mortar vs projectile | 0.000 | 0.500 |
| projectile vs rocket | 0.000 | 0.416 |
| aviation_bomb vs fuze | 0.000 | 0.354 |
| fuze vs rocket | 0.000 | 0.336 |
| fuze vs projectile | 0.000 | 0.148 |
| fuze vs mortar | 0.000 | 0.139 |
| fuze vs grenade | 0.000 | 0.139 |
| cartridge vs fuze | 0.000 | 0.077 |
| grenade vs rocket | 0.000 | 0.000 |
| grenade vs projectile | 0.000 | 0.000 |
| cartridge vs grenade | 0.000 | 0.000 |
| aviation_bomb vs grenade | 0.000 | 0.000 |
| grenade vs mortar | 0.000 | 0.000 |

## 4. Sample-size warning

- Families with n<10 are marked `indicative only`.
- `landmine` (n=2) is marked `no inference`; no family-separation claim is made.

