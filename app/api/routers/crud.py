"""All CRUD routers, collected so main.py can include them in one loop."""
from app.api.routers import depot
from app.api.routers import stop
from app.api.routers import route
from app.api.routers import route_stop
from app.api.routers import bus
from app.api.routers import trip
from app.api.routers import traffic_reading
from app.api.routers import occupancy_reading
from app.api.routers import alert
from app.api.routers import app_user
from app.api.routers import feedback

CRUD_ROUTERS = [
    depot.router,
    stop.router,
    route.router,
    route_stop.router,
    bus.router,
    trip.router,
    traffic_reading.router,
    occupancy_reading.router,
    alert.router,
    app_user.router,
    feedback.router,
]
