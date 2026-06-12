from __future__ import annotations

import re
from datetime import date
from typing import Any

from backend.app.data.cache import get_cached_matches, get_match_cache_status
from backend.app.data.mock_data import MATCHES, STANDINGS, TEAM_SNAPSHOTS
from backend.app.prediction.engine import PredictionEngine, TeamSnapshot


TEAM_ALIASES = {
    "america": "usa",
    "korearepublic": "southkorea",
    "republicofkorea": "southkorea",
    "turkey": "turkiye",
    "unitedstates": "usa",
    "unitedstatesofamerica": "usa",
    "us": "usa",
    "usmnt": "usa",
}


class FootballTools:
    def __init__(self, prediction_engine: PredictionEngine | None = None) -> None:
        self.prediction_engine = prediction_engine or PredictionEngine()

    def list_teams(self) -> list[str]:
        return sorted(team.name for team in TEAM_SNAPSHOTS.values())

    def get_team_profile(self, team_name: str) -> dict[str, Any]:
        team = self._find_team(team_name)
        return {
            "name": team.name,
            "elo": team.elo,
            "fifa_rank": team.fifa_rank,
            "squad_quality": team.squad_quality,
            "recent_form_points": team.recent_form_points,
            "goals_for_last5": team.goals_for_last5,
            "goals_against_last5": team.goals_against_last5,
            "injuries": team.injuries,
            "suspensions": team.suspensions,
            "tournament_experience": team.tournament_experience,
            "host": team.host,
        }

    def get_match_schedule(self, team_name: str | None = None) -> list[dict[str, Any]]:
        matches = self._matches()
        if not team_name:
            return matches

        normalized = self._normalize(team_name)
        return [
            match
            for match in matches
            if normalized in (self._normalize(match["team_a"]), self._normalize(match["team_b"]))
        ]

    def get_next_matches(self, reference_date: str | date | None = None) -> list[dict[str, Any]]:
        target_date = self._coerce_date(reference_date) or date.today()
        upcoming = [
            match
            for match in self._matches()
            if (match_date := self._coerce_date(match.get("date"))) is not None and match_date >= target_date
        ]
        if not upcoming:
            return []

        upcoming.sort(key=lambda match: str(match.get("date") or ""))
        next_date = upcoming[0].get("date")
        return [match for match in upcoming if match.get("date") == next_date]

    def get_group_standings(self, group: str | None = None) -> list[dict[str, Any]]:
        if not group:
            return STANDINGS
        normalized_group = group.strip().upper()
        return [standing for standing in STANDINGS if standing["group"] == normalized_group]

    def get_match_result(self, team_a: str, team_b: str) -> dict[str, Any]:
        normalized_a = self._normalize(team_a)
        normalized_b = self._normalize(team_b)
        for match in self._matches():
            match_teams = {self._normalize(match["team_a"]), self._normalize(match["team_b"])}
            if {normalized_a, normalized_b} == match_teams:
                return match
        return {
            "team_a": team_a,
            "team_b": team_b,
            "status": "not_found",
            "score": None,
        }

    def predict_match(self, team_a: str, team_b: str) -> dict[str, Any]:
        snapshot_a = self._find_team(team_a)
        snapshot_b = self._find_team(team_b)
        return self.prediction_engine.predict(snapshot_a, snapshot_b).as_dict()

    def get_data_freshness(self) -> dict[str, Any]:
        return get_match_cache_status()

    def extract_matchup(self, message: str) -> tuple[str, str] | None:
        cleaned = re.sub(r"^/(predict|compare)\s+", "", message.strip(), flags=re.IGNORECASE)
        mentioned = self._mentioned_teams(cleaned)
        if len(mentioned) >= 2:
            return mentioned[0], mentioned[1]

        match = re.search(r"(.+?)\s+(?:vs\.?|v\.?|against)\s+(.+)", cleaned, flags=re.IGNORECASE)
        if match:
            return self._clean_team(match.group(1)), self._clean_team(match.group(2))

        return None

    def _find_team(self, team_name: str) -> TeamSnapshot:
        normalized = self._normalize(team_name)
        normalized = TEAM_ALIASES.get(normalized, normalized)
        if normalized in TEAM_SNAPSHOTS:
            return TEAM_SNAPSHOTS[normalized]

        for key, snapshot in TEAM_SNAPSHOTS.items():
            if normalized == self._normalize(snapshot.name) or normalized in key:
                return snapshot

        available = ", ".join(self.list_teams())
        raise ValueError(f"Unknown team '{team_name}'. Available teams: {available}")

    def _matches(self) -> list[dict[str, Any]]:
        return get_cached_matches() or MATCHES

    @staticmethod
    def _coerce_date(value: object) -> date | None:
        if isinstance(value, date):
            return value
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None

    def _mentioned_teams(self, value: str) -> list[str]:
        normalized_value = self._normalize(value)
        matches: list[tuple[int, str]] = []
        for key, snapshot in TEAM_SNAPSHOTS.items():
            candidates = {key, self._normalize(snapshot.name)}
            positions = [normalized_value.find(candidate) for candidate in candidates if candidate in normalized_value]
            if positions:
                matches.append((min(position for position in positions if position >= 0), snapshot.name))

        matches.sort(key=lambda item: item[0])
        return [team for _, team in matches]

    @staticmethod
    def _clean_team(value: str) -> str:
        value = re.sub(r"^(predict|compare|chance of|chances for)\s+", "", value.strip(), flags=re.IGNORECASE)
        value = re.sub(r"[?.!]+$", "", value)
        return value.strip()

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())
