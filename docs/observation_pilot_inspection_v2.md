# Gemini observation pilot inspection

## 1. Rule violation scan

Violations: **0**

- No prohibited identification, caliber, danger, or safety-advice text found.

## 2. Nullable-field rates by size bucket

`estimated_length_cm` is not applicable in this eval set (no scale references present) and is excluded from completion rates.

| Bucket | Field | None | Total | None rate |
|---|---|---:|---:|---:|
| small | fins_or_tail_visible | 0 | 1 | 0.0% |
| small | fuze_visible | 0 | 1 | 0.0% |
| small | driving_band_visible | 0 | 1 | 0.0% |
| small | markings_visible | 0 | 1 | 0.0% |
| small | markings_text | 1 | 1 | 100.0% |
| small | embedded_in_ground | 0 | 1 | 0.0% |
| small | length_to_width_ratio | 0 | 1 | 0.0% |
| small | looks_manufactured | 0 | 1 | 0.0% |
| medium | fins_or_tail_visible | 1 | 7 | 14.3% |
| medium | fuze_visible | 1 | 7 | 14.3% |
| medium | driving_band_visible | 1 | 7 | 14.3% |
| medium | markings_visible | 1 | 7 | 14.3% |
| medium | markings_text | 6 | 7 | 85.7% |
| medium | embedded_in_ground | 0 | 7 | 0.0% |
| medium | length_to_width_ratio | 5 | 7 | 71.4% |
| medium | looks_manufactured | 0 | 7 | 0.0% |
| large | fins_or_tail_visible | 0 | 2 | 0.0% |
| large | fuze_visible | 1 | 2 | 50.0% |
| large | driving_band_visible | 0 | 2 | 0.0% |
| large | markings_visible | 0 | 2 | 0.0% |
| large | markings_text | 2 | 2 | 100.0% |
| large | embedded_in_ground | 0 | 2 | 0.0% |
| large | length_to_width_ratio | 0 | 2 | 0.0% |
| large | looks_manufactured | 0 | 2 | 0.0% |

## 3. Unclear features

- `estimated_length_cm: no manual scale reference`: 8
- `markings_text: no visible markings to transcribe`: 7
- `markings_text: other markings are not legible`: 1
- `length_to_width_ratio: object partially outside frame`: 1
- `fuze_visible: cannot definitively identify threaded section as a fuze without inference`: 1
- `markings_text: visible markings are not legible`: 1
- `length_to_width_ratio: objects partially outside frame`: 1
- `body_shape: no distinct object visible`: 1
- `surface_condition: no distinct object visible to assess surface condition`: 1
- `estimated_length_cm: no distinct object visible and no manual scale reference`: 1
- `length_to_width_ratio: no distinct object visible`: 1
- `body_shape: no discernible object of interest`: 1
- `surface_condition: no single object to assess surface condition`: 1
- `estimated_length_cm: no manual scale reference and no discernible object`: 1
- `length_to_width_ratio: no discernible object to measure`: 1
- `body_shape: object is blurry and partially obscured`: 1
- `fins_or_tail_visible: object is partially obscured and blurry`: 1
- `fuze_visible: object is partially obscured and blurry`: 1
- `driving_band_visible: object is partially obscured and blurry`: 1
- `markings_visible: object is too blurry and small to discern markings`: 1
- `markings_text: markings are not visible/legible`: 1
- `surface_condition: object is blurry, making surface details unclear`: 1
- `length_to_width_ratio: object is partially visible and blurry`: 1

## 4. Positive versus negative distributions

### looks_manufactured

- Positive: `{True: 7}`
- Negative: `{False: 2, True: 1}`

### body_shape

- Positive: `{'ogive': 2, 'cylindrical': 3, 'irregular': 1, 'conical': 1}`
- Negative: `{'unclear': 3}`

### surface_condition

- Positive: `{'weathered': 3, 'heavily_corroded': 4}`
- Negative: `{'unclear': 3}`

## 5. Raw observations

### eval_074 · mortar · medium

```json
{
  "body_shape": "ogive",
  "fins_or_tail_visible": true,
  "fuze_visible": true,
  "driving_band_visible": true,
  "markings_visible": true,
  "markings_text": "H",
  "color_bands": [
    "silver",
    "dark",
    "silver"
  ],
  "surface_condition": "weathered",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": 5.5,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "estimated_length_cm: no manual scale reference",
    "markings_text: other markings are not legible"
  ],
  "observation_notes": "An elongated, manufactured object with an ogive nose, cylindrical body, and finned tail. The body is dark and weathered with visible driving bands. The nose and tail sections are metallic silver. A faint 'H' marking is visible on the dark body."
}
```

### eval_029 · cartridge · small

```json
{
  "body_shape": "cylindrical",
  "fins_or_tail_visible": false,
  "fuze_visible": false,
  "driving_band_visible": false,
  "markings_visible": false,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "heavily_corroded",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": 3.5,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "markings_text: no visible markings to transcribe",
    "estimated_length_cm: no manual scale reference"
  ],
  "observation_notes": "Multiple elongated, cylindrical metallic objects are visible. Their surfaces are heavily corroded. No fins, fuzes, or driving bands are visible. No markings or color bands are present. The objects appear manufactured."
}
```

### eval_058 · grenade · large

```json
{
  "body_shape": "irregular",
  "fins_or_tail_visible": false,
  "fuze_visible": true,
  "driving_band_visible": false,
  "markings_visible": false,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "weathered",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": 1.7,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "estimated_length_cm: no manual scale reference",
    "markings_text: no visible markings to transcribe"
  ],
  "observation_notes": "The object has a segmented, somewhat ovoid body with a metallic fuze mechanism at the top, including a lever, pin, and ring. The body shows mottled green and brown/rust discoloration. It is resting on a wooden surface."
}
```

### eval_094 · projectile · medium

```json
{
  "body_shape": "cylindrical",
  "fins_or_tail_visible": false,
  "fuze_visible": false,
  "driving_band_visible": true,
  "markings_visible": false,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "heavily_corroded",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "markings_text: no visible markings to transcribe",
    "estimated_length_cm: no manual scale reference",
    "length_to_width_ratio: object partially outside frame"
  ],
  "observation_notes": "An elongated, heavily corroded metal object is visible, partially cut off by the image frame on both ends. A distinct grooved band is present near the right end. The surface is covered in rust and pitting. No other distinct features, fins, tail, or fuze are visible. The object rests on sandy ground but is not embedded."
}
```

### eval_041 · fuze · large

```json
{
  "body_shape": "conical",
  "fins_or_tail_visible": false,
  "fuze_visible": null,
  "driving_band_visible": false,
  "markings_visible": true,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "weathered",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": 2.5,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "fuze_visible: cannot definitively identify threaded section as a fuze without inference",
    "markings_text: visible markings are not legible",
    "estimated_length_cm: no manual scale reference"
  ],
  "observation_notes": "A tapered metal object with a threaded end and a flat, narrower end. The surface shows some discoloration and faint, illegible markings near the narrower end."
}
```

### eval_112 · rocket · medium

```json
{
  "body_shape": "ogive",
  "fins_or_tail_visible": false,
  "fuze_visible": false,
  "driving_band_visible": false,
  "markings_visible": false,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "heavily_corroded",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": 3.5,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "estimated_length_cm: no manual scale reference",
    "markings_text: no visible markings to transcribe"
  ],
  "observation_notes": "An elongated, heavily corroded object with a tapered end and an open base, lying on the ground."
}
```

### eval_115 · rocket · medium

```json
{
  "body_shape": "cylindrical",
  "fins_or_tail_visible": true,
  "fuze_visible": false,
  "driving_band_visible": false,
  "markings_visible": false,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "heavily_corroded",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": true,
  "unclear_features": [
    "markings_text: no visible markings to transcribe",
    "estimated_length_cm: no manual scale reference",
    "length_to_width_ratio: objects partially outside frame"
  ],
  "observation_notes": "Multiple heavily corroded cylindrical objects are visible, partially submerged in water and mud. Each object has fin-like structures visible at one end. No distinct fuzes, driving bands, or markings are visible."
}
```

### eval_120 · not_ordnance · medium

```json
{
  "body_shape": "unclear",
  "fins_or_tail_visible": false,
  "fuze_visible": false,
  "driving_band_visible": false,
  "markings_visible": false,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "unclear",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": false,
  "image_quality_sufficient": true,
  "unclear_features": [
    "body_shape: no distinct object visible",
    "markings_text: no visible markings to transcribe",
    "surface_condition: no distinct object visible to assess surface condition",
    "estimated_length_cm: no distinct object visible and no manual scale reference",
    "length_to_width_ratio: no distinct object visible"
  ],
  "observation_notes": "The image shows disturbed soil with some dry plant matter. No distinct object is visible."
}
```

### eval_125 · not_ordnance · medium

```json
{
  "body_shape": "unclear",
  "fins_or_tail_visible": false,
  "fuze_visible": false,
  "driving_band_visible": false,
  "markings_visible": false,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "unclear",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": false,
  "image_quality_sufficient": true,
  "unclear_features": [
    "body_shape: no discernible object of interest",
    "markings_text: no visible markings to transcribe",
    "surface_condition: no single object to assess surface condition",
    "estimated_length_cm: no manual scale reference and no discernible object",
    "length_to_width_ratio: no discernible object to measure"
  ],
  "observation_notes": "The image shows a ground covered with fallen leaves of various colors (yellow, orange, brown) and some greyish rocks or ground visible between them. No distinct object of interest is present."
}
```

### eval_126 · not_ordnance · medium

```json
{
  "body_shape": "unclear",
  "fins_or_tail_visible": null,
  "fuze_visible": null,
  "driving_band_visible": null,
  "markings_visible": null,
  "markings_text": null,
  "color_bands": [],
  "surface_condition": "unclear",
  "embedded_in_ground": false,
  "estimated_length_cm": null,
  "length_to_width_ratio": null,
  "looks_manufactured": true,
  "image_quality_sufficient": false,
  "unclear_features": [
    "body_shape: object is blurry and partially obscured",
    "fins_or_tail_visible: object is partially obscured and blurry",
    "fuze_visible: object is partially obscured and blurry",
    "driving_band_visible: object is partially obscured and blurry",
    "markings_visible: object is too blurry and small to discern markings",
    "markings_text: markings are not visible/legible",
    "surface_condition: object is blurry, making surface details unclear",
    "estimated_length_cm: no manual scale reference",
    "length_to_width_ratio: object is partially visible and blurry"
  ],
  "observation_notes": "A small, blurry, metallic-looking object is partially visible in the bottom left corner, surrounded by green and dry grass. The image quality is low."
}
```

## 6. Operational metrics

- Records: 10
- Errors: 0
- Schema-validation errors: 0
- Retries: 0
- HTTP 429 responses: 0
- Cache hits: 0
- Average duration: 8027.5 ms
- Input tokens: 11600
- Output tokens: 2551
- Total cost: $0.0000

