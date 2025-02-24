import dotenv
import os

import unittest

from torch import embedding
from files_ingestor.adapters.llms.anthropic import AnthropicAdapter as AnthropicLLM
from files_ingestor.adapters.llms.ollama import OllamaAdapter as OllamaLLM
from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.llm import FunctionCallingLLMPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort
from files_ingestor.domain.services.file_processor_service import FileProcessorService
from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.adapters.null_logger import NullLoggerAdapter

from files_ingestor.domain.services.react_agent import ReactAgent
from files_ingestor.adapters.config import ConfigConfig
from files_ingestor.adapters.qdrant import QdrantRepository
from files_ingestor.adapters.embedding_models.ollama import OllamaEmbeddingModel

from unittest.mock import Mock

dotenv.load_dotenv()

class TestFileProcessorService(unittest.TestCase):
    def setUp(self):
        self.logger = NullLoggerAdapter()
        self.file_reader = Mock()
        self.mock_vector_store = Mock(spec=VectorStorePort)
        self.mock_embeddings = Mock(spec=EmbeddingModelPort)
        self.service = FileProcessorService(self.logger,
                                            self.mock_vector_store, 
                                            self.mock_embeddings,
                                            self.file_reader)

    def test_process_with_words_operation(self):
        # Arrange
        file_name = "test.txt"
        operations = ["words"]
        content = "Hello world"
        self.file_reader.read.return_value = content

        # Act
        result = self.service.process(file_name, operations)

        # Assert
        self.assertEqual(result["words"], 2)
        self.file_reader.read.assert_called_once_with(file_name)

    def test_process_with_characters_operation(self):
        # Arrange
        file_name = "test.txt"
        operations = ["characters"]
        content = "Hello world"
        self.file_reader.read.return_value = content

        # Act
        result = self.service.process(file_name, operations)

        # Assert
        self.assertEqual(result["characters"], 11)
        self.file_reader.read.assert_called_once_with(file_name)

    def test_process_with_both_operations(self):
        # Arrange
        file_name = "test.txt"
        operations = ["words", "characters"]
        content = "Hello world"
        self.file_reader.read.return_value = content

        # Act
        result = self.service.process(file_name, operations)

        # Assert
        self.assertEqual(result["words"], 2)
        self.assertEqual(result["characters"], 11)
        self.file_reader.read.assert_called_once_with(file_name)

    def test_count_words(self):
        # Arrange
        content = "Hello world"

        # Act
        result = self.service.count_words(content)

        # Assert
        self.assertEqual(result, 2)

    def test_count_characters(self):
        # Arrange
        content = "Hello world"

        # Act
        result = self.service.count_characters(content)

        # Assert
        self.assertEqual(result, 11)

class TestIngestorService(unittest.TestCase):
    def setUp(self):
        self.logger = NullLoggerAdapter()
        self.file_reader = Mock()
        # self.service = FileProcessorService(self.logger, self.file_reader)

    def tearDown(self):
        return super().tearDown()

    def zzz_test_pdf_ingestion(self):
        qdrant_server = os.getenv("QDRANT_SERVER")
        qdrant_repo = QdrantRepository(qdrant_server, self.logger)
        pdf_filepath = "~/Workon/data/aws-overview.pdf"
        service = FileProcessorService(self.logger,
                                       vector_store_repo=qdrant_repo,
                                       embeddings_port=OllamaEmbeddingModel(),
                                       file_reader=self.file_reader)
        nodes = service.ingest_pdf(pdf_filepath)
        self.assertGreater(len(nodes), 0)

if __name__ == "__main__":
    unittest.main()
