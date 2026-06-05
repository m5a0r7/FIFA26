from __future__ import annotations

from backend.app.prediction.engine import TeamSnapshot


TEAM_SNAPSHOTS: dict[str, TeamSnapshot] = {
    "argentina": TeamSnapshot("Argentina", 2110, 2, 91, 12, 10, 5, 1, 0, 95),
    "brazil": TeamSnapshot("Brazil", 2095, 5, 90, 11, 12, 6, 2, 0, 92),
    "france": TeamSnapshot("France", 2130, 3, 93, 12, 11, 4, 1, 1, 94),
    "england": TeamSnapshot("England", 2055, 4, 89, 10, 9, 4, 1, 0, 84),
    "germany": TeamSnapshot("Germany", 1995, 10, 86, 9, 10, 7, 1, 0, 96),
    "portugal": TeamSnapshot("Portugal", 2035, 6, 88, 11, 11, 5, 0, 0, 82),
    "spain": TeamSnapshot("Spain", 2070, 7, 87, 12, 10, 3, 1, 0, 90),
    "morocco": TeamSnapshot("Morocco", 1940, 12, 80, 10, 8, 4, 1, 0, 72),
    "usa": TeamSnapshot("USA", 1885, 14, 78, 8, 7, 5, 1, 0, 58, host=True),
    "canada": TeamSnapshot("Canada", 1810, 35, 72, 7, 8, 8, 2, 0, 42, host=True),
    "mexico": TeamSnapshot("Mexico", 1855, 16, 76, 8, 7, 6, 1, 1, 70, host=True),
}


MATCHES = [
    {
        "date": "2026-06-11",
        "stage": "Group stage",
        "team_a": "Mexico",
        "team_b": "TBD",
        "status": "scheduled",
        "score": None,
        "venue": "Estadio Azteca",
    },
    {
        "date": "2026-06-12",
        "stage": "Group stage",
        "team_a": "USA",
        "team_b": "TBD",
        "status": "scheduled",
        "score": None,
        "venue": "Los Angeles Stadium",
    },
    {
        "date": "2026-06-12",
        "stage": "Group stage",
        "team_a": "Canada",
        "team_b": "TBD",
        "status": "scheduled",
        "score": None,
        "venue": "Toronto Stadium",
    },
]


STANDINGS = [
    {"group": "A", "team": "Mexico", "played": 0, "points": 0, "goal_difference": 0},
    {"group": "A", "team": "TBD", "played": 0, "points": 0, "goal_difference": 0},
    {"group": "B", "team": "Canada", "played": 0, "points": 0, "goal_difference": 0},
    {"group": "B", "team": "TBD", "played": 0, "points": 0, "goal_difference": 0},
    {"group": "D", "team": "USA", "played": 0, "points": 0, "goal_difference": 0},
    {"group": "D", "team": "TBD", "played": 0, "points": 0, "goal_difference": 0},
]
