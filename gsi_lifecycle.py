"""Pure helpers for active-player GSI lifecycle and cautious economy projections.

Only derives information from standard player-visible GSI sections. No spectator
endpoints, memory access or game-process interaction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def side_from_win(reason: Any) -> str | None:
    if not isinstance(reason, str):
        return None
    reason = reason.lower()
    if reason.startswith('ct_win'):
        return 'CT'
    if reason.startswith('t_win'):
        return 'T'
    return None


def history_loss_level(mp: dict[str, Any], side: str) -> int | None:
    """Reconstruct a loss level only when the *whole* current half is visible.

    Assumes default competitive MR12 loss-aversion configuration. This is an
    estimate, NEVER an authoritative server value. Not used for overtime or
    custom modes/half lengths. An incomplete history gives None.
    """
    if mp.get('mode') != 'competitive' or side not in ('CT', 'T'):
        return None
    current = integer(mp.get('round'))
    wins = mp.get('round_wins')
    if current is None or current < 1 or current > 24 or not isinstance(wins, dict):
        return None
    # Only consider completed rounds; map.round may point to an ongoing round.
    completed = {integer(k): side_from_win(v) for k, v in wins.items()}
    completed = {k: v for k, v in completed.items() if k is not None and k > 0}
    half_start = 1 if current <= 12 else 13
    half_end = min(current - 1, 12) if current <= 12 else current - 1
    # The map.round counter is not entirely consistent across integrations.
    # Where a result exists for the current number, include it only if round
    # phase is clearly over (a live round can still be running).
    if half_end < half_start:
        if half_start == 13:
            # A mid-match join at halftime alone does not prove MR12 settings.
            if any(completed.get(i) is None for i in range(1, 13)):
                return None
        return 1  # default starting half level; still only *estimated*
    for index in range(half_start, half_end + 1):
        if completed.get(index) is None:
            return None
    level = 1  # documented default competitive starting level per half
    for index in range(half_start, half_end + 1):
        winner = completed[index]
        level = max(0, level - 1) if winner == side else min(4, level + 1)
    return level


@dataclass
class EconomyObserver:
    """Keeps direct server observations scoped to a specific round and match.

    A value sent in round N must not be reused as 'direct' in round N+1 if
    the next packet omits it. History inference is a separate lower-confidence
    source. Works when GSI sends partial map updates rather than full snapshots.
    """
    direct: dict[str, tuple[int, int | None]] = field(default_factory=dict)

    def reset(self) -> None:
        self.direct.clear()

    def ingest(self, incoming_map: dict[str, Any], merged_map: dict[str, Any]) -> None:
        rnd = integer(merged_map.get('round'))
        for side, field_name in (('CT', 'team_ct'), ('T', 'team_t')):
            team_data = incoming_map.get(field_name)
            if isinstance(team_data, dict) and 'consecutive_round_losses' in team_data:
                level = integer(team_data['consecutive_round_losses'])
                if level is not None and 0 <= level <= 100:
                    self.direct[side] = (level, rnd)
                else:
                    self.direct.pop(side, None)

    def level(self, mp: dict[str, Any], team: str) -> tuple[int | None, str]:
        current = integer(mp.get('round'))
        observation = self.direct.get(team)
        if observation and observation[1] == current:
            return observation[0], 'gsi'
        derived = history_loss_level(mp, team)
        if derived is not None:
            return derived, 'history'
        return None, 'unknown'


def cash_projection(mp: dict[str, Any], player: dict[str, Any], observer: EconomyObserver | None = None) -> dict[str, Any]:
    """Hypothetical money if next loss; excludes purchases, kill/objective bonuses,
    survival/timeout exceptions and per-server economy modifications.
    """
    ps = player.get('state') if isinstance(player.get('state'), dict) else {}
    money = integer(ps.get('money'))
    team = str(player.get('team') or '').upper()
    empty = {'on_loss': None, 'loss_bonus': None, 'loss_streak_known': False,
             'source': 'unknown', 'confidence': 'unavailable', 'loss_level': None}
    if money is None or not 0 <= money <= 16000 or team not in ('CT', 'T'):
        return empty
    if observer:
        losses, source = observer.level(mp, team)
    else:
        field = 'team_ct' if team == 'CT' else 'team_t'
        direct = (mp.get(field) or {}).get('consecutive_round_losses')
        losses = integer(direct)
        source = 'gsi' if losses is not None and losses >= 0 else 'unknown'
    if losses is None or losses < 0:
        return empty
    # The actual reward can differ by team, rules and objective circumstances.
    bonus = min(3400, 1400 + min(losses, 4) * 500)
    return {'on_loss': min(16000, money + bonus), 'loss_bonus': bonus,
            'loss_streak_known': source == 'gsi', 'source': source,
            'confidence': 'reported' if source == 'gsi' else 'estimated',
            'loss_level': losses}
