"""Lambda entry point for the HTTP API (API Gateway proxy to FastAPI through Mangum)."""

from mangum import Mangum

from common.http.fastApiFactory import createFastApiApp
from modules.abdmBridge.routes import router as abdmRouter
from modules.alerts.routes import router as alertsRouter
from modules.children.routes import router as childrenRouter
from modules.dashboard.routes import router as dashboardRouter
from modules.demo.routes import router as demoRouter
from modules.geo.routes import router as geoRouter
from modules.homePlan.routes import router as parentRouter
from modules.parentChannel.routes import router as parentChannelRouter
from modules.referrals.routes import router as referralsRouter
from modules.screening.routes import router as screeningRouter

app = createFastApiApp(
    "up4ds-app-api",
    [
        geoRouter,
        childrenRouter,
        screeningRouter,
        referralsRouter,
        alertsRouter,
        parentRouter,
        parentChannelRouter,
        dashboardRouter,
        abdmRouter,
        demoRouter,
    ],
)

handler = Mangum(app, lifespan="off")
