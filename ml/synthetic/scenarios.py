"""Named simulation scenarios (training days, stress tests, the demo)."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from ml.synthetic.simulator import SimParams

ZONES_MAIN = ["ruins_st_paul", "jesus_square", "rua_sao_paulo", "st_dominic", "senado_square", "almeida_ribeiro"]
DAY_TYPES = ["weekday", "weekday", "weekend", "golden_week", "golden_week"]


def local(day: datetime, hour: int, minute: int = 0) -> datetime:
    """Macau local time (UTC+8) -> UTC datetime."""
    return (day.replace(hour=hour, minute=minute, second=0, microsecond=0) - timedelta(hours=8)).astimezone(timezone.utc)


def training_days(n_days: int = 14, seed: int = 7, sensor_interval_s: int = 20) -> list[SimParams]:
    """A mix of weekdays, weekends and Golden-Week days with random surges,
    event endings, rain spells and occasional route closures."""
    rng = random.Random(seed)
    params: list[SimParams] = []
    base = datetime(2026, 9, 21, tzinfo=timezone.utc)
    for i in range(n_days):
        day = base + timedelta(days=i)
        # Golden Week: 1-7 October
        if 1 <= (day + timedelta(days=0)).day <= 7 and day.month == 10:
            day_type = "golden_week"
        elif day.weekday() >= 5:
            day_type = "weekend"
        else:
            day_type = "weekday"
        p = SimParams(
            seed=seed * 1000 + i,
            start_time=local(day, 8, 0),
            duration_min=14 * 60,
            sensor_interval_s=sensor_interval_s,
            day_type=day_type,
            arrival_scale=rng.uniform(0.8, 1.25),
            noise_sd=0.10,
        )
        for _ in range(rng.randint(0, 3)):
            p.surges.append({"time_min": rng.randint(60, 780), "zone_id": rng.choice(["almeida_ribeiro", "ruins_st_paul"]), "people": rng.randint(150, 500)})
        for _ in range(rng.randint(0, 2)):
            p.event_ends.append({"time_min": rng.randint(120, 760), "zone_id": rng.choice(["senado_square", "st_dominic", "jesus_square"]), "people": rng.randint(300, 900)})
        if rng.random() < 0.35:
            start = rng.randint(60, 700)
            p.rain.append({"start_min": start, "end_min": start + rng.randint(30, 120)})
        if rng.random() < 0.2:
            start = rng.randint(120, 700)
            p.closures.append({"edge_id": rng.choice(["e_ruasp_dominic", "e_dominic_senado", "e_ruins_jesus"]), "start_min": start, "end_min": start + rng.randint(20, 60)})
        params.append(p)
    return params


def golden_week_demo(start_utc: datetime | None = None, sensor_interval_s: int = 5, seed: int = 2026) -> SimParams:
    """Polished demo: Golden-Week afternoon, southbound flow. A performance in
    St. Dominic's Square ends ~14:04 local and tour groups surge in from
    Almeida Ribeiro at ~14:06; Senado Square is forecast to become CRITICAL."""
    day = datetime(2026, 10, 3, tzinfo=timezone.utc)
    start = start_utc or local(day, 13, 45)
    p = SimParams(
        seed=seed,
        start_time=start,
        duration_min=120,
        sensor_interval_s=sensor_interval_s,
        day_type="golden_week",
        arrival_scale=1.1,
        warmup_min=90,
        initial_fill=0.15,
    )
    p.event_ends.append({"time_min": 19, "zone_id": "st_dominic", "people": 900})
    p.surges.append({"time_min": 21, "zone_id": "almeida_ribeiro", "people": 420})
    p.surges.append({"time_min": 27, "zone_id": "almeida_ribeiro", "people": 300})
    return p


def stress_rain_closure(seed: int = 99, sensor_interval_s: int = 20) -> SimParams:
    """Out-of-distribution style day: long heavy rain + route closure + surge."""
    day = datetime(2026, 10, 6, tzinfo=timezone.utc)
    p = SimParams(seed=seed, start_time=local(day, 8, 0), duration_min=14 * 60, sensor_interval_s=sensor_interval_s, day_type="golden_week", arrival_scale=1.3)
    p.rain.append({"start_min": 240, "end_min": 520})
    p.closures.append({"edge_id": "e_dominic_senado", "start_min": 380, "end_min": 470})
    p.surges.append({"time_min": 400, "zone_id": "almeida_ribeiro", "people": 600})
    p.event_ends.append({"time_min": 410, "zone_id": "senado_square", "people": 900})
    return p


SCENARIOS = {
    "golden_week_demo": golden_week_demo,
    "stress_rain_closure": stress_rain_closure,
}
