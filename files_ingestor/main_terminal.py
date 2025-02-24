import logging

from files_ingestor.adapters.default_logger import DefaultLoggerAdapter
from files_ingestor.adapters.repositories.file_reader import FileReaderAdapter
from files_ingestor.adapters.terminal import TerminalAdapter
from files_ingestor.application.handlers.count_file_handler import CountFileHandler
from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.domain.services.file_processor_service import FileProcessorService


def main():
    logger: LoggerPort = DefaultLoggerAdapter(log_level=logging.DEBUG) 
    # Instantiate the FileReaderAdapter (driven adapter)
    file_reader_adapter = FileReaderAdapter()

    # Instantiate the FileProcessorService (business logic)
    file_processor_service = FileProcessorService(logger, file_reader_adapter)

    # Instantiate the Query Handler
    count_file_handler = CountFileHandler(file_processor_service)

    terminal_adapter = TerminalAdapter(logger, count_file_handler)
    terminal_adapter.run()

if __name__ == "__main__":
    main()
