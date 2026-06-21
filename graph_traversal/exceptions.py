"""Custom exceptions for graph traversal logic."""

class GraphConceptNotFound(Exception):
    """Raised when a concept cannot be found inside the active knowledge graph."""
    pass

class TraversalLoopDetected(Exception):
    """Raised when an infinite loop is detected in the traversal path."""
    pass
