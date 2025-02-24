from __future__ import annotations


class QuestionQuery:
    """Encapsulates input parameters for counting file operations."""

    def __init__(self, query: str):
        self.query = query
