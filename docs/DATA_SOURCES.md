# Data Sources and Provenance

Every candidate source must be recorded before its data is used.

| Source | Type | Access | Licence | Download date | Notes |
|---|---|---|---|---|---|
| _Example: source name and canonical URL_ | _Images / metadata / reference_ | _Public / restricted_ | _Licence and version_ | _YYYY-MM-DD_ | _Provenance, restrictions, transformations_ |
| [CTX-UXO v2](https://zenodo.org/records/17052675) | Images and COCO/YOLO annotations | Public Zenodo record | CC BY 4.0 | Set by `manifest.json` on download | DOI `10.21227/cwnm-de53`; MD5 `4191257476e65a50f72dfb9d3ad3213d` |

## CTX-UXO v2

**CTX-UXO: A Comprehensive Dataset for Detection and Identification of UneXploded
Ordnances**, by Gheorghe Marian Craioveanu and Grigore Stamatescu, is published by the
National University of Science and Technology Politehnica Bucharest under CC BY 4.0. The
Zenodo archive provides 3,520 images and 15,449 annotated instances across train, validation,
and test splits, with repositories for binary classification/detection, multiclass detection, and
instance segmentation in COCO and YOLO formats.

The collection includes both real ordnance and replicas. Replica diversity does not establish
field validity and is explicitly treated as a dataset limitation. The pinned archive is
`CTX_UXO_DS_v2_2025.zip` (3,895,410,390 bytes), MD5
`4191257476e65a50f72dfb9d3ad3213d`.

Download and verify it from the repository root:

```bash
PYTHONPATH=src uv run python scripts/fetch_data.py list
PYTHONPATH=src uv run python scripts/fetch_data.py download ctx-uxo-v2
```

The downloader resumes partial transfers, verifies MD5 before extraction, and records successful
acquisition in ignored `data/raw/manifest.json`. Do not redistribute the archive from this
repository; follow the original record and licence terms.

## Data rules

- Raw data is never committed to Git.
- Data with an unverified or incompatible licence is not used.
- Images with unclear provenance are not scraped or incorporated.
- No documents, images, or derived material from any employer or internship context are used.
- Each accepted item retains its source, licence, acquisition date, and transformation history.
- Personal or sensitive metadata is minimised; EXIF GPS is removed by default.
- Redistributing data requires a separate review of the original licence and usage conditions.
