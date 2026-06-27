import random
import math
from datetime import datetime

# ─── Vehicle catalogue ───────────────────────────────────────────────────────
VEHICLES = {
    "Bike": {
        "icon": "🏍️",
        "base_per_km": 8,
        "base_fare": 25,
        "capacity": 1,
        "luggage_ok": False,
        "avg_speed_kmh": 28,
        "carbon_per_km": 0.06,
        "comfort": 2,
        "eco_score": 7,
    },
    "Auto": {
        "icon": "🛺",
        "base_per_km": 12,
        "base_fare": 30,
        "capacity": 3,
        "luggage_ok": True,
        "avg_speed_kmh": 22,
        "carbon_per_km": 0.09,
        "comfort": 5,
        "eco_score": 6,
    },
    "Cab": {
        "icon": "🚕",
        "base_per_km": 16,
        "base_fare": 50,
        "capacity": 4,
        "luggage_ok": True,
        "avg_speed_kmh": 26,
        "carbon_per_km": 0.21,
        "comfort": 8,
        "eco_score": 4,
    },
    "XL Cab": {
        "icon": "🚐",
        "base_per_km": 22,
        "base_fare": 80,
        "capacity": 7,
        "luggage_ok": True,
        "avg_speed_kmh": 24,
        "carbon_per_km": 0.28,
        "comfort": 9,
        "eco_score": 3,
    },
    "Metro": {
        "icon": "🚇",
        "base_per_km": 3,
        "base_fare": 15,
        "capacity": 999,
        "luggage_ok": False,
        "avg_speed_kmh": 45,
        "carbon_per_km": 0.03,
        "comfort": 6,
        "eco_score": 10,
        "walk_minutes": 8,
    },
    "Bus": {
        "icon": "🚌",
        "base_per_km": 2,
        "base_fare": 10,
        "capacity": 999,
        "luggage_ok": False,
        "avg_speed_kmh": 18,
        "carbon_per_km": 0.04,
        "comfort": 4,
        "eco_score": 9,
        "walk_minutes": 5,
    },
}

# ─── Helpers ─────────────────────────────────────────────────────────────────
def _estimate_distance(source: str, destination: str) -> float:
    """Deterministic pseudo-distance from string hash so same pair always same distance."""
    seed = abs(hash(source.lower() + destination.lower())) % 1000
    rng = random.Random(seed)
    return round(rng.uniform(4, 28), 1)

def _traffic_multiplier(traffic: dict) -> float:
    lvl = traffic.get("level", "Low")
    return {"Low": 1.0, "Moderate": 1.35, "Heavy": 1.75}.get(lvl, 1.0)

def _calculate_fare(vehicle_data: dict, distance_km: float, surge: dict,
                    traffic: dict) -> float:
    base  = vehicle_data["base_fare"] + vehicle_data["base_per_km"] * distance_km
    t_mul = _traffic_multiplier(traffic)
    s_mul = surge.get("multiplier", 1.0)
    is_fare_based = vehicle_data.get("base_per_km", 0) > 5
    if is_fare_based:
        fare = base * t_mul * s_mul
    else:
        fare = base  # metro/bus fixed
    jitter = random.Random(hash(str(distance_km) + vehicle_data["icon"])).uniform(0.92, 1.08)
    return round(fare * jitter, 0)

def _calculate_eta(vehicle_data: dict, distance_km: float, traffic: dict) -> int:
    speed = vehicle_data["avg_speed_kmh"]
    t_mul = _traffic_multiplier(traffic)
    travel_min = (distance_km / speed) * 60 * t_mul
    walk_min = vehicle_data.get("walk_minutes", 0)
    return max(5, round(travel_min + walk_min))

# ─── Main API ─────────────────────────────────────────────────────────────────
def get_ride_options(
    source: str,
    destination: str,
    departure_time: str,
    num_people: int,
    luggage: bool,
    budget: float,
    vehicle_pref: str,
    priority: str,
    traffic: dict,
    weather: dict,
    surge: dict,
) -> list[dict]:
    """Return list of ride option dicts for all applicable vehicles."""
    distance = _estimate_distance(source, destination)
    options = []

    for name, vdata in VEHICLES.items():
        # XL Cab only for 5+ people
        if name == "XL Cab" and num_people < 5:
            continue
        if name != "XL Cab" and name == "Cab" and num_people > 6:
            continue

        fare    = _calculate_fare(vdata, distance, surge, traffic)
        eta     = _calculate_eta(vdata, distance, traffic)
        carbon  = round(vdata["carbon_per_km"] * distance, 2)

        options.append({
            "vehicle":     name,
            "icon":        vdata["icon"],
            "fare":        fare,
            "eta":         eta,
            "carbon":      carbon,
            "comfort":     vdata["comfort"],
            "eco_score":   vdata["eco_score"],
            "capacity":    vdata["capacity"],
            "luggage_ok":  vdata["luggage_ok"],
            "distance_km": distance,
            "surge_mul":   surge.get("multiplier", 1.0),
            "reason":      "",  # filled by recommender
            "score":       0,
            "priority_match": priority,
        })

    return options

def get_fare_prediction(current_fare: float, surge_multiplier: float) -> dict:
    """Predict fare 15 and 30 minutes from now based on surge trend."""
    import random
    rng = random.Random(42)

    # Surge typically stabilises or rises slightly in peak hours
    trend_15 = surge_multiplier * rng.uniform(0.96, 1.08)
    trend_30 = surge_multiplier * rng.uniform(0.90, 1.15)

    fare_now = current_fare
    fare_15  = round(current_fare * (trend_15 / surge_multiplier), 0)
    fare_30  = round(current_fare * (trend_30 / surge_multiplier), 0)

    book_now = fare_15 >= fare_now or fare_30 >= fare_now

    if book_now:
        advice = "📌 Book Now — fares likely to rise"
        reason = f"Surge currently {surge_multiplier:.1f}× and trending upward."
    else:
        advice = "⏳ Wait — fares may drop in 15–30 min"
        reason = "Surge appears to be easing off. Waiting could save you money."

    return {
        "now":    fare_now,
        "in_15":  fare_15,
        "in_30":  fare_30,
        "advice": advice,
        "reason": reason,
    }
