import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .models import Sample, Settings


class Storage:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, config TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS samples (
                id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id),
                timestamp TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS sample_time ON samples(run_id, timestamp);
            CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            PRAGMA user_version=2;
        """)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.history_cache = {}

    def cache_get(self, key):
        row = self.connection.execute("SELECT value FROM cache WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def cache_put(self, key, value):
        with self.connection:
            self.connection.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (key, json.dumps(value, allow_nan=False)))

    def save_settings(self, settings):
        with self.connection:
            self.connection.execute("INSERT OR REPLACE INTO settings VALUES (1, ?)", (settings.model_dump_json(),))

    def runs(self):
        return [{"id": row[0], "config": json.loads(row[1]), "start": row[2], "end": row[3], "count": row[4]}
                for row in self.connection.execute("""SELECT r.id,r.config,MIN(s.timestamp),MAX(s.timestamp),COUNT(s.id)
                    FROM runs r LEFT JOIN samples s ON s.run_id=r.id GROUP BY r.id ORDER BY r.id DESC LIMIT 100""")]

    def settings(self):
        row = self.connection.execute("SELECT value FROM settings WHERE id=1").fetchone()
        if not row:
            return Settings()
        data = json.loads(row[0])
        if "location_set" not in data:
            data["weather_source"] = "internet"
        return Settings.model_validate(data)

    def new_run(self, settings, samples=()):
        self.history_cache.clear()
        with self.connection:
            self.connection.execute("INSERT OR REPLACE INTO settings VALUES (1, ?)", (settings.model_dump_json(),))
            run_id = self.connection.execute("INSERT INTO runs(config) VALUES (?)", (settings.model_dump_json(),)).lastrowid
            self.connection.executemany("INSERT INTO samples(run_id,timestamp,payload) VALUES (?,?,?)",
                                        [(run_id, s.timestamp, s.model_dump_json()) for s in samples])
            return run_id

    def latest_run(self):
        return self.connection.execute("SELECT MAX(id) FROM runs").fetchone()[0]

    def run_exists(self, run_id):
        return self.connection.execute("SELECT 1 FROM runs WHERE id=?", (run_id,)).fetchone() is not None

    def save(self, run_id, samples):
        self.history_cache.clear()
        with self.connection:
            self.connection.executemany("INSERT INTO samples(run_id,timestamp,payload) VALUES (?,?,?)",
                                        [(run_id, s.timestamp, s.model_dump_json()) for s in samples])

    def latest(self, run_id):
        row = self.connection.execute("SELECT payload FROM samples WHERE run_id=? ORDER BY timestamp DESC LIMIT 1", (run_id,)).fetchone()
        return Sample.model_validate_json(row[0]) if row else None

    def rows(self, run_id, since=None):
        query = "SELECT payload FROM samples WHERE run_id=?"
        args = [run_id]
        if since:
            query += " AND timestamp>?"
            args.append(since)
        return [json.loads(row[0]) for row in self.connection.execute(query + " ORDER BY timestamp", args)]

    def history(self, run_id, period):
        cache_key = (run_id, period)
        if cache_key in self.history_cache:
            return self.history_cache[cache_key]
        latest = self.latest(run_id)
        config_row = self.connection.execute("SELECT config FROM runs WHERE id=?", (run_id,)).fetchone()
        config = json.loads(config_row[0]) if config_row else {}
        if latest is None:
            return {"points": [], "totals": {}, "sample_count": 0, "duration_hours": 0, "seeded_count": 0, "run_id": run_id, "config": config}
        days = {"day": 1, "week": 7, "month": 30}.get(period)
        since = (datetime.fromisoformat(latest.timestamp) - timedelta(days=days)).isoformat() if days else None
        rows = self.rows(run_id, since)
        if since:
            boundary = datetime.fromisoformat(since)
            rows = [{**row, "interval_seconds": min(row["interval_seconds"], (datetime.fromisoformat(row["timestamp"]) - boundary).total_seconds())} for row in rows]
        totals = dict(load_kwh=0.0, served_kwh=0.0, pv_kwh=0.0, wind_kwh=0.0, import_kwh=0.0,
                      export_kwh=0.0, unserved_kwh=0.0, curtailed_kwh=0.0,
                      cost_eur=0.0, export_revenue_eur=0.0, reference_eur=0.0, savings_eur=0.0)
        prices = all(row["buy_eur_kwh"] is not None for row in rows)
        for r in rows:
            k = r["interval_seconds"] / 3600000
            for name in ("load", "served", "pv", "wind", "unserved", "curtailed"):
                totals[f"{name}_kwh"] += r[f"{name}_w"] * k
            imported, exported = max(0, r["grid_w"]) * k, max(0, -r["grid_w"]) * k
            totals["import_kwh"] += imported
            totals["export_kwh"] += exported
            if prices:
                rate = r["buy_eur_kwh"] + r["distribution_eur_kwh"]
                fixed = r["fixed_eur_day"] * r["interval_seconds"] / 86400
                revenue = exported * r["sell_eur_kwh"]
                totals["export_revenue_eur"] += revenue
                totals["cost_eur"] += imported * rate - revenue + fixed
                totals["reference_eur"] += r["served_w"] * k * rate + fixed
        totals["savings_eur"] = totals["reference_eur"] - totals["cost_eur"]
        if not prices:
            for key in ("cost_eur", "export_revenue_eur", "reference_eur", "savings_eur"):
                totals[key] = None
        # honey: JSON scan is fine for a PC demo; add SQL rollups when experiments exceed 100k samples.
        stride = max(1, (len(rows) + 287) // 288)
        points = []
        fields = ("load_w", "pv_w", "wind_w", "grid_w", "battery_w", "soc_pct")
        for i in range(0, len(rows), stride):
            group = rows[i:i + stride]
            points.append({"timestamp": group[-1]["timestamp"], **{
                key: sum(r[key] * r["interval_seconds"] for r in group) / sum(r["interval_seconds"] for r in group)
                if all(r[key] is not None for r in group) else None for key in fields}})
        result = {"points": points, "totals": totals, "sample_count": len(rows),
                "duration_hours": sum(r["interval_seconds"] for r in rows) / 3600,
                "seeded_count": sum(r["seeded"] for r in rows), "run_id": run_id, "config": config}
        self.history_cache[cache_key] = result
        return result
