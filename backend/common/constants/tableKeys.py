"""Key builders for the single DynamoDB table (pk/sk, plus gsi1 and gsi2)."""

GSI1 = "gsi1"
GSI2 = "gsi2"
PROFILE_SK = "PROFILE"
STATS_PK = "STATS"
OPEN_REFERRALS_GSI1PK = "REFERRAL#OPEN"
UNDER_TREATMENT_GSI1PK = "TREATMENT#ACTIVE"
ACTIVE_PLANS_GSI1PK = "PLAN#ACTIVE"
ACTIVE_PLAN_SK = "PLAN#ACTIVE"
DEMO_CLOCK_PK = "DEMO"
DEMO_CLOCK_SK = "CLOCK"


def trackingPk(trackingId: str) -> str:
    return f"TRACK#{trackingId}"


def childPk(childId: str) -> str:
    return f"CHILD#{childId}"


def phoneGsi1Pk(phone: str) -> str:
    return f"PHONE#{phone}"


def areaGsi2Pk(districtCode: int) -> str:
    return f"AREA#{districtCode}"


def facilityGsi2Pk(facilityId: str) -> str:
    return f"FACILITY#{facilityId}"


def alertsGsi2Pk(districtCode: int) -> str:
    return f"ALERTS#{districtCode}"


def statsSk(districtCode: int, blockCode: int) -> str:
    return f"{districtCode}#{blockCode}"
