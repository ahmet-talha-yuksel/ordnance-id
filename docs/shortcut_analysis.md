# Shortcut suspicion analysis

Observations: 152; positive: 117; negative: 35.
`None` is counted as `unobserved`. MI is reported in nats.

## Association summary

| Field | Positive/negative TVD | MI with positive-family label | MI with size bucket |
|---|---:|---:|---:|
| surface_condition | 0.684 | 0.3466 | 0.0562 |
| looks_manufactured | 0.740 | 0.0701 | 0.0664 |
| body_shape | 0.692 | 0.4920 | 0.0527 |

## surface_condition

### Distribution by family

| Family | n | Distribution |
|---|---:|---|
| aviation_bomb | 21 | `{'heavily_corroded': 19, 'unclear': 1, 'corroded': 1}` |
| cartridge | 10 | `{'heavily_corroded': 5, 'weathered': 4, 'unclear': 1}` |
| fuze | 14 | `{'unclear': 2, 'weathered': 8, 'clean': 3, 'corroded': 1}` |
| grenade | 19 | `{'heavily_corroded': 6, 'corroded': 2, 'weathered': 9, 'unclear': 2}` |
| landmine | 2 | `{'heavily_corroded': 2}` |
| mortar | 19 | `{'heavily_corroded': 8, 'weathered': 6, 'clean': 3, 'corroded': 2}` |
| not_ordnance | 35 | `{'unclear': 19, 'weathered': 16}` |
| projectile | 19 | `{'heavily_corroded': 18, 'weathered': 1}` |
| rocket | 13 | `{'heavily_corroded': 8, 'corroded': 2, 'weathered': 3}` |

### Distribution by size bucket

| Size bucket | n | Distribution |
|---|---:|---|
| small | 12 | `{'heavily_corroded': 2, 'weathered': 7, 'unclear': 3}` |
| medium | 91 | `{'heavily_corroded': 39, 'unclear': 19, 'corroded': 4, 'weathered': 27, 'clean': 2}` |
| large | 49 | `{'heavily_corroded': 25, 'clean': 4, 'weathered': 13, 'corroded': 4, 'unclear': 3}` |

### Negative distribution

- n: 35
- Counts: `{'unclear': 19, 'weathered': 16}`

## looks_manufactured

### Distribution by family

| Family | n | Distribution |
|---|---:|---|
| aviation_bomb | 21 | `{True: 20, 'unobserved': 1}` |
| cartridge | 10 | `{True: 7, False: 2, 'unobserved': 1}` |
| fuze | 14 | `{False: 1, True: 12, 'unobserved': 1}` |
| grenade | 19 | `{True: 18, 'unobserved': 1}` |
| landmine | 2 | `{True: 2}` |
| mortar | 19 | `{True: 19}` |
| not_ordnance | 35 | `{False: 22, 'unobserved': 6, True: 7}` |
| projectile | 19 | `{True: 19}` |
| rocket | 13 | `{True: 13}` |

### Distribution by size bucket

| Size bucket | n | Distribution |
|---|---:|---|
| small | 12 | `{True: 4, False: 7, 'unobserved': 1}` |
| medium | 91 | `{True: 68, 'unobserved': 7, False: 16}` |
| large | 49 | `{True: 45, False: 2, 'unobserved': 2}` |

### Negative distribution

- n: 35
- Counts: `{False: 22, 'unobserved': 6, True: 7}`

## body_shape

### Distribution by family

| Family | n | Distribution |
|---|---:|---|
| aviation_bomb | 21 | `{'cylindrical': 10, 'ogive': 5, 'unclear': 5, 'conical': 1}` |
| cartridge | 10 | `{'unclear': 4, 'cylindrical': 4, 'irregular': 1, 'boxy': 1}` |
| fuze | 14 | `{'irregular': 8, 'unclear': 1, 'cylindrical': 3, 'conical': 2}` |
| grenade | 19 | `{'cylindrical': 4, 'irregular': 8, 'ogive': 2, 'spherical': 2, 'unclear': 3}` |
| landmine | 2 | `{'unclear': 2}` |
| mortar | 19 | `{'ogive': 13, 'conical': 1, 'irregular': 2, 'spherical': 1, 'cylindrical': 2}` |
| not_ordnance | 35 | `{'unclear': 26, 'irregular': 8, 'boxy': 1}` |
| projectile | 19 | `{'cylindrical': 13, 'ogive': 6}` |
| rocket | 13 | `{'unclear': 1, 'conical': 3, 'ogive': 3, 'cylindrical': 6}` |

### Distribution by size bucket

| Size bucket | n | Distribution |
|---|---:|---|
| small | 12 | `{'unclear': 6, 'cylindrical': 3, 'irregular': 3}` |
| medium | 91 | `{'cylindrical': 23, 'ogive': 17, 'unclear': 29, 'boxy': 1, 'irregular': 16, 'spherical': 2, 'conical': 3}` |
| large | 49 | `{'ogive': 12, 'cylindrical': 16, 'unclear': 7, 'conical': 4, 'irregular': 8, 'spherical': 1, 'boxy': 1}` |

### Negative distribution

- n: 35
- Counts: `{'unclear': 26, 'irregular': 8, 'boxy': 1}`

## Suspected shortcuts

Flag rule: positive/negative TVD ≥ 0.50 and either family MI ≥ 0.10 or size-bucket MI ≥ 0.05.

- `surface_condition` — TVD=0.684, family MI=0.3466, size MI=0.0562
- `looks_manufactured` — TVD=0.740, family MI=0.0701, size MI=0.0664
- `body_shape` — TVD=0.692, family MI=0.4920, size MI=0.0527

