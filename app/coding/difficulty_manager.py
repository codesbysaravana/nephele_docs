"""Adaptive difficulty manager for the Nephele coding round.

Adjusts question difficulty up or down based on the candidate's
evaluation scores, implementing a simple step-based escalation
strategy.
"""

import logging

from app.models.coding_models import CodingDifficulty

logger = logging.getLogger(__name__)

# Thresholds
_ESCALATION_THRESHOLD: float = 8.0
_DE_ESCALATION_THRESHOLD: float = 5.0

# Ordered levels for stepping up / down
_DIFFICULTY_LADDER: list[CodingDifficulty] = [
    CodingDifficulty.EASY,
    CodingDifficulty.MEDIUM,
    CodingDifficulty.HARD,
]


class DifficultyManager:
    """Track and adapt coding-round difficulty based on performance.

    Parameters
    ----------
    initial:
        The starting difficulty level.  Defaults to ``EASY``.
    """

    def __init__(self, initial: CodingDifficulty = CodingDifficulty.EASY) -> None:
        self._current: CodingDifficulty = initial
        self._index: int = _DIFFICULTY_LADDER.index(initial)
        logger.info("DifficultyManager initialised at %s", self._current.value)

    # ── public API ───────────────────────────────────────────────────

    @property
    def current_difficulty(self) -> CodingDifficulty:
        """Return the current difficulty level."""
        return self._current

    def adjust(self, score: float) -> CodingDifficulty:
        """Adjust difficulty based on the candidate's overall score.

        Rules
        -----
        * ``score >= 8.0`` → step **up** (Easy→Medium, Medium→Hard).
        * ``score <= 5.0`` → step **down** (Hard→Medium, Medium→Easy).
        * Otherwise → maintain current difficulty.

        Parameters
        ----------
        score:
            The candidate's ``overall`` evaluation score (0–10).

        Returns
        -------
        CodingDifficulty
            The (possibly adjusted) difficulty level.
        """

        previous = self._current

        if score >= _ESCALATION_THRESHOLD and self._index < len(_DIFFICULTY_LADDER) - 1:
            self._index += 1
        elif score <= _DE_ESCALATION_THRESHOLD and self._index > 0:
            self._index -= 1

        self._current = _DIFFICULTY_LADDER[self._index]

        if self._current != previous:
            logger.info(
                "Difficulty adjusted from %s to %s (score=%.1f)",
                previous.value,
                self._current.value,
                score,
            )
        else:
            logger.debug(
                "Difficulty unchanged at %s (score=%.1f)",
                self._current.value,
                score,
            )

        return self._current
