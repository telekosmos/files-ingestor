from __future__ import annotations

from files_ingestor.application.handlers.count_file_handler import CountFileHandler
from files_ingestor.application.queries.count_file_query import CountFileQuery
from files_ingestor.domain.ports.logger_port import LoggerPort

class TerminalAdapter:
    """Adapter for handling terminal input/output."""

    def __init__(self, logger: LoggerPort, query_handler: CountFileHandler):
        self.query_handler = query_handler
        self.logger = logger

    def run(self):
        """Runs the CLI interface."""
        file_name = input("Enter the file name: ")
        operations = input("Enter the operations (words, characters, or both): ").split(",")

        query = CountFileQuery(file_name=file_name, operations=operations)
        result = self.query_handler.handle(query)

        self.logger.info(f"Result: {result}")
