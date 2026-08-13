from pathlib import Path

from PIL import Image

from ordnance_id.data_analysis.tiers import load_class_tiers
from ordnance_id.evals.io import load_eval_set
from ordnance_id.evals.pilot import select_pilot


def test_pilot_selection_is_deterministic_and_stratified(tmp_path: Path) -> None:
    eval_set = load_eval_set(Path("evals/datasets/eval_set_v1.yaml"))
    tiers = load_class_tiers(Path("config/class_tiers.yaml")).mapping()
    image_dir = tmp_path / "eval_images"
    image_dir.mkdir()
    for sample in eval_set.samples:
        Image.new("RGB", (100, 100)).save(image_dir / sample.filename)

    first = select_pilot(eval_set.samples, image_dir, tiers, seed=0)
    second = select_pilot(eval_set.samples, image_dir, tiers, seed=0)
    assert [item.sample.id for item in first] == [item.sample.id for item in second]
    assert sum(item.tier == "reportable" for item in first) == 4
    assert sum(item.tier == "limited" for item in first) == 2
    assert sum(item.tier == "insufficient" for item in first) == 1
    assert sum(not item.sample.ground_truth.is_ordnance for item in first) == 3
    assert any(item.size_bucket == "small" for item in first)
