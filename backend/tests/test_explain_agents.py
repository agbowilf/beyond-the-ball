"""The explain loop, driven by a scripted fake instead of a live model, so it is free and repeatable."""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.explain.agents import explain  # noqa: E402
from backend.explain.models import Claim, Explanation, Review  # noqa: E402

INSIGHT = next(i for i in json.loads((ROOT / "scenarios" / "01_decoy_run.insights.json").read_text())
               if i["type"] == "SPACE_CREATOR")
CONTEXT = {"teams": {"HOME": "North London Red", "AWAY": "South Coast Blue"}}

GROUNDED = Explanation(headline="H10's run pulled A6 out of the space", claims=[
    Claim(text="H10 ran 14.5 m and A6 followed.", evidence=["runnerDisplacementM", "markerId"]),
    Claim(text="A6 ended 11.1 m from the receiving zone.", evidence=["markerDistanceToTargetEndM"]),
])
INVENTED = Explanation(headline="H10's run pulled A6 out of the space", claims=[
    Claim(text="A6 was dragged 20 m out of position.", evidence=["markerDisplacementM"]),
])
APPROVED = Review(approved=True, issues=[])


class FakeRunner:
    """Returns scripted outputs per agent role and records every prompt it was sent."""

    def __init__(self, explainer, checker):
        self.outputs = {"explainer": list(explainer), "fact_checker": list(checker)}
        self.calls = []

    async def __call__(self, role, prompt, schema):
        self.calls.append((role, prompt))
        out = self.outputs[role].pop(0)
        assert isinstance(out, schema)
        return out


def _explain(runner, audience="fan"):
    return asyncio.run(explain(INSIGHT, CONTEXT, audience, runner))


def test_grounded_draft_is_approved_first_time():
    runner = FakeRunner([GROUNDED], [APPROVED])
    result = _explain(runner)
    assert result["status"] == "approved" and result["attempts"] == 1
    assert result["headline"] == GROUNDED.headline
    assert [r for r, _ in runner.calls] == ["explainer", "fact_checker"]


def test_explainer_sees_the_evidence_definitions_and_audience():
    runner = FakeRunner([GROUNDED], [APPROVED])
    _explain(runner, audience="coach")
    prompt = runner.calls[0][1]
    assert '"markerDistanceToTargetEndM"' in prompt
    assert "Marker's distance to where the pass was received" in prompt
    assert "A coach reviewing the move" in prompt


def test_invented_number_triggers_a_revision_with_the_guard_problem():
    runner = FakeRunner([INVENTED, GROUNDED], [APPROVED, APPROVED])
    result = _explain(runner)
    assert result["status"] == "approved" and result["attempts"] == 2
    revision_prompt = runner.calls[2][1]
    assert runner.calls[2][0] == "explainer"
    assert "Number 20 is not in the fields this claim cites" in revision_prompt


def test_fact_checker_rejection_also_triggers_a_revision():
    rejected = Review(approved=False, issues=["Claim 2 says A6 was beaten for pace, which was not measured."])
    runner = FakeRunner([GROUNDED, GROUNDED], [rejected, APPROVED])
    result = _explain(runner)
    assert result["status"] == "approved" and result["attempts"] == 2
    assert "beaten for pace" in runner.calls[2][1]


def test_explanation_is_withheld_if_the_revision_still_fails():
    runner = FakeRunner([INVENTED, INVENTED], [APPROVED, APPROVED])
    result = _explain(runner)
    assert result["status"] == "withheld" and result["attempts"] == 2
    assert "headline" not in result
    assert any("Number 20" in p for p in result["problems"])
