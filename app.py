import streamlit as st
import pandas as pd
from datetime import datetime, time
import json
 
from database import init_db, get_ride_history, save_ride, get_profile_stats
from ride_engine import get_ride_options, get_fare_prediction
from recommender import SmartRecommender
from ml_predictor import TrafficPredictor, WeatherPredictor, SurgePredictor
 
st.set_page_config(
    page_title="MoveSmart 2.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
 
:root {
    --bg-primary: #0A0E1A;
    --bg-card: #111827;
    --bg-card-hover: #1a2236;
    --bg-input: #1E293B;
    --border: #1E293B;
    --border-accent: #334155;
    --accent-blue: #3B82F6;
    --accent-cyan: #06B6D4;
    --accent-green: #10B981;
    --accent-amber: #F59E0B;
    --accent-rose: #F43F5E;
    --accent-violet: #8B5CF6;
    --text-primary: #F1F5F9;
    --text-secondary: #94A3B8;
    --text-muted: #475569;
    --radius: 14px;
    --radius-sm: 8px;
    --shadow: 0 4px 24px rgba(0,0,0,0.4);
}
 
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}
[data-testid="stSidebar"] {
    background: #080C18 !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }
 
div[data-testid="stSidebar"] .stButton button {
    width: 100%;
    background: transparent;
    border: none;
    color: var(--text-secondary);
    text-align: left;
    padding: 0.65rem 1rem;
    border-radius: var(--radius-sm);
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.18s ease;
    margin-bottom: 4px;
}
div[data-testid="stSidebar"] .stButton button:hover {
    background: var(--bg-card);
    color: var(--text-primary);
}
 
[data-testid="block-container"] { padding: 1.5rem 2rem; }
 
.ms-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
}
.ms-card-blue   { border-left: 4px solid #3B82F6; }
.ms-card-green  { border-left: 4px solid #10B981; }
.ms-card-amber  { border-left: 4px solid #F59E0B; }
.ms-card-violet { border-left: 4px solid #8B5CF6; }
.ms-card-rose   { border-left: 4px solid #F43F5E; }
 
.ms-hero {
    background: linear-gradient(135deg, #1a2a4a 0%, #111827 100%);
    border: 1px solid #2563EB44;
    border-radius: var(--radius);
    padding: 1.8rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
}
.ms-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #3B82F6, #06B6D4);
}
 
.ms-score-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1E3A5F;
    color: #60A5FA;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}
 
.ms-tag {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 6px;
    margin-top: 4px;
}
.tag-green  { background: #05230f; color: #34D399; border: 1px solid #065f46; }
.tag-amber  { background: #2d1800; color: #FCD34D; border: 1px solid #78350f; }
.tag-blue   { background: #0c1f4a; color: #93C5FD; border: 1px solid #1e3a8a; }
.tag-rose   { background: #2d0505; color: #FDA4AF; border: 1px solid #7f1d1d; }
.tag-violet { background: #1e0d3a; color: #C4B5FD; border: 1px solid #4c1d95; }
.tag-gray   { background: #1e293b; color: #94A3B8; border: 1px solid #334155; }
 
.ms-page-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.03em;
    margin-bottom: 0.3rem;
}
.ms-page-sub {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-bottom: 1.6rem;
}
.ms-section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 1.4rem 0 0.8rem;
}
 
.ms-insight {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.7rem;
}
.ms-insight-icon { font-size: 1.4rem; flex-shrink: 0; }
.ms-insight-text { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5; }
.ms-insight-text strong { color: var(--text-primary); }
 
.ms-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 1.6rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.ms-logo span { color: var(--accent-blue); }
 
.ms-stat {
    text-align: center;
    padding: 1.1rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}
.ms-stat-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
}
.ms-stat-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
 
.ms-msg-user {
    background: #1E3A5F;
    border-radius: 16px 16px 4px 16px;
    padding: 0.8rem 1.1rem;
    margin: 0.5rem 0 0.5rem auto;
    max-width: 76%;
    color: #DBEAFE;
    font-size: 0.93rem;
    line-height: 1.5;
}
.ms-msg-ai {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px 16px 16px 4px;
    padding: 0.9rem 1.1rem;
    max-width: 82%;
    font-size: 0.93rem;
    line-height: 1.6;
    margin-bottom: 0.5rem;
}
.ms-msg-ai p { margin: 0 0 6px; color: var(--text-primary); }
 
hr.ms-div {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.2rem 0;
}
 
.ms-table { border-collapse: collapse; width: 100%; }
.ms-table th {
    background: var(--bg-input);
    color: var(--text-secondary);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.7rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}
.ms-table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.9rem;
    color: var(--text-primary);
}
.ms-table tr:hover td { background: var(--bg-card-hover); }
 
.stTextInput input, .stSelectbox select, .stNumberInput input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-accent) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}
.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #2563EB, #1d4ed8) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.65rem 2rem !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.97rem !important;
}
[data-testid="stForm"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
}
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)
 
# ── Metro station lookup ──────────────────────────────────────────────────────
METRO_STATIONS = {
    "koramangala":    "Jayanagar / Indiranagar (nearest interchange)",
    "indiranagar":    "Indiranagar",
    "whitefield":     "Whitefield (Kadugodi)",
    "airport":        "Kempegowda International Airport (Aeropolis / Devanahalli)",
    "mg road":        "MG Road",
    "majestic":       "Kempegowda (Majestic)",
    "electronic city":"Electronic City",
    "hebbal":         "Nagawara / Hebbal",
    "jayanagar":      "Jayanagar",
    "marathahalli":   "Marathahalli",
    "kr puram":       "K R Puram",
    "yeshwantpur":    "Yeshwantpur",
    "rajajinagar":    "Rajajinagar",
    "mysore road":    "Mysore Road",
    "banashankari":   "Banashankari",
    "jp nagar":       "JP Nagar",
    "hsr":            "Agara / HSR Layout (walk)",
    "btm":            "Jayanagar (walk ~15 min)",
    "sarjapur":       "Carmelaram (walk / feeder)",
    "silk board":     "Silk Board / BTM Layout",
    "forum mall":     "Koramangala / Forum (walk)",
    "ulsoor":         "Halasuru",
    "cubbon park":    "Cubbon Park",
    "vidhana soudha": "Vidhana Soudha",
    "yelahanka":      "Yelahanka",
    "nagawara":       "Nagawara",
    "hennur":         "Hennur",
    "domlur":         "Indiranagar (walk ~12 min)",
}
 
def nearest_metro(place: str) -> str:
    p = place.lower()
    for key, station in METRO_STATIONS.items():
        if key in p:
            return station
    return f"nearest metro to {place} (check Namma Metro app)"
 
# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
 
if "page"         not in st.session_state: st.session_state.page = "smart_ride"
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "chat_context" not in st.session_state: st.session_state.chat_context = {}
if "last_results" not in st.session_state: st.session_state.last_results = None
 
# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="ms-logo">🚀 Move<span>Smart</span></div>', unsafe_allow_html=True)
    pages = {
        "smart_ride":   ("🏠", "Smart Ride"),
        "ai_planner":   ("🤖", "AI Travel Planner"),
        "ride_history": ("📋", "Ride History"),
        "profile":      ("👤", "Profile"),
    }
    for key, (icon, label) in pages.items():
        if st.session_state.page == key:
            st.markdown(
                f'<div style="background:#1E293B;border:1px solid #334155;border-radius:8px;'
                f'padding:0.6rem 1rem;font-size:0.95rem;font-weight:600;color:#F1F5F9;margin-bottom:4px;">'
                f'{icon}  {label}</div>', unsafe_allow_html=True)
        else:
            if st.button(f"{icon}  {label}", key=f"nav_{key}"):
                st.session_state.page = key
                st.rerun()
    st.markdown("<hr class='ms-div'>", unsafe_allow_html=True)
    st.markdown('<div style="color:#475569;font-size:0.75rem;text-align:center;">MoveSmart 2.0 · AI-Powered</div>', unsafe_allow_html=True)
 
page = st.session_state.page
 
# ══════════════════════════════════════════════════════════════
# SMART RIDE PAGE
# ══════════════════════════════════════════════════════════════
if page == "smart_ride":
    st.markdown('<div class="ms-page-title">🏠 Smart Ride</div>', unsafe_allow_html=True)
    st.markdown('<div class="ms-page-sub">Tell us where you\'re going — we\'ll find the smartest ride.</div>', unsafe_allow_html=True)
 
    with st.form("smart_ride_form"):
        c1, c2 = st.columns(2)
        with c1:
            source      = st.text_input("📍 Source", placeholder="e.g. Koramangala")
            num_people  = st.number_input("👥 Number of People", min_value=1, max_value=20, value=1)
            budget      = st.number_input("💰 Budget (₹)", min_value=0, value=300, step=10)
            priority    = st.selectbox("🎯 Priority", ["Balanced","Cheapest","Fastest","Comfort","Eco Friendly"])
        with c2:
            destination  = st.text_input("🏁 Destination", placeholder="e.g. MG Road")
            departure_time = st.time_input("⏰ Departure Time", value=time(datetime.now().hour, datetime.now().minute))
            luggage      = st.radio("🧳 Luggage", ["No","Yes"], horizontal=True)
            vehicle_pref = st.selectbox("🚗 Preferred Vehicle", ["No Preference","Bike","Auto","Cab","Metro","Bus"])
 
        submitted = st.form_submit_button("🔍 Find Smart Ride", type="primary", use_container_width=True)
 
    if submitted:
        if not source.strip() or not destination.strip():
            st.error("Please enter both source and destination.")
        else:
            with st.spinner("Analysing routes, traffic & weather…"):
                traffic = TrafficPredictor().predict(source, destination, departure_time)
                weather = WeatherPredictor().predict()
                surge   = SurgePredictor().predict(departure_time)
 
                options = get_ride_options(
                    source=source, destination=destination,
                    departure_time=str(departure_time),
                    num_people=num_people, luggage=(luggage=="Yes"),
                    budget=budget, vehicle_pref=vehicle_pref,
                    priority=priority, traffic=traffic, weather=weather, surge=surge,
                )
                recommender = SmartRecommender()
                ranked = recommender.rank(
                    options=options, num_people=num_people, luggage=(luggage=="Yes"),
                    budget=budget, vehicle_pref=vehicle_pref, priority=priority,
                    traffic=traffic, weather=weather, surge=surge,
                )
                st.session_state.last_results = {
                    "source": source, "destination": destination,
                    "ranked": ranked, "num_people": num_people,
                    "budget": budget, "traffic": traffic,
                    "weather": weather, "surge": surge,
                    "departure_time": str(departure_time),
                }
 
    if st.session_state.last_results:
        r          = st.session_state.last_results
        ranked     = r["ranked"]
        num_people = r["num_people"]
        budget     = r["budget"]
        traffic    = r["traffic"]
        weather    = r["weather"]
        surge      = r["surge"]
        source     = r["source"]
        destination= r["destination"]
 
        if not ranked:
            st.warning("No rides found. Try adjusting filters.")
        else:
            best = ranked[0]
 
            # ── Conditions bar ────────────────────────────────────────────
            st.markdown("<hr class='ms-div'>", unsafe_allow_html=True)
            cc = st.columns(4)
 
            t_color = "#F43F5E" if traffic["level"]=="Heavy" else "#F59E0B" if traffic["level"]=="Moderate" else "#10B981"
            w_color = "#3B82F6" if weather["condition"]=="Rainy" else "#10B981"
            s_color = "#F43F5E" if surge["multiplier"]>1.4 else "#F59E0B" if surge["multiplier"]>1.1 else "#10B981"
 
            with cc[0]:
                st.markdown(f'<div class="ms-card" style="text-align:center;padding:0.9rem"><div style="font-size:1.4rem">🚦</div><div style="font-size:0.72rem;color:#64748B">Traffic</div><div style="font-weight:700;color:{t_color}">{traffic["level"]}</div></div>', unsafe_allow_html=True)
            with cc[1]:
                st.markdown(f'<div class="ms-card" style="text-align:center;padding:0.9rem"><div style="font-size:1.4rem">🌤️</div><div style="font-size:0.72rem;color:#64748B">Weather</div><div style="font-weight:700;color:{w_color}">{weather["condition"]}</div></div>', unsafe_allow_html=True)
            with cc[2]:
                st.markdown(f'<div class="ms-card" style="text-align:center;padding:0.9rem"><div style="font-size:1.4rem">⚡</div><div style="font-size:0.72rem;color:#64748B">Surge</div><div style="font-weight:700;color:{s_color}">{surge["multiplier"]:.1f}×</div></div>', unsafe_allow_html=True)
            with cc[3]:
                st.markdown(f'<div class="ms-card" style="text-align:center;padding:0.9rem"><div style="font-size:1.4rem">👥</div><div style="font-size:0.72rem;color:#64748B">People</div><div style="font-weight:700;color:#93C5FD">{num_people} pax</div></div>', unsafe_allow_html=True)
 
            # ── Best Overall card ─────────────────────────────────────────
            st.markdown('<div class="ms-section-title">🏆 Best Overall — Most Comfortable</div>', unsafe_allow_html=True)
 
            budget_color = "#F43F5E" if best["fare"] > budget else "#10B981"
            budget_text  = "⚠️ Over budget" if best["fare"] > budget else "✅ Within budget"
 
            # Hero card — NO nested variables, only simple values
            st.markdown(f"""
            <div class="ms-hero">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">
                    <div>
                        <div style="font-size:1.7rem;font-weight:700;margin-bottom:6px">{best['icon']} {best['vehicle']}</div>
                        <div style="font-size:0.9rem;color:#94A3B8;max-width:480px">{best['reason']}</div>
                    </div>
                    <div style="text-align:right">
                        <div class="ms-score-badge">⭐ AI Score {best['score']}/100</div>
                        <div style="font-size:2.2rem;font-weight:700;color:#F1F5F9;margin-top:8px">₹{best['fare']:.0f}</div>
                        <div style="font-size:0.82rem;color:#64748B">{best['eta']} min ETA</div>
                    </div>
                </div>
                <div style="margin-top:1rem;display:flex;flex-wrap:wrap;gap:6px">
                    <span class="ms-tag tag-green">🌱 {best['carbon']:.1f} kg CO₂</span>
                    <span class="ms-tag" style="background:#0a1f0a;color:{budget_color};border:1px solid {budget_color}44">{budget_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
 
            # Metro info rendered separately — never nested inside another f-string
            if best["vehicle"] == "Metro":
                board_station  = nearest_metro(source)
                alight_station = nearest_metro(destination)
                st.markdown(f"""
                <div style="background:#0a1628;border:1px solid #1e3a8a;border-radius:10px;padding:1rem;margin-top:-0.5rem;margin-bottom:1rem">
                    <div style="font-size:0.82rem;color:#60A5FA;font-weight:600;margin-bottom:8px">🚇 Metro Journey Details</div>
                    <div style="font-size:0.95rem;color:#DBEAFE;margin-bottom:4px">🟢 <strong>Board at:</strong> {board_station}</div>
                    <div style="font-size:0.95rem;color:#DBEAFE;margin-bottom:8px">🔴 <strong>Alight at:</strong> {alight_station}</div>
                    <div style="font-size:0.78rem;color:#475569">Check Namma Metro app for exact line and interchange details.</div>
                </div>
                """, unsafe_allow_html=True)
 
            # ── Most Comfortable alternative ──────────────────────────────
            comfort_opt = max(ranked, key=lambda x: x["comfort"])
            if comfort_opt["vehicle"] != best["vehicle"]:
                st.markdown('<div class="ms-section-title">🛋️ Most Comfortable Alternative</div>', unsafe_allow_html=True)
 
                st.markdown(f"""
                <div class="ms-card ms-card-violet">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
                        <div>
                            <div style="font-size:1.2rem;font-weight:700">{comfort_opt['icon']} {comfort_opt['vehicle']}</div>
                            <div style="font-size:0.85rem;color:#94A3B8;margin-top:4px">{comfort_opt['reason']}</div>
                        </div>
                        <div style="text-align:right">
                            <div style="font-size:1.6rem;font-weight:700">₹{comfort_opt['fare']:.0f}</div>
                            <div style="font-size:0.8rem;color:#64748B">{comfort_opt['eta']} min</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
 
                # Alt metro info also separate
                if comfort_opt["vehicle"] == "Metro":
                    b = nearest_metro(source)
                    a = nearest_metro(destination)
                    st.markdown(f"""
                    <div style="background:#0a1628;border:1px solid #1e3a8a;border-radius:10px;padding:1rem;margin-top:-0.5rem;margin-bottom:1rem">
                        <div style="font-size:0.82rem;color:#60A5FA;font-weight:600;margin-bottom:8px">🚇 Metro Journey Details</div>
                        <div style="font-size:0.95rem;color:#DBEAFE;margin-bottom:4px">🟢 <strong>Board at:</strong> {b}</div>
                        <div style="font-size:0.95rem;color:#DBEAFE;margin-bottom:8px">🔴 <strong>Alight at:</strong> {a}</div>
                        <div style="font-size:0.78rem;color:#475569">Check Namma Metro app for exact line and interchange details.</div>
                    </div>
                    """, unsafe_allow_html=True)
 
            # ── Smart Insights ────────────────────────────────────────────
            recommender_obj = SmartRecommender()
            insights = recommender_obj.generate_insights(best, budget, num_people, traffic, weather)
            if insights:
                st.markdown('<div class="ms-section-title">💡 Smart Insights</div>', unsafe_allow_html=True)
                for ins in insights:
                    st.markdown(f"""
                    <div class="ms-insight">
                        <div class="ms-insight-icon">{ins['icon']}</div>
                        <div class="ms-insight-text">{ins['text']}</div>
                    </div>""", unsafe_allow_html=True)
 
            # ── Book button ───────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ Book & Save Ride", type="primary"):
                save_ride(
                    source=r["source"], destination=r["destination"],
                    vehicle=best["vehicle"], fare=best["fare"],
                    saved=max(0, budget - best["fare"]),
                    departure_time=r["departure_time"],
                )
                st.success(f"Ride saved! {best['vehicle']} booked for ₹{best['fare']:.0f}.")
                st.session_state.last_results = None
                st.rerun()
 
# ══════════════════════════════════════════════════════════════
# AI TRAVEL PLANNER
# ══════════════════════════════════════════════════════════════
elif page == "ai_planner":
    from ai_planner import AITravelPlanner
 
    st.markdown('<div class="ms-page-title">🤖 AI Travel Planner</div>', unsafe_allow_html=True)
    st.markdown('<div class="ms-page-sub">Describe your travel in plain English — get a complete plan.</div>', unsafe_allow_html=True)
 
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="ms-card" style="text-align:center;padding:2rem">
            <div style="font-size:2.5rem;margin-bottom:8px">🤖</div>
            <div style="font-weight:600;font-size:1.05rem;margin-bottom:6px">Hi! I'm your AI Travel Planner.</div>
            <div style="color:#94A3B8;font-size:0.9rem">Tell me where you need to go — I'll handle the rest.</div>
            <div style="margin-top:1rem;color:#64748B;font-size:0.85rem">
                Try: "I need to reach the airport by 7 PM under ₹400" · "We are 5 friends going to Indiranagar" · "Fastest to MG Road, I have luggage"
            </div>
        </div>""", unsafe_allow_html=True)
 
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div style="display:flex;justify-content:flex-end"><div class="ms-msg-user">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ms-msg-ai">{msg["content"]}</div>', unsafe_allow_html=True)
 
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Message", placeholder="e.g. I need to reach Bangalore Airport before 7 PM under ₹400", label_visibility="collapsed")
        send = st.form_submit_button("Send ➤", type="primary", use_container_width=True)
 
    if send and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        planner = AITravelPlanner()
        response = planner.chat(
            user_message=user_input,
            history=st.session_state.chat_history[:-1],
            context=st.session_state.chat_context,
        )
        st.session_state.chat_context = response.get("context", st.session_state.chat_context)
        st.session_state.chat_history.append({"role": "assistant", "content": response["reply"]})
        st.rerun()
 
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.chat_context = {}
            st.rerun()
 
# ══════════════════════════════════════════════════════════════
# RIDE HISTORY
# ══════════════════════════════════════════════════════════════
elif page == "ride_history":
    st.markdown('<div class="ms-page-title">📋 Ride History</div>', unsafe_allow_html=True)
    st.markdown('<div class="ms-page-sub">All your past trips.</div>', unsafe_allow_html=True)
 
    rides = get_ride_history()
 
    if rides.empty:
        st.markdown("""
        <div class="ms-card" style="text-align:center;padding:2.5rem">
            <div style="font-size:2.5rem">📭</div>
            <div style="font-weight:600;margin-top:8px">No rides yet</div>
            <div style="color:#64748B;font-size:0.9rem;margin-top:4px">Book your first ride from Smart Ride.</div>
        </div>""", unsafe_allow_html=True)
    else:
        m1, m2, m3 = st.columns(3)
        for col, val, lbl, icon in [
            (m1, f"₹{rides['fare'].sum():.0f}",       "Total Spent", "💳"),
            (m2, f"₹{rides['money_saved'].sum():.0f}", "Total Saved", "💚"),
            (m3, str(len(rides)),                      "Trips",       "🗺️"),
        ]:
            with col:
                st.markdown(f'<div class="ms-stat"><div style="font-size:1.3rem">{icon}</div><div class="ms-stat-val">{val}</div><div class="ms-stat-label">{lbl}</div></div>', unsafe_allow_html=True)
 
        st.markdown('<div class="ms-section-title">Recent Trips</div>', unsafe_allow_html=True)
        rows = ""
        for _, row in rides.iterrows():
            dt = str(row["departure_time"])[:16]
            saved_html = f'<span class="ms-tag tag-green">+₹{row["money_saved"]:.0f}</span>' if row["money_saved"] > 0 else "—"
            rows += f"<tr><td>{dt}</td><td>{row['source']}</td><td>{row['destination']}</td><td>{row['vehicle']}</td><td>₹{row['fare']:.0f}</td><td>{saved_html}</td></tr>"
 
        st.markdown(f"""
        <div class="ms-card" style="overflow-x:auto;padding:0">
            <table class="ms-table">
                <thead><tr><th>Date/Time</th><th>From</th><th>To</th><th>Vehicle</th><th>Fare</th><th>Saved</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>""", unsafe_allow_html=True)
 
# ══════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════
elif page == "profile":
    st.markdown('<div class="ms-page-title">👤 Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="ms-page-sub">Your travel stats and insights.</div>', unsafe_allow_html=True)
 
    stats = get_profile_stats()
 
    cols = st.columns(4)
    for col, (icon, val, lbl) in zip(cols, [
        ("🗺️", str(stats["trips_completed"]),       "Trips Completed"),
        ("💰", f"₹{stats['money_saved']:.0f}",      "Total Saved"),
        ("💸", f"₹{stats['avg_fare']:.0f}",         "Average Fare"),
        ("🌱", f"{stats['carbon_saved']:.1f} kg",   "CO₂ Saved"),
    ]):
        with col:
            st.markdown(f'<div class="ms-stat"><div style="font-size:1.4rem">{icon}</div><div class="ms-stat-val">{val}</div><div class="ms-stat-label">{lbl}</div></div>', unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
 
    with c1:
        st.markdown('<div class="ms-section-title">🏅 Favourite Transport</div>', unsafe_allow_html=True)
        if stats["fav_transport"]:
            for i, (veh, cnt) in enumerate(stats["fav_transport"].items()):
                medal = ["🥇","🥈","🥉"][i] if i < 3 else "▪️"
                st.markdown(f'<div class="ms-card" style="display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem"><span>{medal} {veh}</span><span class="ms-tag tag-blue">{cnt} trips</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ms-card" style="color:#64748B;text-align:center">No rides yet</div>', unsafe_allow_html=True)
 
    with c2:
        st.markdown('<div class="ms-section-title">📍 Favourite Routes</div>', unsafe_allow_html=True)
        if stats["fav_routes"]:
            for route, cnt in stats["fav_routes"].items():
                src, _, dst = route.partition(" → ")
                st.markdown(f'<div class="ms-card" style="padding:0.75rem 1rem"><div style="font-size:0.9rem;font-weight:600">{src}</div><div style="font-size:0.78rem;color:#64748B">→ {dst}</div><span class="ms-tag tag-gray" style="margin-top:6px;display:inline-block">{cnt}×</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ms-card" style="color:#64748B;text-align:center">No rides yet</div>', unsafe_allow_html=True)
 
    if stats["carbon_saved"] > 0:
        st.markdown(f"""
        <div class="ms-card ms-card-green" style="text-align:center;padding:1.5rem;margin-top:1rem">
            <div style="font-size:2rem">🌍</div>
            <div style="font-weight:600;margin:6px 0">Eco Champion</div>
            <div style="color:#94A3B8;font-size:0.88rem">You've saved <strong style="color:#34D399">{stats['carbon_saved']:.1f} kg</strong> of CO₂ — equivalent to planting {stats['carbon_saved']/20:.1f} trees.</div>
        </div>""", unsafe_allow_html=True)