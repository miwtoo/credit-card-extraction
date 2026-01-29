import json
from pathlib import Path

from credit_card_extraction.extractor import StatementParser
from credit_card_extraction.models import NormalizedLine

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ttb_statement_sample.txt"
GOLDEN_PATH = Path(__file__).parent / "fixtures" / "ttb_statement_sample_golden.json"


def _load_fixture_lines() -> list[NormalizedLine]:
    lines: list[NormalizedLine] = []
    for raw in FIXTURE_PATH.read_text().splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        page_str, y_str, text = stripped.split("|", 2)
        lines.append(
            NormalizedLine(
                text=text.strip(),
                page=int(page_str),
                y=float(y_str),
            )
        )
    return lines


def test_ttb_golden_fixture_parse():
    parser = StatementParser()
    result = parser.parse(_load_fixture_lines())

    actual = result.model_dump(mode="json")
    expected = json.loads(GOLDEN_PATH.read_text())

    assert actual == expected
