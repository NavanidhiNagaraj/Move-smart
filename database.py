import sqlite3
import pandas as pd
from datetime import datetime
from collections import Counter

DB_PATH = "movesmart.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            source        TEXT    NOT NULL,
            destination   TEXT    NOT NULL,
            vehicle       TEXT    NOT NULL,
            fare          REAL    NOT NULL,
            money_saved   REAL    DEFAULT 0,
            departure_time TEXT,
            created_at    TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id            INTEGER PRIMARY KEY CHECK (id = 1),
            name          TEXT    DEFAULT 'Traveller',
            home          TEXT    DEFAULT '',
            work          TEXT    DEFAULT '',
            updated_at    TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        INSERT OR IGNORE INTO user_profile (id, name) VALUES (1, 'Traveller')
    """)

    conn.commit()
    conn.close()

def save_ride(source: str, destination: str, vehicle: str, fare: float,
              saved: float = 0, departure_time: str = None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO rides (source, destination, vehicle, fare, money_saved, departure_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (source, destination, vehicle, fare, saved, departure_time or datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_ride_history() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM rides ORDER BY created_at DESC", conn)
    conn.close()
    return df

def get_profile_stats() -> dict:
    rides = get_ride_history()

    if rides.empty:
        return {
            "trips_completed": 0,
            "money_saved": 0.0,
            "avg_fare": 0.0,
            "carbon_saved": 0.0,
            "fav_transport": {},
            "fav_routes": {},
        }

    trips     = len(rides)
    saved     = rides["money_saved"].sum()
    avg_fare  = rides["fare"].mean()
    # Estimate carbon saved vs always taking a cab
    carbon = rides.apply(lambda r: _carbon_saved(r["vehicle"]), axis=1).sum()

    fav_transport = dict(
        Counter(rides["vehicle"].tolist()).most_common(5)
    )
    routes = rides["source"] + " → " + rides["destination"]
    fav_routes = dict(Counter(routes.tolist()).most_common(5))

    return {
        "trips_completed": trips,
        "money_saved":     round(saved, 2),
        "avg_fare":        round(avg_fare, 2),
        "carbon_saved":    round(carbon, 2),
        "fav_transport":   fav_transport,
        "fav_routes":      fav_routes,
    }

def _carbon_saved(vehicle: str) -> float:
    """Estimate kg CO₂ saved vs always using a petrol cab (baseline ~0.21 kg/km, assume 10 km avg)."""
    baselines = {
        "Bike":   0.06,
        "Auto":   0.09,
        "Cab":    0.21,
        "XL Cab": 0.28,
        "Metro":  0.03,
        "Bus":    0.04,
    }
    baseline_cab = 0.21
    vehicle_emission = baselines.get(vehicle, 0.21)
    avg_km = 10
    return max(0, (baseline_cab - vehicle_emission) * avg_km)
