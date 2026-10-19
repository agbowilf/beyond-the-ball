"""Every explanation committed to the repo must still pass the grounding guard and its audience's style rules."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.explain.grounding import check  # noqa: E402
from backend.explain.models import Explanation  # noqa: E402
from backend.explain.style import check_style  # noqa: E402


def test_committed_explanations_pass_every_check():
    for path in sorted((ROOT / "scenarios").glob("*.explanations.json")):
        insights = json.loads(Path(str(path).replace(".explanations.json", ".insights.json")).read_text())
        for e in json.loads(path.read_text())["explanations"]:
            if e["status"] != "approved":
                continue
            exp = Explanation(headline=e["headline"], claims=e["claims"])
            problems = check(insights[e["insightIndex"]], exp) + check_style(e["audience"], exp)
            assert problems == [], f"{path.name} {e['type']}/{e['audience']}: {problems}"
