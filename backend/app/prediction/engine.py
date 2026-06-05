from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class TeamSnapshot:
    name: str
    elo: float
    fifa_rank: int
    squad_quality: float
    recent_form_points: float
    goals_for_last5: float
    goals_against_last5: float
    injuries: int = 0
    suspensions: int = 0
    tournament_experience: float = 50.0
    host: bool = False


@dataclass(frozen=True)
class MatchPrediction:
    team_a: str
    team_b: str
    team_a_win: float
    draw: float
    team_b_win: float
    confidence: str
    top_factors: list[str] = field(default_factory=list)
    model_version: str = "v0_rule_based"
    data_freshness: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict[str, object]:
        return {
            "team_a": self.team_a,
            "team_b": self.team_b,
            "team_a_win": self.team_a_win,
            "draw": self.draw,
            "team_b_win": self.team_b_win,
            "confidence": self.confidence,
            "top_factors": self.top_factors,
            "model_version": self.model_version,
            "data_freshness": self.data_freshness,
        }


class PredictionEngine:
    """Small, explainable baseline model.

    The point of this first model is not to be perfect. It gives us a stable
    benchmark target and a transparent set of weights we can improve later.
    """

    model_version = "v0_rule_based"

    def predict(self, team_a: TeamSnapshot, team_b: TeamSnapshot) -> MatchPrediction:
        score_a = self._team_score(team_a)
        score_b = self._team_score(team_b)
        diff = score_a - score_b

        draw = self._draw_probability(diff)
        team_a_non_draw = self._logistic(diff / 12.0)
        remaining = 1.0 - draw

        team_a_win = remaining * team_a_non_draw
        team_b_win = remaining * (1.0 - team_a_non_draw)

        team_a_win, draw, team_b_win = self._normalize(team_a_win, draw, team_b_win)

        return MatchPrediction(
            team_a=team_a.name,
            team_b=team_b.name,
            team_a_win=round(team_a_win, 4),
            draw=round(draw, 4),
            team_b_win=round(team_b_win, 4),
            confidence=self._confidence(abs(diff), team_a, team_b),
            top_factors=self._top_factors(team_a, team_b, score_a, score_b),
            model_version=self.model_version,
        )

    def _team_score(self, team: TeamSnapshot) -> float:
        elo_score = self._clamp((team.elo - 1500.0) / 8.0, 0.0, 100.0)
        rank_score = self._clamp(100.0 - ((team.fifa_rank - 1) * 1.2), 0.0, 100.0)
        form_score = self._clamp((team.recent_form_points / 15.0) * 100.0, 0.0, 100.0)
        attack_score = self._clamp((team.goals_for_last5 / 15.0) * 100.0, 0.0, 100.0)
        defense_score = self._clamp(100.0 - ((team.goals_against_last5 / 15.0) * 100.0), 0.0, 100.0)
        availability_penalty = (team.injuries * 2.0) + (team.suspensions * 2.5)
        host_bonus = 4.0 if team.host else 0.0

        return (
            (elo_score * 0.24)
            + (rank_score * 0.15)
            + (team.squad_quality * 0.20)
            + (form_score * 0.16)
            + (attack_score * 0.10)
            + (defense_score * 0.08)
            + (team.tournament_experience * 0.07)
            + host_bonus
            - availability_penalty
        )

    def _top_factors(
        self,
        team_a: TeamSnapshot,
        team_b: TeamSnapshot,
        score_a: float,
        score_b: float,
    ) -> list[str]:
        factors: list[str] = []

        if abs(score_a - score_b) < 3:
            factors.append("The model sees this as a very close matchup.")
        else:
            leader = team_a if score_a > score_b else team_b
            factors.append(f"{leader.name} has the stronger overall pre-match profile.")

        if abs(team_a.elo - team_b.elo) >= 40:
            leader = team_a if team_a.elo > team_b.elo else team_b
            factors.append(f"{leader.name} has the stronger Elo rating.")

        if abs(team_a.recent_form_points - team_b.recent_form_points) >= 3:
            leader = team_a if team_a.recent_form_points > team_b.recent_form_points else team_b
            factors.append(f"{leader.name} has better recent form over the last five matches.")

        availability_a = team_a.injuries + team_a.suspensions
        availability_b = team_b.injuries + team_b.suspensions
        if abs(availability_a - availability_b) >= 2:
            healthier = team_a if availability_a < availability_b else team_b
            factors.append(f"{healthier.name} has a cleaner availability picture.")

        if team_a.host != team_b.host:
            host = team_a if team_a.host else team_b
            factors.append(f"{host.name} receives a host or location advantage.")

        return factors[:4]

    def _draw_probability(self, diff: float) -> float:
        return self._clamp(0.285 - (abs(diff) * 0.004), 0.16, 0.31)

    def _confidence(self, score_gap: float, team_a: TeamSnapshot, team_b: TeamSnapshot) -> str:
        missing_like = sum(
            value <= 0
            for team in (team_a, team_b)
            for value in (
                team.elo,
                team.fifa_rank,
                team.squad_quality,
                team.recent_form_points,
            )
        )
        if missing_like:
            return "low"
        if score_gap >= 12:
            return "high"
        if score_gap >= 5:
            return "medium"
        return "low"

    @staticmethod
    def _logistic(value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    @staticmethod
    def _normalize(team_a_win: float, draw: float, team_b_win: float) -> tuple[float, float, float]:
        total = team_a_win + draw + team_b_win
        if total <= 0:
            return 0.33, 0.34, 0.33
        return team_a_win / total, draw / total, team_b_win / total

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))
