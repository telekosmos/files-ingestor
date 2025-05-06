from __future__ import annotations

from files_ingestor.application.commands.ingest_pdf import (
    IngestCloudStorageCmd,
    IngestFolderCmd,
    IngestPDFCmd,
)
from files_ingestor.application.handlers.handler import Handler
from files_ingestor.domain.services.file_processor_service import FileProcessorService


class IngestionHandler(Handler):
    """Handles the file ingestion command"""

    def __init__(self, ingestor_service: FileProcessorService):
        self.ingestor = ingestor_service

    def handle(self, cmd: IngestPDFCmd | IngestFolderCmd | IngestCloudStorageCmd):
        """Handles the query and invokes the domain service."""
        return self.ingestor.process(cmd)
