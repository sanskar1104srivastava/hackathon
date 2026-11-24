"""One child through the whole journey, against an in-memory DynamoDB (moto). No AI, WhatsApp or ABDM calls."""

import json
import os
import unittest
from datetime import UTC, date, datetime
from pathlib import Path

import boto3
from moto import mock_aws

TABLE_DEFINITION = Path(__file__).resolve().parents[1] / "deploy" / "tableDefinition.json"
TEST_ENV = {
    "AWS_DEFAULT_REGION": "ap-south-1",
    "AWS_ACCESS_KEY_ID": "test",
    "AWS_SECRET_ACCESS_KEY": "test",
    "mainTableName": "up4ds-test-main",
    "appEnv": "test",
    "parentChannelToken": "test-channel-token",
}


@mock_aws
class ApiFlowTest(unittest.TestCase):
    def setUp(self):
        os.environ.update(TEST_ENV)
        definition = json.loads(TABLE_DEFINITION.read_text()) | {"TableName": TEST_ENV["mainTableName"]}
        boto3.client("dynamodb", region_name="ap-south-1").create_table(**definition)

        from fastapi.testclient import TestClient

        from common.config.settings import getSettings
        from common.db.dynamoDbService import getDb
        from modules.appApi.main import app

        getSettings.cache_clear()
        getDb.cache_clear()
        self.client = TestClient(app)

    def call(self, method: str, path: str, expectedStatus: int = 200, **kwargs):
        response = self.client.request(method, path, **kwargs)
        self.assertEqual(response.status_code, expectedStatus, response.text)
        return response.json()

    def test_screening_to_referral_home_plan_alert_and_dashboard(self):
        district = self.call("GET", "/v1/districts")[0]
        block = district["blocks"][0]
        dateOfBirth = date(date.today().year - 2, 1, 15)
        child = self.call(
            "POST",
            "/v1/children",
            201,
            json={
                "name": "Riya",
                "sex": "female",
                "dateOfBirth": dateOfBirth.isoformat(),
                "guardianName": "Sunita",
                "guardianPhone": "9876543210",
                "districtCode": district["districtCode"],
                "blockCode": block["blockCode"],
            },
        )
        self.assertNotIn("parentAccessToken", child)

        checks = self.call("GET", "/v1/checks", params={"ageMonths": 24})["checks"]
        self.assertIn("muac", {check["id"] for check in checks})

        screening = {
            "screeningId": "phone-made-id-0001",
            "setting": "anganwadi",
            "workerId": "asha-7",
            "consentGiven": True,
            "screenedAt": datetime.now(UTC).isoformat(),
            "measurements": {"weightKg": 13.2, "heightCm": 93, "muacCm": 14.5, "haemoglobinGdl": 6.5},
            "answers": {"walksAlone": False, "singleWords": True},
        }
        result = self.call("POST", f"/v1/children/{child['childId']}/screenings", 201, json=screening)
        domains = result["screening"]["outcome"]["domains"]
        self.assertEqual(domains["deficiencies"]["colour"], "red")
        self.assertEqual(domains["development"]["colour"], "yellow")
        self.assertIsNotNone(result["referral"])
        self.assertEqual(result["homePlan"]["focusAreas"], ["movement"])

        resent = self.call("POST", f"/v1/children/{child['childId']}/screenings", 201, json=screening)
        self.assertTrue(resent["duplicate"])

        parentPath, token = child["parentLinkPath"].split("?token=")
        parentView = self.call("GET", f"/v1{parentPath}", params={"token": token})
        self.assertTrue(parentView["homePlan"]["todaysActivities"])
        self.call("GET", f"/v1{parentPath}", 401, params={"token": "wrong"})

        referral = result["referral"]
        inbox = self.call("GET", f"/v1/facilities/{referral['facilityId']}/referrals")
        self.assertEqual([item["referralId"] for item in inbox], [referral["referralId"]])
        referralPath = f"/v1/children/{child['childId']}/referrals/{referral['referralId']}"
        self.call("POST", f"{referralPath}/arrival")
        diagnosed = self.call(
            "POST",
            f"{referralPath}/diagnosis",
            json={
                "doctorName": "Dr Mehta",
                "diagnosisText": "Severe anaemia confirmed",
                "carePlan": {
                    "careInstructionsHi": "रोज़ आयरन सिरप दें",
                    "medicines": [{"name": "Iron syrup", "scheduleHi": "रोज़ सुबह"}],
                },
            },
        )
        self.assertEqual(diagnosed["status"], "underTreatment")

        self.call("POST", "/v1/demo/skip-week")
        self.call("POST", "/v1/demo/skip-week")
        alerts = self.call("GET", "/v1/alerts", params={"districtCode": district["districtCode"]})
        self.assertEqual([alert["kind"] for alert in alerts], ["noImprovement"])

        totals = self.call("GET", "/v1/dashboard/summary")["totals"]
        self.assertEqual(
            {key: totals[key] for key in ("screened", "referred", "reached", "homePlans", "alerts")},
            {"screened": 1, "referred": 1, "reached": 1, "homePlans": 1, "alerts": 1},
        )

        status = self.call(
            "GET",
            "/v1/parent-channel/status",
            params={"phone": "9876543210"},
            headers={"X-Channel-Token": "test-channel-token"},
        )
        self.assertIn("Riya", status["children"][0]["summaryHi"])


if __name__ == "__main__":
    unittest.main()
