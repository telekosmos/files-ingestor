from __future__ import annotations

from files_ingestor.application.commands.ingest_pdf import IngestPDFCmd, IngestFolderCmd
from files_ingestor.application.handlers.handler import Handler
from files_ingestor.domain.services.file_processor_service import FileProcessorService


class IngestionHandler(Handler):
    """Handles the file ingestoin command"""

    def __init__(self, ingestor_service: FileProcessorService):
        self.ingestor = ingestor_service

    def handle(self, cmd: IngestPDFCmd | IngestFolderCmd):
        """Handles the query and invokes the domain service."""
        match cmd:
            case IngestPDFCmd():
                return self.ingestor.ingest_pdf(cmd.filepath)
            case IngestFolderCmd():
                return self.ingestor.ingest_folder(cmd.folder_path)


class IngestionFolderHandler(Handler):
    """Handles the ingestion of files in folder"""

    def __init__(self, ingestor_service: FileProcessorService):
        self.ingestor = ingestor_service

    def handle(self, cmd: IngestFolderCmd):
        """Handles the query and invokes the domain service."""
        return self.ingestor.ingest_folder(cmd.folder_path)
