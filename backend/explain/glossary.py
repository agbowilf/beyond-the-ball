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
            "markerDisplacementM": "How far the marker moved in total over the same window, in metres. This is NOT how much "
                                   "further from the receiving spot the marker ended up; that is markerPullM",
            "markerFollowCosine": "How closely the marker's movement matched the run's direction (1 = exactly)",
            "markerDistanceToTargetStartM": "Marker's distance to where the pass was received, at run start, in metres",
            "markerDistanceToTargetEndM": "Marker's distance to where the pass was received, when the pass was played",
            "nearestDefenderToTargetStartM": "Nearest outfield defender to the receiving zone at run start, in metres",
            "nearestDefenderToTargetEndM": "Nearest outfield defender to the receiving zone when the pass was played",
            "shotSecondsAfterPass": "Seconds from the moment the pass was played (not received) to the shot",
            "runnerTouches": "Times the runner played, received or shot the ball from the start of the run to the "
                             "shot; 0 means the runner never touched the ball",
            "freeSpaceStartM2": "Receiving space at run start, in square metres: the free area around the receiving "
                                "spot, out to the nearest outfield defender. Call it receiving space",
            "freeSpaceEndM2": "Receiving space when the pass was played, in square metres",
            "freeSpaceGainM2": "How much the receiving space grew during the run, in square metres",
            "freeSpaceRatio": "How many times larger the receiving space was when the pass was played than at run start",
            "markerPullM": "How much further from the receiving spot the marker ended up, in metres (not the total "
                           "distance the marker moved, which is markerDisplacementM)",
            "backLineDropM": "How far the defending back line dropped towards its own goal during the run, in metres "
                             "(negative means it stepped up). It happened during the run; it does NOT show the run "
                             "alone caused it, so never say the runner pushed or forced the line back",
            "targetZone": "Lane and area of the spot where the pass was received, from the attacking team's point of "
                          "view. It describes the receiving spot only, not where any other player was",
        },
    },
    "SEQUENCE_ORIGIN": {
        "summary": "The action where a chance really began: the earliest pass that broke a line, "
                   "after which the attack kept moving forward to the shot. For a ONE_TWO, the origin is the "
                   "first pass (playerId to partnerId) and the line-breaking pass is the partner's return "
                   "(partnerId back to playerId); only the return took opponents out of play.",
        "fields": {
            "playerId": "Who played the origin pass (for a ONE_TWO, the first pass of the one-two)",
            "partnerId": "The other player in the one-two, who played the line-breaking return pass; "
                         "or the receiver of a single line-breaking pass",
            "pattern": "ONE_TWO or LINE_BREAKING_PASS",
            "bypassedIds": "Opponents bypassed by the line-breaking pass (goal-side of the ball when it was played, not "
                           "when it was received), not by the origin pass. Call them opponents or players, not "
                           "defenders: their positions were not measured, and say bypassed, not taken out of play",
            "opponentsBypassed": "Number of opponents bypassed by the line-breaking pass",
            "lineBreakingPassT": "When the line-breaking pass was played, in seconds",
            "passesToShot": "Passes from the origin to the shot, origin included",
            "progressionM": "Ground gained toward goal from the origin pass to the shot, in metres",
            "secondsBeforeFinalPass": "How long before the assist was played (not received) the chance began, in seconds",
            "secondsBeforeShot": "How long before the shot the chance began, in seconds",
        },
    },
}


def citable_fields(insight):
    """Every field name a claim about this insight may cite."""
    keys = set(COMMON_FIELDS) | set(insight.get("evidence", {}))
    keys |= {k for k in insight if k not in ("type", "evidence")}
    return keys
