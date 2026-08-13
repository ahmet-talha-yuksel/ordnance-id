from scripts.inspect_observations import PROHIBITED_PATTERNS


def matches(text: str) -> set[str]:
    return {name for name, pattern in PROHIBITED_PATTERNS.items() if pattern.search(text)}


def test_policy_scanner_flags_identification_caliber_danger_and_advice() -> None:
    assert "ordnance_type_or_model" in matches("This is a mortar model.")
    assert "caliber_or_diameter_claim" in matches("The diameter is 81 mm.")
    assert "danger_or_risk" in matches("This object is dangerous and explosive.")
    assert "safety_advice" in matches("Do not approach or touch it.")


def test_visible_fuze_statement_is_not_misclassified_as_identification() -> None:
    assert matches("No fins, fuze, or readable markings are visible.") == set()
