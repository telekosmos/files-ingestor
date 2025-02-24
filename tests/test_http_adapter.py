import unittest
from unittest import mock
from unittest.mock import MagicMock, Mock, patch
import unittest.mock

from fastapi.testclient import TestClient

from files_ingestor.adapters.http import create_http_app
from files_ingestor.application.handlers.count_file_handler import CountFileHandler
from files_ingestor.application.handlers.ingestion_handler import IngestionHandler
from files_ingestor.application.queries.count_file_query import CountFileQuery
from files_ingestor.domain.ports.file_processor_port import FileProcessorPort
from files_ingestor.domain.ports.logger_port import LoggerPort


class TestHttpAdapter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_logger = Mock(spec=LoggerPort)
        self.mock_processor = Mock(spec=FileProcessorPort)
        self.mock_handler = Mock(spec=CountFileHandler)
        self.mock_ingestor_handler = Mock(spec=IngestionHandler)
        self.app = create_http_app(self.mock_logger, self.mock_handler, self.mock_ingestor_handler)
        self.client = TestClient(self.app)


    def test_status_endpoint(self):
        """Test that the status endpoint returns the expected response."""
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

if __name__ == "__main__":
    unittest.main()
