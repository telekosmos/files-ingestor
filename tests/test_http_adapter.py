import os
import unittest
import unittest.mock
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient

from files_ingestor.adapters.http import create_http_app
from files_ingestor.application.handlers.count_file_handler import CountFileHandler
from files_ingestor.application.handlers.ingestion_handler import IngestionHandler
from files_ingestor.application.handlers.qa_handler import QAHandler
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

    def test_ingest_folder_endpoint(self):
        # Setup mock objects
        logger_mock = MagicMock(spec=LoggerPort)
        qa_handler_mock = MagicMock(spec=QAHandler)
        ingestion_handler_mock = MagicMock(spec=IngestionHandler)
        ingestion_handler_mock.handle.return_value = 1  # Mock the return value of handle method


        # Create an instance of the FastAPI app
        app = create_http_app(logger=logger_mock, query_handler=qa_handler_mock, ingestor_handler=ingestion_handler_mock)
        client = TestClient(app)

        # Define test folder and its contents
        test_folder_path = "./tmp/test_folder"
        os.makedirs(test_folder_path, exist_ok=True)
        with open(os.path.join(test_folder_path, "test_file.pdf"), "w") as f:
            f.write("Test file content")

        # Make a POST request to the /ingest-folder endpoint
        response = client.post("/ingest-folder", json={"folder_path": test_folder_path}, params={"folder_path": test_folder_path})

        # Assert the response status code and content
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "success"
        assert "num_files" in response.json()
        assert response.json()["num_files"] == 1

        # Clean up test folder
        for file_name in os.listdir(test_folder_path):
            file_path = os.path.join(test_folder_path, file_name)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        os.rmdir(test_folder_path)


if __name__ == "__main__":
    unittest.main()
