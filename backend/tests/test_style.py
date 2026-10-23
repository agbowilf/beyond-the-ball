import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.explain.models import Claim, Explanation  # noqa: E402
from backend.explain.style import check_style  # noqa: E402


def _exp(*texts, headline="No. 10's run opens up the space"):
    return Explanation(headline=headline, claims=[Claim(text=t, evidence=["runnerDisplacementM"]) for t in texts])


FAN = _exp("North London Red's No. 10 ran off the ball and dragged a defender away.",
           "That left loads of space, and the chance came 2.2 seconds later.")
COACH = _exp("H10 ran 14.5 m off the ball and A6 tracked the run.",
             "A6 ended 11.1 m from the receiving zone.",
             "The shot came 2.2 s after the pass.")
ANALYST = _exp("H10 covered 14.5 m in the 5 s before the pass.",
               "A6 followed with a direction match of 0.99.",
               "The detector is 90% confident.")


def test_each_audience_accepts_its_own_style():
    assert check_style("fan", FAN) == []
    assert check_style("coach", COACH) == []
    assert check_style("analyst", ANALYST) == []


def test_fan_rejects_more_than_one_number():
    assert any("at most one number" in p for p in check_style("fan", COACH))


def test_fan_rejects_jargon():
    exp = _exp("No. 10 pulled the marker out of the receiving zone.", "The space opened up.")
    problems = check_style("fan", exp)
    assert any("marker" in p and "receiving zone" in p for p in problems)


def test_analyst_needs_a_measurement_in_every_sentence():
    assert any("at least one measurement" in p for p in check_style("analyst", FAN))


def test_coach_limits_numbers_per_sentence():
    exp = _exp("H10 ran 14.5 m, A6 ran 9.6 m and ended 11.1 m away.", "A6 tracked the run.", "The space opened.")
    assert any("quotes 3 numbers" in p and "at most two" in p for p in check_style("coach", exp))


def test_praise_is_rejected_for_every_audience():
    exp = _exp("H10 made a clever 14.5 m run.", "A6 followed 9.6 m.", "A6 ended 11.1 m away.")
    for audience in ("fan", "coach", "analyst"):
        assert any("clever" in p for p in check_style(audience, exp))


def test_unmeasured_player_roles_are_rejected():
    exp = _exp("The midfield duo played a one-two.", "It cut out two defenders.", headline="No. 8 starts it")
    problems = check_style("fan", exp)
    assert any("midfield" in p and "duo" in p for p in problems)
    assert not any("defenders" in p for p in problems)


def test_field_names_and_codes_are_rejected():
    exp = _exp("A6 followed with a markerFollowCosine of 0.99.", "The pattern was ONE_TWO.", "It took 3.6 s.")
    problems = check_style("analyst", exp)
    assert any("markerFollowCosine" in p for p in problems) and any("ONE_TWO" in p for p in problems)


def test_plain_word_field_names_are_allowed():
    exp = _exp("H10 ran 14.5 m.", "The detector confidence was 90%.", "The pattern took 3.6 s.")
    assert check_style("analyst", exp) == []


def test_long_headline_feedback_gives_the_count():
    exp = _exp("No. 10 ran.", "The space opened.", headline="One two three four five six seven eight nine ten eleven")
    assert any("has 11 words" in p for p in check_style("fan", exp))


def test_claim_counts_differ_by_audience():
    assert any("Use exactly 3 claims" in p for p in check_style("coach", FAN))


def test_real_data_rejects_shirt_number_phrasing():
    exp = _exp("Metrica Away's No. 10 ran 21.5 m.", "The space opened.", headline="H10's run opens space")
    assert check_style("fan", exp) == []
    assert any("labels, not shirt numbers" in p for p in check_style("fan", exp, real_data=True))


def test_jargon_matches_whole_words_only():
    exp = _exp("Metrica Away's H10 ran far.", "The space opened.", headline="H10's run opens space")
    assert check_style("fan", exp) == []
