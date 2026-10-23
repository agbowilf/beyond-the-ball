"""Run every detector on each scenario clip in a folder and save the insights next to it.

Usage: python3 scripts/analyse_clips.py external-data/metrica/clips
Writes <clip>.insights.json beside each <clip>.json and prints one line per detection.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.run_analysis import analyse  # noqa: E402


def summary(insight):
    ev = insight["evidence"]
    if insight["type"] == "SPACE_CREATOR":
        return (f"Space Creator  {insight['playerId']} drags {insight['markerId']}, pull {ev['markerPullM']} m, "
                f"space x{ev['freeSpaceRatio']}, conf {insight['confidence']:.2f}")
    return (f"Sequence Origin  {insight['playerId']} -> {insight['partnerId']} ({insight['pattern']}), "
            f"bypassed {len(insight['bypassedIds'])}, {ev['secondsBeforeShot']} s before shot, "
            f"conf {insight['confidence']:.2f}")


def main():
    folder = Path(sys.argv[1])
    for path in sorted(p for p in folder.glob("*.json") if not p.name.endswith(".insights.json")):
        insights = analyse(json.loads(path.read_text()))
        path.with_suffix(".insights.json").write_text(json.dumps(insights, indent=1) + "\n")
        for i in insights:
            print(f"{path.stem}  t={i['t']:5.1f}  {summary(i)}")


if __name__ == "__main__":
    main()
