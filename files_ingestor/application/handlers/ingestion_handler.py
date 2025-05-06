from __future__ import annotations

from collections.abc import Sequence

from llama_index.core.schema import BaseNode

from files_ingestor.application.commands import Command
from files_ingestor.application.handlers.handler import Handler
from files_ingestor.domain.services.file_processor_service import FileProcessorService


class IngestionHandler(Handler):
    """Handles the file ingestion command"""

    def __init__(self, ingestor_service: FileProcessorService):
        self.ingestor = ingestor_service

    def handle(self, cmd: Command) -> Sequence[BaseNode] | int:
        """Handles the query and invokes the domain service."""
        return self.ingestor.process(cmd)
