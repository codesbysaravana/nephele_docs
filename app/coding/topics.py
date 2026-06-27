"""Topic–difficulty mapping and skill-to-topic recommendation logic.

Provides the canonical mapping of which difficulty levels are available
for each coding topic, and a heuristic that recommends topics based on
a candidate's declared skill set.
"""

from typing import Dict, List

from app.models.coding_models import CodingDifficulty, CodingTopic

# ── Every topic supports all three difficulty tiers by default. ──────
TOPIC_DIFFICULTY_MAP: Dict[CodingTopic, List[CodingDifficulty]] = {
    CodingTopic.ARRAYS: [CodingDifficulty.EASY, CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.STRINGS: [CodingDifficulty.EASY, CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.LINKED_LISTS: [CodingDifficulty.EASY, CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.STACKS: [CodingDifficulty.EASY, CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.QUEUES: [CodingDifficulty.EASY, CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.HASH_MAPS: [CodingDifficulty.EASY, CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.TREES: [CodingDifficulty.EASY, CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.BST: [CodingDifficulty.EASY, CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.GRAPHS: [CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.HEAPS: [CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.GREEDY: [CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
    CodingTopic.DYNAMIC_PROGRAMMING: [CodingDifficulty.MEDIUM, CodingDifficulty.HARD],
}


# ── Skill-keyword → topic mapping (case-insensitive matching) ────────
_SKILL_TOPIC_MAP: Dict[str, List[CodingTopic]] = {
    # General-purpose / scripting languages → fundamentals
    "python": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.HASH_MAPS, CodingTopic.DYNAMIC_PROGRAMMING],
    "java": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.LINKED_LISTS, CodingTopic.TREES, CodingTopic.DYNAMIC_PROGRAMMING],
    "c++": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.STACKS, CodingTopic.GRAPHS, CodingTopic.DYNAMIC_PROGRAMMING],
    "c": [CodingTopic.ARRAYS, CodingTopic.LINKED_LISTS, CodingTopic.STACKS, CodingTopic.QUEUES],
    "javascript": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.HASH_MAPS, CodingTopic.STACKS],
    "typescript": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.HASH_MAPS, CodingTopic.STACKS],
    "go": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.HASH_MAPS, CodingTopic.GRAPHS],
    "rust": [CodingTopic.ARRAYS, CodingTopic.LINKED_LISTS, CodingTopic.TREES, CodingTopic.GRAPHS],

    # Database / storage
    "sql": [CodingTopic.HASH_MAPS, CodingTopic.TREES, CodingTopic.BST],
    "database": [CodingTopic.HASH_MAPS, CodingTopic.TREES, CodingTopic.BST],
    "mongodb": [CodingTopic.HASH_MAPS, CodingTopic.TREES],
    "redis": [CodingTopic.HASH_MAPS, CodingTopic.QUEUES, CodingTopic.HEAPS],
    "postgresql": [CodingTopic.HASH_MAPS, CodingTopic.TREES, CodingTopic.BST],

    # Data-engineering / ML
    "machine learning": [CodingTopic.ARRAYS, CodingTopic.DYNAMIC_PROGRAMMING, CodingTopic.GRAPHS, CodingTopic.GREEDY],
    "data science": [CodingTopic.ARRAYS, CodingTopic.HASH_MAPS, CodingTopic.DYNAMIC_PROGRAMMING],
    "data structures": [CodingTopic.LINKED_LISTS, CodingTopic.TREES, CodingTopic.BST, CodingTopic.GRAPHS, CodingTopic.HEAPS],
    "algorithms": [CodingTopic.GREEDY, CodingTopic.DYNAMIC_PROGRAMMING, CodingTopic.GRAPHS],

    # Web / distributed
    "react": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.STACKS],
    "node": [CodingTopic.ARRAYS, CodingTopic.QUEUES, CodingTopic.HASH_MAPS],
    "django": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.HASH_MAPS],
    "flask": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.HASH_MAPS],
    "fastapi": [CodingTopic.ARRAYS, CodingTopic.STRINGS, CodingTopic.HASH_MAPS],
    "microservices": [CodingTopic.QUEUES, CodingTopic.GRAPHS, CodingTopic.HASH_MAPS],
    "distributed systems": [CodingTopic.GRAPHS, CodingTopic.QUEUES, CodingTopic.HASH_MAPS],
    "system design": [CodingTopic.GRAPHS, CodingTopic.QUEUES, CodingTopic.HASH_MAPS, CodingTopic.HEAPS],
}

# Default topics when no skill matches
_DEFAULT_TOPICS: List[CodingTopic] = [
    CodingTopic.ARRAYS,
    CodingTopic.STRINGS,
    CodingTopic.HASH_MAPS,
]


def get_recommended_topics(skills: List[str]) -> List[CodingTopic]:
    """Map candidate skills to relevant coding topics.

    Performs case-insensitive substring matching of each skill against
    the internal ``_SKILL_TOPIC_MAP``.  Deduplicates and preserves
    insertion order.  Falls back to ``_DEFAULT_TOPICS`` when no skills
    match.

    Parameters
    ----------
    skills:
        The candidate's self-declared skills / technologies.

    Returns
    -------
    List[CodingTopic]
        An ordered list of recommended topics (no duplicates).
    """

    if not skills:
        return list(_DEFAULT_TOPICS)

    seen: set[CodingTopic] = set()
    recommended: List[CodingTopic] = []

    for skill in skills:
        normalised = skill.strip().lower()
        for keyword, topics in _SKILL_TOPIC_MAP.items():
            # Substring match in either direction so "PostgreSQL" matches
            # the "postgresql" key, and "python3" matches "python".
            if keyword in normalised or normalised in keyword:
                for topic in topics:
                    if topic not in seen:
                        seen.add(topic)
                        recommended.append(topic)

    return recommended if recommended else list(_DEFAULT_TOPICS)
