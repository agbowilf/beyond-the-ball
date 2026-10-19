"""What each insight field means, taken from docs/detection-rules.md.

Agents receive these definitions so they explain the numbers rather than guess at them.
"""

# Top-level fields any claim may cite, besides the evidence fields.
COMMON_FIELDS = {
    "t": "Time of the key action, in seconds from the start of the clip",
    "team": "Team that made the play",
    "playerId": "Player credited with the insight",
    "confidence": "Detector confidence from 0 to 1",
}

FIELDS = {
    "SPACE_CREATOR": {
        "summary": "An off-ball run dragged a defender away from the zone a teammate then received the ball in.",
        "fields": {
            "playerId": "The runner whose movement created the space",
            "markerId": "The defender who followed the run",
            "runnerDisplacementM": "How far the runner moved over the 5 s before the pass, in metres",
            "markerDisplacementM": "How far the marker moved over the same window, in metres",
            "markerFollowCosine": "How closely the marker's movement matched the run's direction (1 = exactly)",
            "markerDistanceToTargetStartM": "Marker's distance to where the pass was received, at run start, in metres",
            "markerDistanceToTargetEndM": "Marker's distance to where the pass was received, when the pass was played",
            "nearestDefenderToTargetStartM": "Nearest outfield defender to the receiving zone at run start, in metres",
            "nearestDefenderToTargetEndM": "Nearest outfield defender to the receiving zone when the pass was played",
            "shotSecondsAfterPass": "Seconds from the pass to the shot",
        },
    },
    "SEQUENCE_ORIGIN": {
        "summary": "The action where a chance really began: the earliest pass that broke a line, "
                   "after which the attack kept moving forward to the shot.",
        "fields": {
            "playerId": "Who played the origin pass",
            "partnerId": "The other player in the one-two, or the receiver of a single line-breaking pass",
            "pattern": "ONE_TWO or LINE_BREAKING_PASS",
            "bypassedIds": "Opponents taken out of play by the line-breaking pass",
            "opponentsBypassed": "Number of opponents taken out of play",
            "lineBreakingPassT": "When the line-breaking pass was played, in seconds",
            "passesToShot": "Passes from the origin to the shot, origin included",
            "progressionM": "Ground gained toward goal from the origin pass to the shot, in metres",
            "secondsBeforeFinalPass": "How long before the assist the chance began, in seconds",
            "secondsBeforeShot": "How long before the shot the chance began, in seconds",
        },
    },
}


def citable_fields(insight):
    """Every field name a claim about this insight may cite."""
    keys = set(COMMON_FIELDS) | set(insight.get("evidence", {}))
    keys |= {k for k in insight if k not in ("type", "evidence")}
    return keys
