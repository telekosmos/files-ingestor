import logging

from files_ingestor.adapters.config import ConfigConfig
from files_ingestor.adapters.default_logger import DefaultLoggerAdapter
from files_ingestor.adapters.embedding_models.ollama import OllamaEmbeddingModel
from files_ingestor.adapters.qdrant import QdrantRepository
from files_ingestor.adapters.repositories.file_reader import FileReaderAdapter
from files_ingestor.adapters.repositories.local_storage import LocalStorageAdapter
from files_ingestor.adapters.repositories.s3_storage import S3StorageAdapter
from files_ingestor.adapters.terminal import TerminalAdapter
from files_ingestor.application.handlers.ingestion_handler import IngestionHandler
from files_ingestor.domain.ports.cloud_storage_port import CloudStoragePort
from files_ingestor.domain.ports.config import ConfigPort
from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort
from files_ingestor.domain.services.file_processor_service import FileProcessorService


def main() -> None:
    print("Starting terminal app...")
    logger: LoggerPort = DefaultLoggerAdapter(log_level=logging.DEBUG)
    config: ConfigPort = ConfigConfig()
    print(f"from config {config.get('llm.anthropic.name')}")  # type: ignore  # noqa: PGH003
    # Instantiate the FileReaderAdapter (driven adapter)
    file_reader_adapter = FileReaderAdapter()
    s3_storage: CloudStoragePort = S3StorageAdapter(logger=logger, config=config)
    local_storage: CloudStoragePort = LocalStorageAdapter(logger=logger)
    embedding_model: EmbeddingModelPort = OllamaEmbeddingModel()
    qdrant_url: str = config.get("vectorstore.qdrant.url")  # type: ignore  # noqa: PGH003
    vector_repository: VectorStorePort = QdrantRepository(qdrant_url, logger=logger)

    # Instantiate the FileProcessorService (business logic)
    file_processor_service = FileProcessorService(
        logger, config, vector_repository, embedding_model, file_reader_adapter, s3_storage, local_storage
    )

    # Instantiate the Query Handler
    ingestion_handler = IngestionHandler(file_processor_service)

    terminal_adapter = TerminalAdapter(logger, ingestion_handler)
    terminal_adapter.run()


if __name__ == "__main__":
    main()
