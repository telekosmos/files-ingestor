import os
import unittest
import unittest.mock
from unittest.mock import Mock

from fastapi.testclient import TestClient

from files_ingestor.adapters.http_app import create_http_app
from files_ingestor.application.handlers.ingestion_handler import IngestionHandler
from files_ingestor.application.handlers.qa_handler import QAHandler
from files_ingestor.domain.ports.logger_port import LoggerPort


class TestHttpAdapter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_logger = Mock(spec=LoggerPort)
        self.mock_qa_handler = Mock(spec=QAHandler)
        self.mock_ingestor_handler = Mock(spec=IngestionHandler)
        self.app = create_http_app(
            logger=self.mock_logger, query_handler=self.mock_qa_handler, ingestor_handler=self.mock_ingestor_handler
        )
        self.client = TestClient(self.app)

    def test_status_endpoint(self):
        """Test that the status endpoint returns the expected response."""
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_ingest_pdf_endpoint(self):
        """Test the PDF ingestion endpoint."""
        # Create a test PDF file
        test_content = b"Test PDF content"
        self.mock_ingestor_handler.handle.return_value = []  # Mock successful ingestion

        # Send request
        response = self.client.post("/ingest-pdf", files={"file": ("test.pdf", test_content, "application/pdf")})

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["filename"], "test.pdf")

    def test_ingest_folder_endpoint(self):
        """Test the folder ingestion endpoint."""
        # Setup mock to return number of processed files
        self.mock_ingestor_handler.handle.return_value = 1

        # Create test folder and file
        test_folder_path = "./tmp/test_folder"
        os.makedirs(test_folder_path, exist_ok=True)
        test_file_path = os.path.join(test_folder_path, "test_file.pdf")
        with open(test_file_path, "w") as f:
            f.write("Test file content")

        try:
            # Make request
            response = self.client.post("/ingest-folder", params={"folder_path": test_folder_path})

            # Verify response
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "success", "num_files": 1})

            # Verify handler was called
            self.mock_ingestor_handler.handle.assert_called_once()
        finally:
            # Clean up
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)
            if os.path.exists(test_folder_path):
                os.rmdir(test_folder_path)

    def test_ingest_cloud_storage_endpoint(self):
        """Test the cloud storage ingestion endpoint with S3 bucket."""
        # Setup mock handler to return number of processed files
        self.mock_ingestor_handler.handle.return_value = 3  # Simulate processing 3 PDF files

        # Test data
        test_request = {"url": "s3://test-bucket/pdfs/", "recursive": True}

        # Make request to the endpoint
        response = self.client.post("/ingest-cloud", json=test_request)

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "num_files": 3})

        # Verify handler was called with correct command
        self.mock_ingestor_handler.handle.assert_called_once()
        command = self.mock_ingestor_handler.handle.call_args[0][0]
        self.assertEqual(command.url, "s3://test-bucket/pdfs/")
        self.assertEqual(command.recursive, True)

    def test_ingest_cloud_storage_endpoint_invalid_url(self):
        """Test cloud storage ingestion with invalid URL."""
        # Setup mock handler to raise ValueError
        self.mock_ingestor_handler.handle.side_effect = ValueError("Invalid S3 URL")

        # Test data with invalid URL
        test_request = {"url": "invalid://test-bucket/pdfs/", "recursive": True}

        # Make request to the endpoint
        response = self.client.post("/ingest-cloud", json=test_request)

        # Verify error response
        self.assertEqual(response.status_code, 200)  # FastAPI still returns 200 as we handle the error
        self.assertEqual(response.json(), {"status": "error", "message": "Invalid S3 URL"})

    def test_ingest_cloud_storage_endpoint_processing_error(self):
        """Test cloud storage ingestion with processing error."""
        # Setup mock handler to raise Exception
        error = Exception("Failed to process S3 files")
        self.mock_ingestor_handler.handle.side_effect = error

        # Test data
        test_request = {"url": "s3://test-bucket/pdfs/", "recursive": True}

        # Make request to the endpoint
        response = self.client.post("/ingest-cloud", json=test_request)

        # Verify error response
        self.assertEqual(response.status_code, 200)  # FastAPI still returns 200 as we handle the error
        self.assertEqual(response.json(), {"status": "error", "message": "Failed to process S3 files"})

        # Verify error was logged
        self.mock_logger.error.assert_called_once_with("Error processing cloud storage", error=error)


if __name__ == "__main__":
    unittest.main()
