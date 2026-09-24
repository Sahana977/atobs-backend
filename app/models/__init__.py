"""Every table in the app, in dependency order (parents first)."""
from app.models import depot
from app.models import stop
from app.models import route
from app.models import route_stop
from app.models import bus
from app.models import trip
from app.models import traffic_reading
from app.models import occupancy_reading
from app.models import alert
from app.models import app_user
from app.models import feedback

ALL_MODELS = [
    depot,
    stop,
    route,
    route_stop,
    bus,
    trip,
    traffic_reading,
    occupancy_reading,
    alert,
    app_user,
    feedback,
]
