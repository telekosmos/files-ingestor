import logging

from files_ingestor.adapters.config import ConfigConfig
from files_ingestor.adapters.default_logger import DefaultLoggerAdapter
from files_ingestor.adapters.embedding_models.ollama import OllamaEmbeddingModel
from files_ingestor.adapters.repositories.file_reader import FileReaderAdapter
from files_ingestor.adapters.terminal import TerminalAdapter
from files_ingestor.application.handlers.count_file_handler import CountFileHandler
from files_ingestor.application.handlers.ingestion_handler import IngestionHandler
from files_ingestor.domain.ports.config import ConfigPort
from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.domain.services.file_processor_service import FileProcessorService


def main():
    print("Starting terminal app...")
    logger: LoggerPort = DefaultLoggerAdapter(log_level=logging.DEBUG)
    config: ConfigPort = ConfigConfig()
    print(f"from config {config.get('llm.anthropic.name')}")
    # Instantiate the FileReaderAdapter (driven adapter)
    file_reader_adapter = FileReaderAdapter()
    embedding_model: EmbeddingModelPort = OllamaEmbeddingModel()

    # Instantiate the FileProcessorService (business logic)
    file_processor_service = FileProcessorService(logger, config, None, embedding_model, file_reader_adapter)

    # Instantiate the Query Handler
    # count_file_handler = CountFileHandler(file_processor_service)
    ingestion_handler = IngestionHandler(file_processor_service)

    terminal_adapter = TerminalAdapter(logger, ingestion_handler)
    terminal_adapter.run()


if __name__ == "__main__":
    main()
