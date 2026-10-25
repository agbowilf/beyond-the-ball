"""Explain every insight in a file for each audience and save the results.

Usage: python -m backend.explain scenarios/01_decoy_run.insights.json [--audience fan coach analyst]
       [--only SEQUENCE_ORIGIN:coach ...]   regenerate just these, keeping the rest of the existing file
       [--trace]                            print every agent step: drafts, code checks, fact-checker, revisions
       [--no-save]                          do not write the file (for demos; committed explanations stay reviewed)

Needs FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL (in the environment or .env) and `az login`.
"""
import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .agents import AUDIENCES, FoundryRunner, explain

ROOT = Path(__file__).resolve().parents[2]


def trace(step, detail):
    """Readable view of the agent loop, for showing it working."""
    rule = "-" * 72
    if step == "draft":
        print(f"\n{rule}\nEXPLAINER draft\n  # {detail.headline}")
        for c in detail.claims:
            print(f"  - {c.text}\n      cites: {', '.join(c.evidence)}")
    elif step == "code checks":
        print("CODE CHECKS (grounding, style, teams, pattern): " + ("pass" if not detail else ""))
        for p in detail:
            print(f"  x {p}")
    elif step == "fact-checker":
        print("FACT-CHECKER agent: " + ("approved" if detail.approved else "rejected"))
        for issue in detail.issues:
            print(f"  x {issue}")
    elif step == "revise":
        print(">> sent back to the Explainer with these problems")
    elif step == "approved":
        print(f"\nAPPROVED after {detail} attempt(s)\n{rule}")
    elif step == "withheld":
        print(f"\nWITHHELD: never shown\n{rule}")


def load_env(path=ROOT / ".env"):
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


async def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("insights", type=Path)
    parser.add_argument("--audience", nargs="+", choices=list(AUDIENCES), default=list(AUDIENCES))
    parser.add_argument("--only", nargs="+", metavar="TYPE:AUDIENCE", default=[],
                        help="regenerate only these explanations and keep the rest of the existing file")
    parser.add_argument("--trace", action="store_true", help="print every agent step")
    parser.add_argument("--no-save", action="store_true", help="do not write the explanations file")
    args = parser.parse_args()
    only = {tuple(o.split(":")) for o in args.only}

    load_env()
    insights = json.loads(args.insights.read_text())
    scenario = json.loads(Path(str(args.insights).replace(".insights.json", ".json")).read_text())
    context = {"teams": {k: v["name"] for k, v in scenario["teams"].items()}}
    if "source" in scenario:
        # Real data: player numbers are labels assigned by our converter, not shirt numbers.
        context["realData"] = True
        context["notes"] = [
            "This is real, anonymised match tracking data. Player ids such as H10 are labels, not shirt numbers: "
            "refer to players by id (for example 'H10' or 'player H10'), never as 'No. 10', for every audience."
        ]
    run = FoundryRunner()

    out = Path(str(args.insights).replace(".insights.json", ".explanations.json"))
    kept = json.loads(out.read_text())["explanations"] if only and out.exists() else []

    results = []
    for index, insight in enumerate(insights):
        for audience in args.audience:
            if only and (insight["type"], audience) not in only:
                results += [e for e in kept if e["insightIndex"] == index and e["audience"] == audience]
                continue
            if args.trace:
                print(f"\n=== {insight['type']} · {insight['playerId']} · for a {audience} ===")
            result = await explain(insight, context, audience, run, log=trace if args.trace else None)
            results.append({"insightIndex": index, "type": insight["type"], "playerId": insight["playerId"], **result})
            print(f"{insight['type']:<16} {audience:<8} {result['status']} after {result['attempts']} attempt(s)")

    if args.no_save:
        print("not saved (--no-save)")
        return
    out.write_text(json.dumps({
        "scenarioId": scenario["scenarioId"],
        "model": run.model,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "explanations": results,
    }, indent=2) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
