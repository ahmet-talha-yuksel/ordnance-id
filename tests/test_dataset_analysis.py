import json
from pathlib import Path

from ordnance_id.data_analysis.discovery import analyze_dataset, discover_repositories


def test_discovers_and_analyzes_coco_without_directory_assumptions(tmp_path: Path) -> None:
    repository = tmp_path / "unexpected" / "annotations"
    repository.mkdir(parents=True)
    (repository / "test_objects.json").write_text(
        json.dumps(
            {
                "images": [{"id": 1, "file_name": "one.jpg", "width": 100, "height": 50}],
                "categories": [{"id": 4, "name": "mortar"}],
                "annotations": [
                    {"id": 1, "image_id": 1, "category_id": 4, "bbox": [0, 0, 20, 10]}
                ],
            }
        )
    )

    assert discover_repositories(tmp_path) == [(repository, "coco")]
    report = analyze_dataset(tmp_path)
    split = report.repositories[0].splits[0]
    assert split.name == "test"
    assert split.image_count == 1
    assert split.class_counts == {"mortar": 1}
    assert split.bbox_area_fractions == [0.04]

