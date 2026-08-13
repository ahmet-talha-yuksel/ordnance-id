# Decision tree draft

This is a design draft, not an implemented classifier. It uses only `observe_v2` fields and
routes unresolved cases to abstention.

## Evidence rules

- Family-stage primary fields require family MI ≥ 0.10 nats and no shortcut flag on the
  **family axis**.
- A pair is considered unresolved when every accepted categorical field has TVD < 0.50.
- `landmine` (n=2) is excluded from inference and always routes to abstention.
- `None`/`unobserved` remains a category; it is not coerced to `False`.

## Stage A — is_ordnance gate

No tested field supports a reliable positive **and** negative decision after is_ordnance-axis
shortcuts are rejected. `surface_condition`, `looks_manufactured`, and `body_shape` are excluded
at this stage. Ratio availability is also excluded because availability describes observability,
not object identity. The only remaining physically grounded signals are positive-only structural
cues. Therefore this gate can produce `candidate_positive` or `abstain`, but it must not emit
`not_ordnance` from these data.

| Node | Rule | Evidence | n |
|---|---|---|---:|
| A1 | Any of `fins_or_tail_visible`, `fuze_visible`, `driving_band_visible` is `True` | Positive 53/117, negative 0/35; OR TVD=0.453 | 152 |
| A2 | A1 true → `candidate_positive`; A1 false/unobserved → `abstain` | No accepted field supports a negative decision | 152 |

A2 is a high-precision candidate route in this sample, not an accuracy claim. It leaves 64/117
positives unresolved and makes no negative classification. The is_ordnance gate therefore depends
on confidence and abstention, not a complete observation-field decision rule; this is a finding of
the analysis.

## Stage B — family narrowing

Only candidates from A3 enter this stage.

| Order | Branch | Candidate set / action | Evidence | Family sample sizes |
|---:|---|---|---|---|
| 1 | `body_shape` | Split into geometric candidate sets; never use at Stage A | family MI=0.4920; is_ordnance-axis TVD=0.692; family-axis physical pattern documented below | positive n=117 |
| 2 | `body_shape=ogive` | `{mortar, projectile, aviation_bomb, rocket}` | mortar 13/19; projectile 6/19; aviation_bomb 5/21; rocket 3/13 | family n=13–21 |
| 3 | `body_shape=cylindrical` | `{projectile, aviation_bomb, rocket, cartridge}` | projectile 13/19; aviation_bomb 10/21; rocket 6/13; cartridge 4/10 | family n=10–21 |
| 4 | `body_shape=irregular` | `{fuze, grenade}` | fuze 8/14; grenade 8/19; pair body-shape TVD=0.297 | fuze 14, grenade 19 |
| 5 | `fins_or_tail_visible=True` | Narrow toward `{mortar, rocket, aviation_bomb}` | MI=0.2438; mortar–projectile TVD=0.632; mortar–rocket TVD=0.429 | mortar 19, rocket 13, aviation_bomb 21 |
| 6 | `fuze_visible=True` | Narrow toward `{grenade, fuze}` but retain abstention | MI=0.1820; grenade–projectile TVD=0.579; grenade–fuze accepted-field max TVD=0.297 | grenade 19, fuze 14 |
| 7 | `driving_band_visible=True` | Narrow toward `{mortar, rocket, projectile}` | MI=0.2505; mortar–projectile field TVD=0.316; projectile–rocket accepted-field max TVD=0.356 | mortar 19, rocket 13, projectile 19 |
| 8 | Ratio median ≤1.80 with the grenade branch active | retain `grenade` as a candidate, not a final label | grenade ratio median=1.60, IQR=1.45–1.80, filled n=16 | grenade 19 |
| 9 | Ratio median region 2.20–2.50 with the fuze branch active | retain `fuze` as a candidate, not a final label | fuze median=2.50, IQR=2.20–2.50, filled n=13 | fuze 14 |
| 10 | Any remaining candidate set with more than one family | `abstain` | No accepted branch reaches the stated pairwise TVD threshold | applicable candidate n |

## Family pairs unresolved by accepted observation fields

The value shown is the largest TVD among `fins_or_tail_visible`, `fuze_visible`,
`driving_band_visible`, `markings_visible`, `embedded_in_ground`, and
`image_quality_sufficient`, and family-axis `body_shape`. Fields rejected below do not rescue a
pair. Adding `body_shape` resolves 5 of the previous 9 pairs; 4 remain unresolved.

| Family pair | Maximum accepted-field TVD | Best field | Action |
|---|---:|---|---|
| aviation_bomb vs cartridge | 0.362 | body_shape | abstain |
| aviation_bomb vs projectile | 0.419 | embedded_in_ground | abstain |
| fuze vs grenade | 0.297 | body_shape | abstain |
| projectile vs rocket | 0.356 | fuze_visible | abstain |

`landmine` is additionally unresolved by policy because n=2; no metric-based inference is made.

## Rejected features

| Feature | Measured evidence | Rejection reason |
|---|---|---|
| surface_condition | family MI=0.3466; positive/negative TVD=0.684; size MI=0.0562 | suspected shortcut on both axes |
| body_shape at Stage A | family MI=0.4920; positive/negative TVD=0.692; negatives are 26/35 unclear | suspected is_ordnance shortcut; retained at Stage B because family geometry is physically defensible |
| looks_manufactured | family MI=0.0701; positive/negative TVD=0.740; size MI=0.0664 | suspected is_ordnance shortcut and low family MI |
| image_quality_sufficient | family MI=0.0279 | low discriminativeness |
| embedded_in_ground | family MI=0.0959 | below primary-field MI threshold |
| markings_visible | family MI=0.0898 | below primary-field MI threshold |
| estimated_length_cm | not applicable; no scale references | unavailable in this eval set |
| markings_text | filled 10/152 | sparse free text, not a categorical branch |
| color_bands | list-valued field | no validated categorical encoding in this analysis |

The accepted structural and family-axis shape fields are insufficient for a complete family classifier. Phase 3
implementation should preserve abstention rather than backfilling these gaps with rejected
features.
