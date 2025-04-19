import unittest
from unittest.mock import Mock, patch

from files_ingestor.adapters.terminal import TerminalAdapter
from files_ingestor.application.handlers.handler import Handler
from files_ingestor.application.commands.ingest_pdf import IngestPDFCmd
from files_ingestor.domain.ports.logger_port import LoggerPort


class TestTerminalAdapter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_logger = Mock(spec=LoggerPort)
        self.mock_handler = Mock(spec=Handler)
        
        # Create the terminal adapter with mocked dependencies
        self.adapter = TerminalAdapter(
            logger=self.mock_logger, 
            handler=self.mock_handler
        )

    def test_run_with_pdf_ingestion(self):
        """Test running the terminal adapter with PDF ingestion."""
        # Mock the handler to return a specific result
        test_file_name = 'test_document.pdf'
        expected_result = {"status": "processed", "file": test_file_name}
        self.mock_handler.handle.return_value = expected_result

        # Simulate user input for file name
        with patch('builtins.input', return_value=test_file_name):
            self.adapter.run()

            # Assert that the handler was called with correct IngestPDFCmd
            self.assertIsInstance(
                self.mock_handler.handle.call_args[0][0],
                IngestPDFCmd
            )
            self.assertEqual(
                self.mock_handler.handle.call_args[0][0].file_name,
                test_file_name
            )

            # Assert that the result was logged
            self.mock_logger.info.assert_called_once_with(f"Result: {expected_result}")

    def test_run_with_different_file(self):
        """Test running the terminal adapter with a different file."""
        # Mock the handler to return a specific result
        test_file_name = 'another_document.pdf'
        expected_result = {"status": "processed", "file": test_file_name}
        self.mock_handler.handle.return_value = expected_result

        # Simulate user input for file name
        with patch('builtins.input', return_value=test_file_name):
            self.adapter.run()

            # Assert that the handler was called with correct IngestPDFCmd
            self.assertIsInstance(
                self.mock_handler.handle.call_args[0][0],
                IngestPDFCmd
            )
            self.assertEqual(
                self.mock_handler.handle.call_args[0][0].file_name,
                test_file_name
            )

            # Assert that the result was logged
            self.mock_logger.info.assert_called_once_with(f"Result: {expected_result}")


if __name__ == "__main__":
    unittest.main()
