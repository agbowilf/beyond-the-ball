"""Run all detectors on a scenario file and print structured insights as JSON.

Usage: python backend/run_analysis.py scenarios/01_decoy_run.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.analysis.space_creator import detect_space_creators  # noqa: E402
from backend.analysis.sequence_origin import detect_sequence_origins  # noqa: E402


def analyse(scenario):
    return detect_space_creators(scenario) + detect_sequence_origins(scenario)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: run_analysis.py <scenario.json>")
    scenario = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(analyse(scenario), indent=2))


if __name__ == "__main__":
    main()
