"""Daily follow-up, run by EventBridge: home activities, weekly progress, referral and treatment reminders."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from common.messaging import whatsAppService
from modules.alerts.alertService import createAlert
from modules.children import dbService as childrenDb
from modules.homePlan import planService
from modules.referrals import dbService as referralsDb

logger = logging.getLogger(__name__)
REFERRAL_REMINDER_DAYS = (2, 7)
REFERRAL_ALERT_DAY = 14


def daysSince(isoTimestamp: str, today: date) -> int:
    return (today - date.fromisoformat(isoTimestamp[:10])).days


def followUpPlans(today: date) -> int:
    plans = planService.listActivePlans()
    for plan in plans:
        child = childrenDb.getChild(plan["childId"])
        planService.sendTodaysActivities(child, plan, today)
        if daysSince(plan["weekStartedOn"], today) >= 7:
            planService.evaluateWeek(child, plan, today)
    return len(plans)


def followUpReferrals(today: date) -> int:
    referrals = referralsDb.listOpenReferrals()
    for referral in referrals:
        age = daysSince(referral["createdAt"], today)
        dueReminders = [day for day in REFERRAL_REMINDER_DAYS if age >= day and day not in referral["remindersSent"]]
        fields: dict[str, Any] = {}
        if dueReminders:
            whatsAppService.sendText(
                referral["guardianPhone"],
                (
                    f"याद दिलाना: {referral['childName']} को {referral['facilityName']} में डॉक्टर को दिखाना है। "
                    "जाँच और इलाज मुफ़्त है।"
                ),
            )
            fields["remindersSent"] = referral["remindersSent"] + dueReminders
        if age >= REFERRAL_ALERT_DAY and not referral.get("alertRaised"):
            createAlert(
                childrenDb.getChild(referral["childId"]),
                "referralNotReached",
                f"{referral['childName']}: {age} दिन से रेफ़रल के बाद अस्पताल नहीं पहुँचे।",
            )
            fields["alertRaised"] = True
        if fields:
            referralsDb.updateReferral(referral["childId"], referral["referralId"], fields)
    return len(referrals)


def followUpTreatments(today: date) -> int:
    """Reminds the family the day before each check-up or therapy session, and weekly about medicines."""
    referrals = referralsDb.listReferralsUnderTreatment()
    for referral in referrals:
        if referral.get("lastReminderOn") == today.isoformat():
            continue
        carePlan = referral["carePlan"]
        tomorrow = (today + timedelta(days=1)).isoformat()
        messages = []
        if tomorrow in carePlan["checkupDates"]:
            messages.append("कल डॉक्टर से जाँच का दिन है।")
        if tomorrow in carePlan["therapyDates"]:
            messages.append("कल थेरेपी का दिन है।")
        if carePlan["medicines"] and daysSince(referral["diagnosedAt"], today) % 7 == 0:
            messages += [f"दवा: {medicine['name']}, {medicine['scheduleHi']}" for medicine in carePlan["medicines"]]
        if messages:
            whatsAppService.sendText(referral["guardianPhone"], f"{referral['childName']}: " + " ".join(messages))
            referralsDb.updateReferral(
                referral["childId"], referral["referralId"], {"lastReminderOn": today.isoformat()}
            )
    return len(referrals)


def runDaily(now: datetime) -> dict[str, int]:
    today = now.date()
    summary = {
        "plans": followUpPlans(today),
        "openReferrals": followUpReferrals(today),
        "underTreatment": followUpTreatments(today),
    }
    logger.info("Follow-up run date=%s summary=%s", today, summary)
    return summary
