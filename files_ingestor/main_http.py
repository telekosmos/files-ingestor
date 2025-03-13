import logging

from files_ingestor.adapters import qdrant
from files_ingestor.adapters.config import ConfigConfig
from files_ingestor.adapters.default_logger import DefaultLoggerAdapter
from files_ingestor.adapters.embedding_models.ollama import OllamaEmbeddingModel
from files_ingestor.adapters.http import HttpApp, create_http_app
from files_ingestor.adapters.llms.anthropic import AnthropicAdapter
from files_ingestor.adapters.llms.ollama import OllamaAdapter
from files_ingestor.adapters.qdrant import QdrantRepository
from files_ingestor.adapters.repositories.file_reader import FileReaderAdapter
from files_ingestor.application.handlers.count_file_handler import CountFileHandler
from files_ingestor.application.handlers.ingestion_handler import IngestionFolderHandler, IngestionHandler
from files_ingestor.application.handlers.qa_handler import QAHandler
from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.file_reader_port import FileReaderPort
from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort
from files_ingestor.domain.services.file_processor_service import FileProcessorService
from files_ingestor.domain.services.react_agent import ReactAgent

# Instantiate adaptres for cross application concerns
logger: LoggerPort = DefaultLoggerAdapter(log_level=logging.DEBUG)
config: ConfigConfig = ConfigConfig()

# Instantiate infrastructure
file_reader_adapter: FileReaderPort = FileReaderAdapter()
embedding_model: EmbeddingModelPort = OllamaEmbeddingModel()
ollama_model_name: str = config.get("llm.mistralsmall24b.name")
ollama_model_name: str = config.get("llm.gemma2_tools.name")
ollama_llm: OllamaAdapter = OllamaAdapter(ollama_model_name, logger=logger)
anthropic_llm = AnthropicAdapter(config=config, logger=logger)
llm = anthropic_llm
qdrant_url: str = config.get("vectorstore.qdrant.url")
vector_repository: VectorStorePort = QdrantRepository(qdrant_url, logger=logger)

# Instantiate the FileProcessorService (business logic)
file_processor_service = FileProcessorService(logger,
                                              config,
                                              vector_repository,
                                              embedding_model,
                                              file_reader=file_reader_adapter)

logger.info(f"Creating react agent with llm {llm.model_name}")
react_agent = ReactAgent(embedding_model=embedding_model,
                        llm=llm,
                        vector_store=vector_repository,
                        config=config,
                        logger=logger)

# CQS commands and queries handlers
count_file_handler = CountFileHandler(file_processor_service)
ingestion_handler = IngestionHandler(file_processor_service)
ingestion_handler = IngestionFolderHandler(file_processor_service)
qa_handler = QAHandler(react_agent)

# Run HTTP interface
app = create_http_app(logger, query_handler=qa_handler, ingestor_handler=ingestion_handler)

def start():
    import uvicorn
    uvicorn.run("files_ingestor.main_http:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()
