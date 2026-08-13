# Decision tree draft

This is a design draft, not an implemented classifier. It uses only `observe_v2` fields and
routes unresolved cases to abstention.

## Evidence rules

- Family-stage primary fields require family MI ≥ 0.10 nats and no shortcut flag.
- A pair is considered unresolved when every accepted categorical field has TVD < 0.50.
- `landmine` (n=2) is excluded from inference and always routes to abstention.
- `None`/`unobserved` remains a category; it is not coerced to `False`.

## Stage A — is_ordnance gate

No observed field supports a reliable positive **and** negative decision after shortcut-suspect
fields are rejected. Therefore this gate can produce `candidate_positive` or `abstain`, but it
must not emit `not_ordnance` from these data.

| Node | Rule | Evidence | n |
|---|---|---|---:|
| A1 | `length_to_width_ratio is not None` | Filled: positive 89/117, negative 3/35; presence TVD=0.675 | 152 |
| A2 | Any of `fins_or_tail_visible`, `fuze_visible`, `driving_band_visible` is `True` | Positive 53/117, negative 0/35; OR TVD=0.453 | 152 |
| A3 | A1 and A2 → `candidate_positive`; otherwise → `abstain` | Positive 43/117, negative 0/35 | 152 |

A3 is a high-precision candidate route in this sample, not an accuracy claim. It leaves 74/117
positives unresolved and makes no negative classification.

## Stage B — family narrowing

Only candidates from A3 enter this stage.

| Order | Branch | Candidate set / action | Evidence | Family sample sizes |
|---:|---|---|---|---|
| 1 | `fins_or_tail_visible=True` | `{mortar, rocket, aviation_bomb}`; continue, never finalize | MI=0.2438; mortar–projectile TVD=0.632; mortar–rocket TVD=0.429 | mortar 19, rocket 13, aviation_bomb 21 |
| 2 | `fins_or_tail_visible=False` and `fuze_visible=True` | `{grenade, fuze}`; abstain between them | fuze MI=0.1820; grenade–projectile TVD=0.579; grenade–fuze accepted-field max TVD=0.274 | grenade 19, fuze 14 |
| 3 | `driving_band_visible=True` after either branch | `{mortar, rocket, projectile}`; continue, never finalize | MI=0.2505; mortar–projectile TVD=0.316 for this field; projectile–rocket accepted-field max TVD=0.356 | mortar 19, rocket 13, projectile 19 |
| 4 | Ratio median ≤1.80 with the grenade branch active | retain `grenade` as a candidate, not a final label | grenade ratio median=1.60, IQR=1.45–1.80, filled n=16 | grenade 19 |
| 5 | Ratio median region 2.20–2.50 with the fuze branch active | retain `fuze` as a candidate, not a final label | fuze median=2.50, IQR=2.20–2.50, filled n=13 | fuze 14 |
| 6 | Ratio near 3.50 in elongated branches | `{aviation_bomb, cartridge, mortar, projectile, rocket}`; abstain unless another accepted branch separates the pair | medians all 3.50; mortar–rocket empirical ratio overlap=0.608 | 10–21 per family |
| 7 | Any remaining candidate set with more than one family | `abstain` | No accepted branch reaches the stated pairwise TVD threshold | applicable candidate n |

## Family pairs unresolved by accepted observation fields

The value shown is the largest TVD among `fins_or_tail_visible`, `fuze_visible`,
`driving_band_visible`, `markings_visible`, `embedded_in_ground`, and
`image_quality_sufficient`. Fields rejected below do not rescue a pair.

| Family pair | Maximum accepted-field TVD | Best field | Action |
|---|---:|---|---|
| aviation_bomb vs cartridge | 0.224 | embedded_in_ground | abstain |
| aviation_bomb vs fuze | 0.381 | embedded_in_ground | abstain |
| aviation_bomb vs projectile | 0.419 | embedded_in_ground | abstain |
| cartridge vs fuze | 0.471 | fuze_visible | abstain |
| cartridge vs projectile | 0.374 | driving_band_visible | abstain |
| fuze vs grenade | 0.274 | fuze_visible | abstain |
| fuze vs projectile | 0.474 | driving_band_visible | abstain |
| mortar vs rocket | 0.429 | fins_or_tail_visible | abstain |
| projectile vs rocket | 0.356 | fuze_visible | abstain |

`landmine` is additionally unresolved by policy because n=2; no metric-based inference is made.

## Rejected features

| Feature | Measured evidence | Rejection reason |
|---|---|---|
| surface_condition | family MI=0.3466; positive/negative TVD=0.684; size MI=0.0562 | suspected shortcut |
| body_shape | family MI=0.4920; positive/negative TVD=0.692; size MI=0.0527 | suspected shortcut |
| looks_manufactured | family MI=0.0701; positive/negative TVD=0.740; size MI=0.0664 | suspected shortcut and low family MI |
| image_quality_sufficient | family MI=0.0279 | low discriminativeness |
| embedded_in_ground | family MI=0.0959 | below primary-field MI threshold |
| markings_visible | family MI=0.0898 | below primary-field MI threshold |
| estimated_length_cm | not applicable; no scale references | unavailable in this eval set |
| markings_text | filled 10/152 | sparse free text, not a categorical branch |
| color_bands | list-valued field | no validated categorical encoding in this analysis |

The accepted structural fields are insufficient for a complete family classifier. Phase 3
implementation should preserve abstention rather than backfilling these gaps with rejected
features.
