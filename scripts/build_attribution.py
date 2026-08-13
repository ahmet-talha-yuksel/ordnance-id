"""Generate the committed CC BY 4.0 attribution for evaluation data."""

from pathlib import Path

import typer

from ordnance_id.data_sources import load_catalog


def main(output: Path = Path("evals/ATTRIBUTION.md")) -> None:
    """Render attribution fields from the validated source catalog."""

    source = load_catalog(Path("config/data_sources.yaml")).by_name("ctx-uxo-v2")
    text = f"""# Evaluation Data Attribution

## {source.title}

- Authors: {", ".join(source.authors)}
- Affiliation: {source.affiliation}
- DOI: [{source.doi}](https://doi.org/{source.doi})
- Source: {source.landing_page}
- Licence: {source.license}
- Changes: A bounded subset of the original test split is copied and filenames are normalized.
  Source annotations are mapped to family-level labels without manual relabeling. No image content
  is intentionally modified.

The image files remain excluded from Git and are not redistributed by this repository.
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    typer.echo(f"Wrote {output}")


if __name__ == "__main__":
    typer.run(main)

