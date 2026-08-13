# Gemini observation pilot inspection

## 1. Rule violation scan

Violations: **0**

- No prohibited identification, caliber, danger, or safety-advice text found.

## 2. Nullable-field rates by size bucket

| Bucket | Field | None | Total | None rate |
|---|---|---:|---:|---:|
| small | fins_or_tail_visible | 1 | 1 | 100.0% |
| small | fuze_visible | 1 | 1 | 100.0% |
| small | driving_band_visible | 1 | 1 | 100.0% |
| small | markings_or_stencil_text | 1 | 1 | 100.0% |
| small | embedded_in_ground | 0 | 1 | 0.0% |
| small | estimated_length_cm | 1 | 1 | 100.0% |
| small | length_to_width_ratio | 1 | 1 | 100.0% |
| small | looks_manufactured | 0 | 1 | 0.0% |
| medium | fins_or_tail_visible | 2 | 7 | 28.6% |
| medium | fuze_visible | 3 | 7 | 42.9% |
| medium | driving_band_visible | 3 | 7 | 42.9% |
| medium | markings_or_stencil_text | 7 | 7 | 100.0% |
| medium | embedded_in_ground | 1 | 7 | 14.3% |
| medium | estimated_length_cm | 7 | 7 | 100.0% |
| medium | length_to_width_ratio | 7 | 7 | 100.0% |
| medium | looks_manufactured | 1 | 7 | 14.3% |
| large | fins_or_tail_visible | 0 | 2 | 0.0% |
| large | fuze_visible | 1 | 2 | 50.0% |
| large | driving_band_visible | 0 | 2 | 0.0% |
| large | markings_or_stencil_text | 2 | 2 | 100.0% |
| large | embedded_in_ground | 0 | 2 | 0.0% |
| large | estimated_length_cm | 2 | 2 | 100.0% |
| large | length_to_width_ratio | 2 | 2 | 100.0% |
| large | looks_manufactured | 0 | 2 | 0.0% |

## 3. Unclear features

- `markings_or_stencil_text`: 10
- `length_to_width_ratio`: 10
- `estimated_length_cm`: 10
- `fuze_visible`: 5
- `driving_band_visible`: 4
- `fins_or_tail_visible`: 3
- `body_shape`: 2
- `surface_condition`: 2
- `embedded_in_ground`: 1
- `looks_manufactured`: 1

## 4. Positive versus negative distributions

### looks_manufactured

- Positive: `{True: 7}`
- Negative: `{False: 2, None: 1}`

### body_shape

- Positive: `{'ogive': 3, 'cylindrical': 2, 'boxy': 1, 'conical': 1}`
- Negative: `{'unclear': 2, 'irregular': 1}`

### surface_condition

- Positive: `{'weathered': 4, 'heavily_corroded': 3}`
- Negative: `{'unclear': 2, 'weathered': 1}`

## 5. Raw observations

### eval_074 · mortar · medium

```json
{
  "body_shape": "ogive",
  "fins_or_tail_visible": true,
  "fuze_visible": true,
  "driving_band_visible": true,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "weathered",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "markings_or_stencil_text",
    "length_to_width_ratio",
    "estimated_length_cm"
  ],
  "observation_notes": "An elongated object with an ogive-shaped main body, a cylindrical section with multiple fins at one end, and a cap-like structure at the opposite end. Several raised, circumferential bands are present on the main body. The surface shows signs of weathering and discoloration, with some areas appearing dark and others metallic silver."
}
```

### eval_029 · cartridge · small

```json
{
  "body_shape": "cylindrical",
  "fins_or_tail_visible": null,
  "fuze_visible": null,
  "driving_band_visible": null,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "weathered",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "length_to_width_ratio",
    "fins_or_tail_visible",
    "fuze_visible",
    "driving_band_visible",
    "markings_or_stencil_text",
    "estimated_length_cm"
  ],
  "observation_notes": "Multiple elongated, cylindrical objects are piled together. Their surfaces appear weathered. No distinct markings, fins, fuzes, or driving bands are visible. The image is somewhat blurry, making precise details and ratios difficult to discern."
}
```

### eval_058 · grenade · large

```json
{
  "body_shape": "boxy",
  "fins_or_tail_visible": false,
  "fuze_visible": true,
  "driving_band_visible": false,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "weathered",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "markings_or_stencil_text",
    "estimated_length_cm",
    "length_to_width_ratio"
  ],
  "observation_notes": "A metal object with a segmented, ovoid body, a lever-and-ring mechanism at the top, and a weathered surface with patches of green paint and rust."
}
```

### eval_094 · projectile · medium

```json
{
  "body_shape": "ogive",
  "fins_or_tail_visible": false,
  "fuze_visible": false,
  "driving_band_visible": true,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "heavily_corroded",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "markings_or_stencil_text",
    "estimated_length_cm",
    "length_to_width_ratio"
  ],
  "observation_notes": "The object is elongated with an ogive-like taper on the left. It has a heavily corroded, rusty surface. A distinct band with horizontal grooves is visible near the right end. No fins, fuze, or readable markings are visible."
}
```

### eval_041 · fuze · large

```json
{
  "body_shape": "conical",
  "fins_or_tail_visible": false,
  "fuze_visible": null,
  "driving_band_visible": false,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "weathered",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "fuze_visible",
    "markings_or_stencil_text",
    "estimated_length_cm",
    "length_to_width_ratio"
  ],
  "observation_notes": "The object is a tapered metal body with a flat narrower end and a threaded wider end. The surface shows some discoloration and minor imperfections. Faint, unreadable marks are present near the narrower end."
}
```

### eval_112 · rocket · medium

```json
{
  "body_shape": "ogive",
  "fins_or_tail_visible": false,
  "fuze_visible": false,
  "driving_band_visible": false,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "heavily_corroded",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "length_to_width_ratio",
    "markings_or_stencil_text",
    "estimated_length_cm"
  ],
  "observation_notes": "Elongated object with a tapered front end and an open, cylindrical rear end. The surface is heavily corroded with white deposits and reddish-brown patches. No fins, fuze, or markings are visible."
}
```

### eval_115 · rocket · medium

```json
{
  "body_shape": "cylindrical",
  "fins_or_tail_visible": true,
  "fuze_visible": null,
  "driving_band_visible": null,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "heavily_corroded",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "fuze_visible",
    "driving_band_visible",
    "markings_or_stencil_text",
    "estimated_length_cm",
    "length_to_width_ratio"
  ],
  "observation_notes": "Multiple elongated, cylindrical, heavily corroded metal objects are visible, partially submerged in water or mud. Each object has distinct fin-like structures at one end. No clear markings or fuzes are visible due to heavy corrosion."
}
```

### eval_120 · not_ordnance · medium

```json
{
  "body_shape": "unclear",
  "fins_or_tail_visible": null,
  "fuze_visible": null,
  "driving_band_visible": null,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "unclear",
  "embedded_in_ground": null,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": false,
  "image_quality_sufficient": true,
  "unclear_features": [
    "body_shape",
    "fins_or_tail_visible",
    "fuze_visible",
    "driving_band_visible",
    "markings_or_stencil_text",
    "surface_condition",
    "embedded_in_ground",
    "estimated_length_cm",
    "length_to_width_ratio"
  ],
  "observation_notes": "The image shows disturbed soil with some dry plant debris. No distinct object is visible."
}
```

### eval_125 · not_ordnance · medium

```json
{
  "body_shape": "irregular",
  "fins_or_tail_visible": false,
  "fuze_visible": false,
  "driving_band_visible": false,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "weathered",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": false,
  "image_quality_sufficient": true,
  "unclear_features": [
    "markings_or_stencil_text",
    "estimated_length_cm",
    "length_to_width_ratio"
  ],
  "observation_notes": "The image shows a ground covered with fallen leaves in various shades of yellow, orange, and brown. Some darker, possibly rocky or stony, ground is visible beneath the leaves, with patches of green moss."
}
```

### eval_126 · not_ordnance · medium

```json
{
  "body_shape": "unclear",
  "fins_or_tail_visible": null,
  "fuze_visible": null,
  "driving_band_visible": null,
  "markings_or_stencil_text": null,
  "color_bands": [],
  "surface_condition": "unclear",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": null,
  "image_quality_sufficient": false,
  "unclear_features": [
    "body_shape",
    "fins_or_tail_visible",
    "fuze_visible",
    "driving_band_visible",
    "markings_or_stencil_text",
    "surface_condition",
    "estimated_length_cm",
    "length_to_width_ratio",
    "looks_manufactured"
  ],
  "observation_notes": "A very small, blurry, metallic-looking object is partially visible in the bottom left corner, surrounded by grass and dry leaves. Its shape and surface details are indistinct due to blurriness and partial obstruction."
}
```

## 6. Operational metrics

- Records: 10
- Errors: 0
- Schema-validation errors: 0
- Retries: 0
- HTTP 429 responses: 0
- Cache hits: 0
- Average duration: 7428.7 ms
- Input tokens: 6880
- Output tokens: 2331
- Total cost: $0.0000

