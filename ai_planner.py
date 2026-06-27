"""
ai_planner.py  –  AI Travel Planner
A conversational travel assistant powered by the Anthropic API.
Parses natural-language travel intent and returns structured travel plans.
"""
from __future__ import annotations
import json
import re
from datetime import datetime

import requests

from ml_predictor import TrafficPredictor, WeatherPredictor, SurgePredictor
from ride_engine import get_ride_options
from recommender import SmartRecommender

# ─── System prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MoveSmart AI, a friendly and expert travel planning assistant for Indian cities, primarily Bengaluru.

Your job is to help users plan their journey. You:
1. Extract travel intent from casual, natural-language messages (source, destination, deadline, budget, group size, luggage, preferences).
2. Provide a complete travel plan with:
   - Recommended vehicle and why
   - Estimated fare (₹)
   - Estimated arrival time
   - Alternative options
   - Smart tips (traffic, weather, surge)
3. Maintain conversational context across messages (remember what the user told you earlier).
4. Format responses with emojis and clear sections — but keep it concise and human.
5. If critical info is missing (e.g. destination), ask for it directly.
6. Always mention cost per person if group size > 1.
7. Always mention if it's raining or heavy traffic and adjust the recommendation accordingly.
8. Give a confidence score (e.g. "AI Confidence: 87%") for your recommendation.

Keep responses under 300 words unless the user asks for detail.
Use ₹ for Indian Rupees. Use Indian city/area names naturally.
Never say you're an AI language model — you are MoveSmart AI."""


class AITravelPlanner:
    """Wraps the Anthropic messages API for conversational travel planning."""

    def __init__(self):
        self.traffic_pred = TrafficPredictor()
        self.weather_pred = WeatherPredictor()
        self.surge_pred   = SurgePredictor()
        self.recommender  = SmartRecommender()

    def chat(
        self,
        user_message: str,
        history: list[dict],
        context: dict,
    ) -> dict:
        """
        Send a message to Claude and return {reply: str, context: dict}.
        `history` is a list of {role, content} dicts (prior turns).
        `context` is a dict of extracted travel info persisted across turns.
        """
        # Build live conditions string to inject
        weather = self.weather_pred.predict()
        traffic = self.traffic_pred.predict(
            source=context.get("source", ""),
            destination=context.get("destination", ""),
        )
        surge = self.surge_pred.predict()

        conditions_note = (
            f"\n\n[LIVE CONDITIONS — inject naturally where relevant: "
            f"Weather: {weather['condition']} ({weather['temp_c']}°C). "
            f"Traffic: {traffic['level']} ({traffic['description']}). "
            f"Surge: {surge['level']} ({surge['multiplier']:.1f}×). "
            f"Today: {datetime.now().strftime('%A, %d %b %Y, %I:%M %p')}]"
        )

        # Build message history for the API
        messages = []
        for h in history:
            if h["role"] in ("user", "assistant"):
                messages.append({"role": h["role"], "content": h["content"]})

        messages.append({"role": "user", "content": user_message})

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 1000,
                    "system": SYSTEM_PROMPT + conditions_note,
                    "messages": messages,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            reply = "".join(
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text"
            )
        except requests.exceptions.Timeout:
            reply = "⏱️ The AI is taking too long to respond. Please try again."
        except requests.exceptions.RequestException as e:
            # Graceful fallback — generate a rule-based plan
            reply = self._fallback_plan(user_message, context, weather, traffic, surge)

        # Update context with any newly mentioned entities
        updated_context = self._update_context(user_message, context)

        # Format reply for HTML display
        html_reply = self._to_html(reply)

        return {"reply": html_reply, "context": updated_context}

    # ── Fallback rule-based plan (no API) ─────────────────────────────────────
    def _fallback_plan(
        self, message: str, context: dict,
        weather: dict, traffic: dict, surge: dict
    ) -> str:
        source = context.get("source") or "your location"
        dest   = context.get("destination") or "your destination"
        people = context.get("num_people", 1)
        budget = context.get("budget", 500)
        luggage= context.get("luggage", False)

        options = get_ride_options(
            source=source,
            destination=dest,
            departure_time=datetime.now().strftime("%H:%M"),
            num_people=people,
            luggage=luggage,
            budget=budget,
            vehicle_pref="No Preference",
            priority="Balanced",
            traffic=traffic,
            weather=weather,
            surge=surge,
        )
        ranked = self.recommender.rank(
            options=options,
            num_people=people,
            luggage=luggage,
            budget=budget,
            vehicle_pref="No Preference",
            priority="Balanced",
            traffic=traffic,
            weather=weather,
            surge=surge,
        )

        if not ranked:
            return (
                "I couldn't find ride options for that route right now. "
                "Could you share more details about your trip?"
            )

        best = ranked[0]
        alt  = ranked[1] if len(ranked) > 1 else None

        lines = [
            f"🗺️ **{source} → {dest}**",
            "",
            f"🏆 **Best Pick: {best['icon']} {best['vehicle']}**",
            f"💰 Fare: ₹{best['fare']:.0f}  |  ⏱️ ETA: ~{best['eta']} min",
        ]
        if people > 1:
            lines.append(f"👥 Split fare: ₹{best['fare']/people:.0f}/person")

        lines += [
            f"📝 {best['reason']}",
            "",
            f"🌤️ Weather: {weather['condition']} · 🚦 Traffic: {traffic['level']} · ⚡ Surge: {surge['multiplier']:.1f}×",
        ]

        if alt:
            lines += [
                "",
                f"🔄 **Alternative: {alt['icon']} {alt['vehicle']}** — ₹{alt['fare']:.0f}, {alt['eta']} min",
            ]

        lines += ["", f"🎯 AI Confidence: {best['score']}%"]
        return "\n".join(lines)

    # ── Context extraction (simple keyword parse) ─────────────────────────────
    def _update_context(self, message: str, context: dict) -> dict:
        ctx = dict(context)
        msg = message.lower()

        # People count
        m = re.search(r"(\d+)\s+(friend|person|people|pax|passenger|of us)", msg)
        if m:
            ctx["num_people"] = int(m.group(1))

        # Budget
        m = re.search(r"₹\s*(\d+)|under\s+(\d+)|budget\s+(\d+)", msg)
        if m:
            ctx["budget"] = int(next(x for x in m.groups() if x))

        # Luggage
        if any(w in msg for w in ("luggage", "suitcase", "bag", "baggage")):
            ctx["luggage"] = True

        return ctx

    # ── Markdown → HTML ────────────────────────────────────────────────────────
    def _to_html(self, text: str) -> str:
        """Convert simple markdown to HTML for chat display."""
        lines = text.split("\n")
        html_lines = []
        for line in lines:
            # Bold
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            # Italic
            line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
            if line.strip():
                html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append("<br>")
        return "".join(html_lines)
