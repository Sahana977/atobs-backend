"""
Road graph (24 nodes, 41 edges around Marathahalli) + comfort-aware routing.

Edge cost = ROUTE_ALPHA * travel_minutes + ROUTE_BETA * crowding_penalty
  travel_minutes   = base_minutes * traffic multiplier
  crowding_penalty = max(0, predicted_occupancy - 50)   (only penalise above 'comfortable')

beta = 0 gives the plain fastest route; beta > 0 trades a few minutes for a less crowded bus.
"""
import heapq
from dataclasses import dataclass

import numpy as np

from app.config import RANDOM_SEED, ROUTE_ALPHA, ROUTE_BETA

STOPS = [
    "Marathahalli Bridge", "Kalamandir", "Spice Garden", "Munnekolala", "Kundalahalli Gate",
    "AECS Layout", "Brookefield", "Graphite India", "ITPL", "Hope Farm",
    "Whitefield", "Kadugodi", "Hoodi", "Mahadevapura", "Brigade Metropolis",
    "KR Puram", "Tin Factory", "Doddanekundi", "HAL", "Kadubeesanahalli",
    "Panathur", "Bellandur", "Varthur Kodi", "Sarjapur Road Jn",
]
STOP_IDS = {name: f"S{i + 1:02d}" for i, name in enumerate(STOPS)}

# 24 ring edges + 17 cross-links = 41 edges
_CHORDS = [(0, 5), (0, 18), (0, 19), (1, 17), (2, 6), (3, 7), (4, 8), (5, 9), (6, 13),
           (8, 12), (9, 22), (11, 22), (12, 15), (13, 17), (16, 18), (19, 21), (20, 23)]

TRAFFIC_MULTIPLIER = {"low": 1.0, "medium": 1.3, "high": 1.7, "severe": 2.3}


@dataclass
class Edge:
    a: int
    b: int
    base_minutes: float
    distance_km: float
    trip_id: str  # representative BMTC trip serving this segment


def build_edges(seed: int = RANDOM_SEED) -> list[Edge]:
    rng = np.random.default_rng(seed)
    pairs = [(i, (i + 1) % len(STOPS)) for i in range(len(STOPS))] + _CHORDS
    edges = []
    for a, b in pairs:
        km = round(float(rng.uniform(0.8, 3.5)), 2)
        edges.append(Edge(a, b, round(km * 2.4, 1), km, f"T{rng.integers(1, 61):03d}"))
    return edges


EDGES = build_edges()


def graph_info() -> dict:
    return {
        "nodes": [{"index": i, "stop_id": STOP_IDS[n], "name": n} for i, n in enumerate(STOPS)],
        "edges": [{"from": STOPS[e.a], "to": STOPS[e.b], "distance_km": e.distance_km,
                   "base_minutes": e.base_minutes, "trip_id": e.trip_id} for e in EDGES],
        "node_count": len(STOPS),
        "edge_count": len(EDGES),
    }


def resolve_stop(name_or_id: str) -> int:
    key = name_or_id.strip().lower()
    for i, n in enumerate(STOPS):
        if key in (n.lower(), STOP_IDS[n].lower()):
            return i
    raise KeyError(f"Unknown stop: {name_or_id}")


def dijkstra(src: int, dst: int, edge_costs: dict[tuple[int, int], float]) -> list[int]:
    adj: dict[int, list[tuple[int, float]]] = {}
    for (a, b), c in edge_costs.items():
        adj.setdefault(a, []).append((b, c))
    dist, prev = {src: 0.0}, {}
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == dst:
            break
        if d > dist.get(u, float("inf")):
            continue
        for v, c in adj.get(u, []):
            nd = d + c
            if nd < dist.get(v, float("inf")):
                dist[v], prev[v] = nd, u
                heapq.heappush(pq, (nd, v))
    if dst not in dist:
        raise ValueError("No path between these stops")
    path, node = [dst], dst
    while node != src:
        node = prev[node]
        path.append(node)
    return path[::-1]


def plan_route(origin: str, destination: str, traffic_level: str,
               occupancy_fn, beta: float = ROUTE_BETA) -> dict:
    """
    occupancy_fn(list_of_(trip_id, stop_id)) -> list_of_predicted_occupancy.
    Passed in so this module doesn't depend on the ML layer (easy to test).
    """
    src, dst = resolve_stop(origin), resolve_stop(destination)
    mult = TRAFFIC_MULTIPLIER[traffic_level]

    # Both directions of every edge; occupancy is predicted at the stop you arrive at
    directed = [(e.a, e.b, e) for e in EDGES] + [(e.b, e.a, e) for e in EDGES]
    occ = occupancy_fn([(e.trip_id, STOP_IDS[STOPS[v]]) for _, v, e in directed])

    info, fast_cost, comfort_cost = {}, {}, {}
    for (u, v, e), o in zip(directed, occ):
        minutes = e.base_minutes * mult
        info[(u, v)] = (minutes, o, e)
        fast_cost[(u, v)] = minutes
        comfort_cost[(u, v)] = ROUTE_ALPHA * minutes + beta * max(0.0, o - 50)

    def describe(path):
        legs = []
        for u, v in zip(path, path[1:]):
            minutes, o, e = info[(u, v)]
            legs.append({"from": STOPS[u], "to": STOPS[v], "trip_id": e.trip_id,
                         "minutes": round(minutes, 1), "distance_km": e.distance_km,
                         "predicted_occupancy_pct": o})
        occs = [l["predicted_occupancy_pct"] for l in legs] or [0]
        return {
            "stops": [STOPS[i] for i in path],
            "total_minutes": round(sum(l["minutes"] for l in legs), 1),
            "total_km": round(sum(l["distance_km"] for l in legs), 2),
            "avg_occupancy_pct": round(float(np.mean(occs)), 1),
            "max_occupancy_pct": round(float(np.max(occs)), 1),
            "legs": legs,
        }

    fastest = describe(dijkstra(src, dst, fast_cost))
    comfort = describe(dijkstra(src, dst, comfort_cost))
    return {
        "origin": STOPS[src], "destination": STOPS[dst], "traffic_level": traffic_level,
        "beta": beta, "fastest_route": fastest, "comfort_route": comfort,
        "extra_minutes_for_comfort": round(comfort["total_minutes"] - fastest["total_minutes"], 1),
        "occupancy_reduction_pct": round(fastest["avg_occupancy_pct"] - comfort["avg_occupancy_pct"], 1),
    }
