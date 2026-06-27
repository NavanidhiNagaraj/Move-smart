"""
recommender.py  –  SmartRecommender
Ranks ride options by a multi-factor AI score and generates plain-English insights.
"""
from __future__ import annotations
import math


class SmartRecommender:
    """
    Ranks ride options across price, ETA, comfort, eco, and contextual factors
    (weather, luggage, passenger count, budget, traffic, surge) and explains every choice.
    """

    # ── Weights by priority preset ────────────────────────────────────────────
    _WEIGHT_PRESETS: dict[str, dict] = {
        "Cheapest":     {"price": 0.50, "eta": 0.15, "comfort": 0.10, "eco": 0.10, "context": 0.15},
        "Fastest":      {"price": 0.10, "eta": 0.50, "comfort": 0.15, "eco": 0.05, "context": 0.20},
        "Comfort":      {"price": 0.15, "eta": 0.20, "comfort": 0.45, "eco": 0.05, "context": 0.15},
        "Eco Friendly": {"price": 0.10, "eta": 0.10, "comfort": 0.10, "eco": 0.55, "context": 0.15},
        "Balanced":     {"price": 0.25, "eta": 0.25, "comfort": 0.20, "eco": 0.10, "context": 0.20},
    }

    def rank(
        self,
        options: list[dict],
        num_people: int,
        luggage: bool,
        budget: float,
        vehicle_pref: str,
        priority: str,
        traffic: dict,
        weather: dict,
        surge: dict,
    ) -> list[dict]:
        """Score, sort, and annotate every ride option."""
        weights = self._WEIGHT_PRESETS.get(priority, self._WEIGHT_PRESETS["Balanced"])

        if not options:
            return []

        # Pre-compute min/max for normalisation
        fares   = [o["fare"]    for o in options]
        etas    = [o["eta"]     for o in options]
        comforts= [o["comfort"] for o in options]
        ecos    = [o["eco_score"] for o in options]

        min_f, max_f = min(fares), max(fares)
        min_e, max_e = min(etas),  max(etas)

        def norm(val, lo, hi, invert=False):
            if hi == lo:
                return 0.5
            s = (val - lo) / (hi - lo)
            return 1 - s if invert else s

        scored = []
        for opt in options:
            price_score   = norm(opt["fare"],       min_f, max_f, invert=True) * 100
            eta_score     = norm(opt["eta"],         min_e, max_e, invert=True) * 100
            comfort_score = norm(opt["comfort"],     1, 10) * 100
            eco_score_s   = norm(opt["eco_score"],   1, 10) * 100
            context_score = self._context_score(
                opt, num_people, luggage, budget, vehicle_pref,
                traffic, weather, surge
            )

            total = (
                weights["price"]   * price_score +
                weights["eta"]     * eta_score +
                weights["comfort"] * comfort_score +
                weights["eco"]     * eco_score_s +
                weights["context"] * context_score
            )

            opt = opt.copy()
            opt["score"]          = round(total)
            opt["reason"]         = self._reason(
                opt, num_people, luggage, budget, vehicle_pref,
                traffic, weather, surge, priority
            )
            opt["priority_match"] = priority
            scored.append(opt)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _context_score(
        self, opt, num_people, luggage, budget, vehicle_pref,
        traffic, weather, surge
    ) -> float:
        score = 50  # neutral baseline

        # Passenger fit
        if opt["capacity"] >= num_people:
            score += 20
        else:
            score -= 40  # can't fit — heavy penalty

        # Luggage
        if luggage and not opt["luggage_ok"]:
            score -= 30
        elif not luggage:
            pass  # neutral

        # Budget
        if opt["fare"] <= budget:
            score += 15
        elif opt["fare"] <= budget * 1.2:
            score -= 5
        else:
            score -= 20

        # Weather
        if weather.get("condition") == "Rainy":
            if opt["vehicle"] == "Bike":
                score -= 35
            elif opt["vehicle"] in ("Cab", "XL Cab"):
                score += 10

        # Traffic → prefer Metro
        if traffic.get("level") == "Heavy":
            if opt["vehicle"] == "Metro":
                score += 25
            elif opt["vehicle"] in ("Bike", "Auto"):
                score -= 10

        # Surge — penalise cab options when surge is high
        if surge.get("multiplier", 1) > 1.4:
            if opt["vehicle"] in ("Cab", "XL Cab"):
                score -= 15
            if opt["vehicle"] in ("Metro", "Bus"):
                score += 10

        # User vehicle preference
        if vehicle_pref != "No Preference":
            if opt["vehicle"] == vehicle_pref:
                score += 20
            else:
                score -= 5

        # Passenger-specific preference
        if num_people == 1 and opt["vehicle"] == "Bike":
            score += 8
        elif num_people == 2 and opt["vehicle"] == "Auto":
            score += 8
        elif 3 <= num_people <= 4 and opt["vehicle"] == "Cab":
            score += 12
        elif num_people >= 5 and opt["vehicle"] == "XL Cab":
            score += 20

        return max(0, min(100, score))

    def _reason(
        self, opt, num_people, luggage, budget, vehicle_pref,
        traffic, weather, surge, priority
    ) -> str:
        parts = []

        v = opt["vehicle"]

        # Passenger fit
        if num_people >= 5 and v == "XL Cab":
            parts.append(f"spacious for {num_people} people")
        elif num_people == 1 and v == "Bike":
            parts.append("solo rider — bike is the quickest door-to-door")
        elif num_people == 2 and v == "Auto":
            parts.append("auto fits 2 comfortably at lower cost")
        elif 3 <= num_people <= 4 and v == "Cab":
            parts.append(f"cab fits all {num_people} passengers")

        # Luggage
        if luggage and opt["luggage_ok"]:
            parts.append("handles your luggage")
        elif luggage and not opt["luggage_ok"]:
            parts.append("⚠️ luggage may not fit")

        # Weather
        if weather.get("condition") == "Rainy":
            if v == "Bike":
                parts.append("⚠️ avoid in rain")
            elif v in ("Cab", "XL Cab"):
                parts.append("enclosed ride in the rain")

        # Traffic
        if traffic.get("level") == "Heavy" and v == "Metro":
            parts.append("skips heavy road traffic on a dedicated track")
        elif traffic.get("level") == "Heavy" and v in ("Bike", "Auto"):
            parts.append("may be slowed by heavy traffic")

        # Surge
        if surge.get("multiplier", 1) > 1.3 and v in ("Cab", "XL Cab"):
            parts.append(f"surge {surge['multiplier']:.1f}× inflates fare")
        elif v in ("Metro", "Bus"):
            parts.append("fixed government fare — no surge")

        # Budget
        if opt["fare"] > budget:
            over = opt["fare"] - budget
            parts.append(f"₹{over:.0f} over your budget")
        else:
            parts.append("within budget")

        # Priority
        if priority == "Eco Friendly":
            parts.append(f"only {opt['carbon']:.1f} kg CO₂")
        elif priority == "Comfort":
            parts.append(f"comfort score {opt['comfort']}/10")

        if not parts:
            parts.append("solid all-round option")

        return " · ".join(parts).capitalize()

    def generate_insights(
        self, best: dict, budget: float, num_people: int,
        traffic: dict, weather: dict
    ) -> list[dict]:
        insights = []

        # Savings
        if budget > 0 and best["fare"] < budget:
            saved = budget - best["fare"]
            insights.append({
                "icon": "💰",
                "text": f"<strong>You save ₹{saved:.0f}</strong> compared to your budget on this trip.",
            })

        # Monthly estimate
        if best["fare"] > 0:
            monthly = best["fare"] * 22 * 0.7  # rough commuter estimate
            insights.append({
                "icon": "📅",
                "text": f"Estimated <strong>monthly commute cost ≈ ₹{monthly:.0f}</strong> at this fare.",
            })

        # Carbon
        baseline_cab_carbon = 0.21 * best.get("distance_km", 10)
        carbon_saved = max(0, baseline_cab_carbon - best["carbon"])
        if carbon_saved > 0:
            insights.append({
                "icon": "🌱",
                "text": f"This trip saves <strong>{carbon_saved:.1f} kg CO₂</strong> vs taking a cab.",
            })

        # Split fare
        if num_people > 1:
            insights.append({
                "icon": "👥",
                "text": f"Split equally: <strong>₹{best['fare']/num_people:.0f}/person</strong> for {num_people} people.",
            })

        # Weather advisory
        if weather.get("condition") == "Rainy":
            insights.append({
                "icon": "🌧️",
                "text": "It's raining — <strong>bikes avoided</strong>. Cab or Metro recommended.",
            })

        # Traffic advisory
        if traffic.get("level") == "Heavy":
            insights.append({
                "icon": "🚦",
                "text": "<strong>Heavy traffic</strong> detected. Metro is the fastest alternative right now.",
            })

        # Surge advisory
        if best.get("surge_mul", 1) > 1.3:
            insights.append({
                "icon": "⚡",
                "text": f"Surge pricing active ({best['surge_mul']:.1f}×). Consider waiting 20 min or taking Metro/Bus.",
            })

        return insights[:6]
