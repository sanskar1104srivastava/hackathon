import unittest
from datetime import UTC, datetime

from modules.screening.growthService import computeZScores, lmsAt, zScore
from modules.screening.requests import Measurements, ScreeningInput
from modules.screening.rulesEngine import ChildFacts, evaluateScreening


def makeInput(**overrides) -> ScreeningInput:
    fields = {
        "screeningId": "test-screening-1",
        "setting": "anganwadi",
        "screenedAt": datetime(2026, 11, 22, tzinfo=UTC),
        "workerId": "asha-1",
        "consentGiven": True,
    }
    return ScreeningInput(**(fields | overrides))


class GrowthServiceTest(unittest.TestCase):
    def test_who_median_is_zero(self):
        scores = computeZScores("male", 0, weightKg=3.3464, heightCm=49.8842)
        self.assertEqual(scores.weightForAge, 0)
        self.assertEqual(scores.heightForAge, 0)

    def test_published_minus_two_sd_at_birth(self):
        # WHO weight-for-age table, boys at birth: -2 SD is 2.5 kg (2.46 before rounding).
        lms = lmsAt("weianthro.txt", "male", 0)
        self.assertAlmostEqual(lms.valueAtSd(-2), 2.46, places=2)
        self.assertAlmostEqual(zScore(lms.valueAtSd(-2), lms, restricted=True), -2, places=6)

    def test_restricted_adjustment_beyond_three_sd(self):
        lms = lmsAt("weianthro.txt", "female", 365)
        sd2, sd3 = lms.valueAtSd(-2), lms.valueAtSd(-3)
        self.assertAlmostEqual(zScore(sd3 - (sd2 - sd3), lms, restricted=True), -4, places=6)

    def test_length_rows_are_interpolated(self):
        low, high = lmsAt("wflanthro.txt", "male", 65.0), lmsAt("wflanthro.txt", "male", 65.1)
        self.assertAlmostEqual(lmsAt("wflanthro.txt", "male", 65.05).m, (low.m + high.m) / 2, places=9)

    def test_school_age_uses_2007_bmi_reference(self):
        median = lmsAt("bfawho2007.txt", "male", 120).m
        scores = computeZScores("male", round(120 * 30.4375), weightKg=median * 1.4**2, heightCm=140)
        self.assertAlmostEqual(scores.bmiForAge, 0, delta=0.05)
        self.assertIsNone(scores.weightForHeight)


class RulesEngineTest(unittest.TestCase):
    toddler = ChildFacts(sex="female", ageDays=730)

    def test_all_normal_is_green(self):
        outcome = evaluateScreening(self.toddler, makeInput(measurements=Measurements(muacCm=14, haemoglobinGdl=12)))
        self.assertEqual(outcome.overall, "green")
        self.assertEqual(outcome.nextSteps, [])

    def test_severe_anaemia_refers(self):
        outcome = evaluateScreening(self.toddler, makeInput(measurements=Measurements(haemoglobinGdl=6.5)))
        self.assertEqual(outcome.domains["deficiencies"].colour, "red")
        self.assertEqual(outcome.nextSteps, ["referral"])

    def test_muac_bands(self):
        yellow = evaluateScreening(self.toddler, makeInput(measurements=Measurements(muacCm=12.0)))
        red = evaluateScreening(self.toddler, makeInput(measurements=Measurements(muacCm=11.0)))
        self.assertEqual(yellow.domains["deficiencies"].colour, "yellow")
        self.assertEqual(red.domains["deficiencies"].colour, "red")

    def test_one_delayed_milestone_is_watched_two_are_referred(self):
        one = evaluateScreening(self.toddler, makeInput(answers={"walksAlone": False, "singleWords": True}))
        two = evaluateScreening(self.toddler, makeInput(answers={"walksAlone": False, "singleWords": False}))
        self.assertEqual(one.domains["development"].colour, "yellow")
        self.assertEqual(one.nextSteps, ["homePlan"])
        self.assertEqual(two.domains["development"].colour, "red")

    def test_mchat_medium_risk_is_yellow(self):
        risky = {"mchat01": False, "mchat02": True, "mchat05": True, "mchat10": False, "mchat11": True}
        outcome = evaluateScreening(self.toddler, makeInput(answers=risky))
        self.assertEqual(outcome.domains["development"].findings[0].noteEn, "M-CHAT-R score 4")
        self.assertEqual(outcome.domains["development"].colour, "yellow")

    def test_ai_unsure_refers_and_out_of_age_checks_are_ignored(self):
        observations = [{"checkId": "cleftLip", "outcome": "unsure"}, {"checkId": "neuralTube", "outcome": "seen"}]
        outcome = evaluateScreening(self.toddler, makeInput(aiObservations=observations))
        self.assertEqual(outcome.domains["defects"].colour, "red")
        self.assertEqual([f.checkId for f in outcome.domains["defects"].findings], ["cleftLip"])

    def test_speech_below_expected_is_yellow(self):
        outcome = evaluateScreening(ChildFacts("male", 1500), makeInput(speech={"shownCount": 10, "namedCount": 3}))
        self.assertEqual(outcome.domains["development"].colour, "yellow")


if __name__ == "__main__":
    unittest.main()
