"""Explain every insight in a file for each audience and save the results.

Usage: python -m backend.explain scenarios/01_decoy_run.insights.json [--audience fan coach analyst]
       [--only SEQUENCE_ORIGIN:coach ...]   regenerate just these, keeping the rest of the existing file

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
    args = parser.parse_args()
    only = {tuple(o.split(":")) for o in args.only}

    load_env()
    insights = json.loads(args.insights.read_text())
    scenario = json.loads(Path(str(args.insights).replace(".insights.json", ".json")).read_text())
    context = {"teams": {k: v["name"] for k, v in scenario["teams"].items()}}
    run = FoundryRunner()

    out = Path(str(args.insights).replace(".insights.json", ".explanations.json"))
    kept = json.loads(out.read_text())["explanations"] if only and out.exists() else []

    results = []
    for index, insight in enumerate(insights):
        for audience in args.audience:
            if only and (insight["type"], audience) not in only:
                results += [e for e in kept if e["insightIndex"] == index and e["audience"] == audience]
                continue
            result = await explain(insight, context, audience, run)
            results.append({"insightIndex": index, "type": insight["type"], "playerId": insight["playerId"], **result})
            print(f"{insight['type']:<16} {audience:<8} {result['status']} after {result['attempts']} attempt(s)")

    out.write_text(json.dumps({
        "scenarioId": scenario["scenarioId"],
        "model": run.model,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "explanations": results,
    }, indent=2) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
