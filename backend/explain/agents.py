"""Explanation agents built on Microsoft Agent Framework and a Microsoft Foundry model deployment.

Two agents collaborate on each insight:

- the Explainer writes a headline and claims for a fan, coach or analyst, citing the insight fields each
  claim uses, in a style that suits that reader;
- the Fact-checker reviews that draft against the insight.

The deterministic grounding guard (grounding.py) and audience style rules (style.py) check every draft
as well. If any check or the fact-checker finds a problem, the explainer revises once with that
feedback, up to twice. If it still fails, the explanation is withheld rather than shown.
"""
import json
import os

from .glossary import COMMON_FIELDS, FIELDS
from .grounding import check
from .style import check_pattern, check_style, check_team_names
from .models import Explanation, Review

AUDIENCES = {
    "fan": """A casual football fan watching the replay on their phone.
- Talk like a friendly commentator explaining what they just saw. Simple everyday words only.
- No statistics: quote at most ONE number in the whole explanation, and only if it makes the moment hit harder.
- Never use jargon such as marker, receiving zone, line-breaking, bypass, displacement, progression, cosine,
  confidence or detector. Say "the defender marking them", "the space", "cut out two players" instead.
- Plain words must keep the exact meaning: distances are measured to the spot where the pass was received,
  not to the ball or the goal.
- Name players by team and shirt number, for example "North London Red's No. 10", then "No. 10".
- No praise or criticism such as clever or brilliant; let what happened speak for itself.
- Lead with the most surprising measured fact. If the runner never touched the ball (runnerTouches is 0), say so:
  fans love a player who changed a move without touching the ball.
- 1 or 2 short sentences, each under 20 words; the replay shows the rest. A punchy headline of at most 10 words, for example
  "No. 10's decoy run opens the door".""",
    "coach": """A coach breaking down the move with their players.
- Use football coaching language, but only for ideas this insight type measures (see "whatItMeans" and the field
  definitions). For example, "marker" and "receiving zone" belong to Space Creator insights, not Sequence Origin.
- Name only tactics the insight measured; for example, do not say players were pressing.
- Explain the mechanism: what the attacker did, how the defender reacted, and what that opened up.
- Use only the numbers that make the point, at most two per sentence, with units.
- Name players by id, for example H10 or A6.
- Exactly 3 sentences.""",
    "analyst": """A performance analyst writing a match report.
- Precise and measured. Every sentence quotes at least one measurement with its unit.
- Include the timings and the detector confidence where relevant.
- Technical terms are fine. Name players by id, for example H10 or A6.
- 3 or 4 sentences.""",
}

EXPLAINER_INSTRUCTIONS = """You explain football insights that a detection engine has already measured from tracking data.
Rules:
- Use only the facts in the insight. Never add tactics, intentions, skill judgements or anything else that was not measured.
- In particular, never state a location (near the line, in the box, down the wing), a direction (down the field, forward,
  wide), a speed (sprinted, quick), or a player's position or role (defender, midfielder, centre-back) unless a field
  says so. The marker in a Space Creator insight is "the defender marking" the runner; that much is measured.
- Write a headline and claims as the audience guide says. Each claim is one sentence stating one fact.
- The headline quotes no numbers; numbers go only in claims, where they are cited.
- A claim may describe a measured fact in plain words without quoting its number, but it must still cite the field.
- For every claim, list in `evidence` the exact field names it relies on, taken from the field definitions.
- Quote numbers exactly as they appear in the insight, or rounded to a whole number. Never compute new numbers such as differences or totals.
- Be precise about who did what: attribute each action to the player and pass the field definitions say.
- Follow any notes in the insight's brief; they override the audience guide.
- If backLineDropM is 5 or more, include it in football language (for example "the back line dropped deep as H10 ran in
  behind"), citing backLineDropM. Describe it as happening during the run, never as caused or forced by the runner.
- Refer to players by their ids, for example H10 or A6, and never with gendered pronouns. Never write field names
  such as markerFollowCosine in the text.
- Keep each time span's exact start and end as defined (for example, played versus received).
- Write the headline in sentence case."""

FACT_CHECKER_INSTRUCTIONS = """You fact-check a draft explanation of a football insight against the insight it describes.
Approve only if every claim is fully supported by the fields it cites. Go through the draft word by word and list any
location, direction, speed, tactic or player role that no field states, for example "near the line", "down the field",
"sprinted" or "defensive line". Also list as an issue each claim that is unsupported,
misreads a field, attributes an action to the wrong player or pass, invents a detail, or speculates about intent or
quality. Check attributions against the field definitions carefully. Plain-language wording for fans is fine, but
it must keep what was measured: for example, a distance to where the pass was received is not a distance to the
ball. Do not rewrite the draft."""


def who_did_what(insight):
    """Plain statement of each player's action, generated from the insight so agents cannot misread the pattern."""
    if insight["type"] != "SEQUENCE_ORIGIN":
        return None
    p, q, n = insight["playerId"], insight["partnerId"], insight["evidence"]["opponentsBypassed"]
    if insight["pattern"] == "ONE_TWO":
        return (f"One-two: {p} passed to {q} (the origin pass), then {q} passed back to {p}; that return pass is the "
                f"line-breaking pass that bypassed {n} opponents.")
    return (f"Single pass, no one-two: {p}'s pass to {q} is both the origin and the line-breaking pass; it bypassed "
            f"{n} opponents. {q} received it and did not pass back.")


def brief(insight, context):
    """Everything an agent may know about one insight, as JSON."""
    spec = FIELDS[insight["type"]]
    return json.dumps({
        "insightType": insight["type"],
        "whatItMeans": spec["summary"],
        # Named by role: in real clips the attacking team is labelled HOME whatever its real name, which misled agents.
        "teams": {
            "attacking (made the play)": context.get("teams", {}).get(insight["team"]),
            "defending": context.get("teams", {}).get("AWAY" if insight["team"] == "HOME" else "HOME"),
        },
        "notes": context.get("notes", []) + [x for x in [who_did_what(insight)] if x],
        "fieldDefinitions": {**COMMON_FIELDS, **spec["fields"]},
        # The team label (HOME/AWAY) is replaced by the attacking team's real name, so it cannot be misread as one.
        "insight": {**insight, "team": context.get("teams", {}).get(insight["team"], insight["team"])},
    }, indent=2)


async def explain(insight, context, audience, run, max_revisions=2, log=None):
    """Draft, check and if needed revise an explanation. `run(role, prompt, schema)` calls an agent.

    `log(step, detail)`, if given, is called at each step (used by `--trace` to show the loop working).
    """
    log = log or (lambda step, detail: None)
    facts = brief(insight, context)
    prompt = f"Audience: {AUDIENCES[audience]}\n\nInsight:\n{facts}"
    draft = await run("explainer", prompt, Explanation)
    log("draft", draft)

    for attempt in range(1, max_revisions + 2):
        problems = (check(insight, draft) + check_style(audience, draft, real_data=context.get("realData", False))
                    + check_team_names(draft, context.get("teams", {}), insight["team"])
                    + check_pattern(insight, draft))
        log("code checks", problems)
        review = await run("fact_checker", f"Insight:\n{facts}\n\nDraft:\n{draft.model_dump_json(indent=2)}", Review)
        log("fact-checker", review)
        issues = problems + ([] if review.approved else review.issues or ["The fact-checker did not approve."])
        if not issues:
            log("approved", attempt)
            return {"status": "approved", "audience": audience, **draft.model_dump(), "attempts": attempt}
        if attempt > max_revisions:
            log("withheld", issues)
            return {"status": "withheld", "audience": audience, "attempts": attempt, "problems": issues}
        log("revise", issues)
        feedback = "\n".join(f"- {i}" for i in issues)
        draft = await run(
            "explainer",
            f"{prompt}\n\nYour previous draft:\n{draft.model_dump_json(indent=2)}\n\nFix these problems:\n{feedback}",
            Explanation,
        )
        log("draft", draft)


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
