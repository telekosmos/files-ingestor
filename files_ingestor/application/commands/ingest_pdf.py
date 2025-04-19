from __future__ import annotations

from . import Command


class IngestPDFCmd(Command):
    """Encapsulates input parameters for file ingestion operations."""

    def __init__(self, filename: str):
        self.file_name: str = filename

    def name(self):
        return "Ingest PDF Command"


class IngestFolderCmd(Command):
    """Encapsulates input parameter (path) for folder ingestion operations."""

    def __init__(self, folder_path: str):
        self.folder_path: str = folder_path

    def name(self):
        return "Ingest Folder Command"
