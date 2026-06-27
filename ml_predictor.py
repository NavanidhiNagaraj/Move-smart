"""
ml_predictor.py  –  Traffic, Weather, and Surge predictors.
Uses heuristic models with time-of-day, day-of-week, and location signals.
No external ML dependency required — fully self-contained.
"""
from __future__ import annotations
import hashlib
import math
import random
from datetime import datetime, time as dtime


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _stable_random(seed_str: str, lo: float = 0, hi: float = 1) -> float:
    """Deterministic random in [lo, hi] from a string seed."""
    digest = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return lo + (digest % 10000) / 10000 * (hi - lo)


def _parse_time(t) -> dtime:
    if isinstance(t, dtime):
        return t
    if isinstance(t, str):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(t, fmt).time()
            except ValueError:
                continue
    return datetime.now().time()


# ─── Traffic Predictor ────────────────────────────────────────────────────────
class TrafficPredictor:
    """
    Predicts traffic level based on time-of-day and a seeded route hash.
    Returns: {level: 'Low'|'Moderate'|'Heavy', delay_pct: float, description: str}
    """

    _RUSH_HOURS = {
        "morning": (7, 9),    # 7 AM – 9 AM
        "evening": (17, 20),  # 5 PM – 8 PM
    }

    def predict(self, source: str, destination: str, departure_time=None) -> dict:
        t = _parse_time(departure_time)
        hour = t.hour
        dow = datetime.now().weekday()  # 0=Mon … 6=Sun
        is_weekend = dow >= 5

        # Base traffic level from time
        in_morning_rush = self._RUSH_HOURS["morning"][0] <= hour < self._RUSH_HOURS["morning"][1]
        in_evening_rush = self._RUSH_HOURS["evening"][0] <= hour < self._RUSH_HOURS["evening"][1]

        # Route-specific jitter
        route_factor = _stable_random(source + destination, 0, 0.3)

        if is_weekend:
            base_level = 0.2 + route_factor
        elif in_morning_rush or in_evening_rush:
            base_level = 0.65 + route_factor
        elif 10 <= hour < 16:
            base_level = 0.35 + route_factor
        elif 22 <= hour or hour < 6:
            base_level = 0.05 + route_factor
        else:
            base_level = 0.30 + route_factor

        if base_level < 0.33:
            level, delay_pct = "Low", round(base_level * 15)
            desc = "Traffic is moving freely."
        elif base_level < 0.65:
            level, delay_pct = "Moderate", round(base_level * 40)
            desc = "Some congestion expected — minor delays."
        else:
            level, delay_pct = "Heavy", round(base_level * 70)
            desc = "Heavy congestion — expect significant delays on road."

        return {
            "level":      level,
            "delay_pct":  min(delay_pct, 80),
            "description": desc,
            "rush_hour":  in_morning_rush or in_evening_rush,
        }


# ─── Weather Predictor ────────────────────────────────────────────────────────
class WeatherPredictor:
    """
    Returns a simple weather snapshot.
    In production this would call a weather API.
    Here we use time + date heuristics for a realistic demo.
    """

    def predict(self) -> dict:
        now = datetime.now()
        month = now.month

        # Monsoon months in Bengaluru: June–September
        is_monsoon = 6 <= month <= 9
        hour = now.hour

        rain_seed = _stable_random(str(now.date()), 0, 1)
        rain_prob = 0.60 if is_monsoon else 0.10

        if rain_seed < rain_prob:
            condition = "Rainy"
            temp_c = 22 + _stable_random("temp_rain", 0, 4)
            desc = "Rainy conditions. Avoid two-wheelers."
        elif rain_seed < rain_prob + 0.25:
            condition = "Cloudy"
            temp_c = 24 + _stable_random("temp_cloud", 0, 4)
            desc = "Overcast skies, comfortable for all vehicles."
        else:
            condition = "Clear"
            temp_c = 26 + _stable_random("temp_clear", 0, 6)
            desc = "Clear skies — all vehicles suitable."

        return {
            "condition":  condition,
            "temp_c":     round(temp_c, 1),
            "description": desc,
            "rain_prob":  round(rain_prob * 100),
        }


# ─── Surge Predictor ─────────────────────────────────────────────────────────
class SurgePredictor:
    """
    Predicts ride-hailing surge multiplier based on time of day and day of week.
    """

    def predict(self, departure_time=None) -> dict:
        t = _parse_time(departure_time)
        hour = t.hour
        dow = datetime.now().weekday()
        is_weekend = dow >= 5

        # Surge peaks during rush hours and late nights
        if (7 <= hour <= 9) or (17 <= hour <= 20):
            base_mul = 1.5 if not is_weekend else 1.2
        elif 22 <= hour or hour <= 5:
            base_mul = 1.6
        elif is_weekend and 11 <= hour <= 14:
            base_mul = 1.3
        else:
            base_mul = 1.0

        # Add small jitter
        jitter = _stable_random(str(hour) + str(dow), -0.1, 0.15)
        multiplier = max(1.0, round(base_mul + jitter, 2))

        if multiplier >= 1.5:
            level = "High"
            desc  = f"High surge ({multiplier:.1f}×) — consider Metro or Bus."
        elif multiplier >= 1.2:
            level = "Moderate"
            desc  = f"Moderate surge ({multiplier:.1f}×) — fares slightly elevated."
        else:
            level = "Normal"
            desc  = "Normal pricing — no surge active."

        return {
            "multiplier": multiplier,
            "level":      level,
            "description": desc,
        }
