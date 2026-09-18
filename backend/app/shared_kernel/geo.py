# Pure-Python haversine over an in-memory candidate set, no PostGIS/spatial
# index. Deliberate for a Stage One pilot (~6 suburbs, a small worker base) —
# not an oversight. Revisit (PostGIS `geography` column + GIST index, filter
# pushed into SQL) only once Stage Two/Three coverage actually grows the
# candidate counts enough to matter — see BACK-008 in docs/backlog.md.
#
# Lives in shared_kernel (not the suburbs app) because both the jobs and
# crews apps' matching services depend on it directly as a pure function —
# no I/O, no port/DI needed (ADR-007).
from decimal import Decimal
from math import atan2, cos, radians, sin, sqrt

from app.shared_kernel.enums import DistanceBandEnum

EARTH_RADIUS_KM = 6371.0
NEARBY_KM = 3.0
MODERATE_KM = 8.0

BAND_RANK = {
    DistanceBandEnum.SAME_SUBURB: 0,
    DistanceBandEnum.NEARBY: 1,
    DistanceBandEnum.MODERATE: 2,
    DistanceBandEnum.FAR: 3,
}


def haversine_km(lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal) -> float:
    p1, p2 = radians(float(lat1)), radians(float(lat2))
    dphi = radians(float(lat2) - float(lat1))
    dlambda = radians(float(lon2) - float(lon1))
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * atan2(sqrt(a), sqrt(1 - a))


def classify_distance(
    suburb_a: str, suburb_b: str, coords: dict[str, tuple[Decimal, Decimal]]
) -> tuple[DistanceBandEnum, float]:
    if suburb_a == suburb_b:
        return DistanceBandEnum.SAME_SUBURB, 0.0

    lat1, lon1 = coords[suburb_a]
    lat2, lon2 = coords[suburb_b]
    km = haversine_km(lat1, lon1, lat2, lon2)

    if km < NEARBY_KM:
        return DistanceBandEnum.NEARBY, km
    if km < MODERATE_KM:
        return DistanceBandEnum.MODERATE, km
    return DistanceBandEnum.FAR, km
