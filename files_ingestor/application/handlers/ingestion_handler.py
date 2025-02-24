from __future__ import annotations

from files_ingestor.application.commands.ingest_pdf import IngestPDFCmd
from files_ingestor.domain.services.file_processor_service import FileProcessorService


class IngestionHandler:
    """Handles the file-counting query."""

    def __init__(self, ingestor_service: FileProcessorService):
        self.ingestor = ingestor_service

    def handle(self, cmd: 'IngestPDFCmd') -> str:  # noqa: UP037
        """Handles the query and invokes the domain service."""
        return self.ingestor.ingest_pdf(cmd.filepath)
