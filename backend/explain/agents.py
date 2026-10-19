"""Explanation agents built on Microsoft Agent Framework and a Microsoft Foundry model deployment.

Two agents collaborate on each insight:

- the Explainer writes a headline and claims for an audience, citing the insight fields each claim uses;
- the Fact-checker reviews that draft against the insight.

The deterministic grounding guard (grounding.py) checks every draft as well. If the guard or the
fact-checker finds a problem, the explainer revises once with that feedback. If the revision still
fails, the explanation is withheld rather than shown.
"""
import json
import os

from .glossary import COMMON_FIELDS, FIELDS
from .grounding import check
from .models import Explanation, Review

AUDIENCES = {
    "fan": "A football fan watching the highlight. Plain words, no jargon, lively but accurate.",
    "coach": "A coach reviewing the move. Focus on the movement, the timing and what the defender did.",
    "analyst": "A performance analyst. Precise; quote the key measurements with their units.",
}

EXPLAINER_INSTRUCTIONS = """You explain football insights that a detection engine has already measured from tracking data.
Rules:
- Use only the facts in the insight. Never add tactics, intentions, skill judgements or anything else that was not measured.
- Write a headline of at most 12 words and 2 to 4 claims. Each claim is one sentence stating one fact.
- For every claim, list in `evidence` the exact field names it relies on, taken from the field definitions.
- Quote numbers exactly as they appear in the insight, or rounded to a whole number. Never compute new numbers such as differences or totals.
- Refer to players by their ids, for example H10 or A6."""

FACT_CHECKER_INSTRUCTIONS = """You fact-check a draft explanation of a football insight against the insight it describes.
Approve only if every claim is fully supported by the fields it cites. List as an issue each claim that is unsupported,
misreads a field, invents a detail, or speculates about intent or quality. Do not rewrite the draft."""


def brief(insight, context):
    """Everything an agent may know about one insight, as JSON."""
    spec = FIELDS[insight["type"]]
    return json.dumps({
        "insightType": insight["type"],
        "whatItMeans": spec["summary"],
        "teams": context.get("teams", {}),
        "fieldDefinitions": {**COMMON_FIELDS, **spec["fields"]},
        "insight": insight,
    }, indent=2)


async def explain(insight, context, audience, run, max_revisions=1):
    """Draft, check and if needed revise an explanation. `run(role, prompt, schema)` calls an agent."""
    facts = brief(insight, context)
    prompt = f"Audience: {AUDIENCES[audience]}\n\nInsight:\n{facts}"
    draft = await run("explainer", prompt, Explanation)

    for attempt in range(1, max_revisions + 2):
        problems = check(insight, draft)
        review = await run("fact_checker", f"Insight:\n{facts}\n\nDraft:\n{draft.model_dump_json(indent=2)}", Review)
        issues = problems + ([] if review.approved else review.issues or ["The fact-checker did not approve."])
        if not issues:
            return {"status": "approved", "audience": audience, **draft.model_dump(), "attempts": attempt}
        if attempt > max_revisions:
            return {"status": "withheld", "audience": audience, "attempts": attempt, "problems": issues}
        feedback = "\n".join(f"- {i}" for i in issues)
        draft = await run(
            "explainer",
            f"{prompt}\n\nYour previous draft:\n{draft.model_dump_json(indent=2)}\n\nFix these problems:\n{feedback}",
            Explanation,
        )


class FoundryRunner:
    """Runs the agents on a Microsoft Foundry model deployment through Agent Framework.

    Reads FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL and authenticates with `az login`.
    """

    def __init__(self, project_endpoint=None, model=None):
        # Imported here so the rest of the package, and its tests, work without the Azure packages.
        from agent_framework import Agent
        from agent_framework.foundry import FoundryChatClient
        from azure.identity import AzureCliCredential

        self.model = model or os.environ["FOUNDRY_MODEL"]
        client = FoundryChatClient(
            project_endpoint=project_endpoint or os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=self.model,
            credential=AzureCliCredential(),
        )
        self.agents = {
            "explainer": Agent(client, EXPLAINER_INSTRUCTIONS, name="Explainer"),
            "fact_checker": Agent(client, FACT_CHECKER_INSTRUCTIONS, name="FactChecker"),
        }

    async def __call__(self, role, prompt, schema):
        response = await self.agents[role].run(prompt, options={"response_format": schema})
        if response.value is None:
            raise RuntimeError(f"{role} returned no structured output: {response.text[:200]}")
        return response.value
