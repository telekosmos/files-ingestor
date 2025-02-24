from __future__ import annotations


class IngestPDFCmd:
    """Encapsulates input parameters for counting file operations."""

    def __init__(self, filename: str):
        self.filepath: str = filename
