import os
import unittest
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from files_ingestor.adapters.repositories.s3_storage import S3StorageAdapter
from files_ingestor.domain.ports.config import ConfigPort
from files_ingestor.domain.ports.logger_port import LoggerPort


class TestS3StorageAdapter(unittest.TestCase):
    def setUp(self):
        """Set up test dependencies."""
        self.mock_logger = Mock(spec=LoggerPort)
        self.mock_config = Mock(spec=ConfigPort)

        # Patch boto3.client to return a mock before creating the adapter
        self.boto3_patcher = patch("boto3.client")
        self.mock_boto3_client = self.boto3_patcher.start()

        # Create mock S3 client and paginator
        self.mock_s3_client = Mock()
        self.mock_boto3_client.return_value = self.mock_s3_client

        self.mock_paginator = Mock()
        self.mock_s3_client.get_paginator.return_value = self.mock_paginator

        # Create the S3 storage adapter
        self.s3_storage_adapter = S3StorageAdapter(self.mock_logger, self.mock_config)

    def tearDown(self):
        """Clean up mocks after each test."""
        self.boto3_patcher.stop()

    def test_is_cloud_url(self):
        """Test URL validation for S3 URLs."""
        self.assertTrue(self.s3_storage_adapter.is_cloud_url("s3://bucket/path"))
        self.assertFalse(self.s3_storage_adapter.is_cloud_url("https://bucket.s3.amazonaws.com/path"))
        self.assertFalse(self.s3_storage_adapter.is_cloud_url("file:///local/path"))

    def test_list_files_non_recursive(self):
        """Test listing files in a non-recursive manner."""
        # Mock pagination response
        self.mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "folder/document1.pdf"},
                    {"Key": "folder/document2.txt"},
                    {"Key": "folder/subfolder/document3.pdf"},
                ]
            }
        ]

        # List files non-recursively
        files = self.s3_storage_adapter.list_files("s3://test-bucket/folder/", recursive=False)

        # Verify results - should only include files directly in folder
        self.assertEqual(len(files), 2)
        self.assertIn("s3://test-bucket/folder/document1.pdf", files)
        self.assertIn("s3://test-bucket/folder/document2.txt", files)

        # Verify method calls
        self.mock_s3_client.get_paginator.assert_called_once_with("list_objects_v2")
        self.mock_paginator.paginate.assert_called_once_with(Bucket="test-bucket", Prefix="folder/")

    def test_list_files_recursive(self):
        """Test listing files recursively."""
        # Mock pagination response
        self.mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "folder/document1.pdf"},
                    {"Key": "folder/document2.txt"},
                    {"Key": "folder/subfolder/document3.pdf"},
                ]
            }
        ]

        # List files recursively
        files = self.s3_storage_adapter.list_files("s3://test-bucket/folder/", recursive=True)

        # Verify results - should include all files
        self.assertEqual(len(files), 3)
        self.assertIn("s3://test-bucket/folder/document1.pdf", files)
        self.assertIn("s3://test-bucket/folder/document2.txt", files)
        self.assertIn("s3://test-bucket/folder/subfolder/document3.pdf", files)

        # Verify paginator calls
        self.mock_paginator.paginate.assert_called_once_with(Bucket="test-bucket", Prefix="folder/")

    def test_list_files_empty_response(self):
        """Test listing files when no files exist."""
        # Mock empty response
        self.mock_paginator.paginate.return_value = [{}]

        # List files
        files = self.s3_storage_adapter.list_files("s3://test-bucket/empty/", recursive=True)

        # Verify empty result
        self.assertEqual(len(files), 0)

    def test_download_file(self):
        """Test downloading a file from S3."""
        # Prepare local path
        import tempfile

        local_path = os.path.join(tempfile.gettempdir(), "downloaded_file.pdf")

        # Download file
        downloaded_path = self.s3_storage_adapter.download_file("s3://test-bucket/path/to/file.pdf", local_path)

        # Verify download
        self.assertEqual(downloaded_path, local_path)
        self.mock_s3_client.download_file.assert_called_once_with("test-bucket", "path/to/file.pdf", local_path)

    def test_invalid_url_raises_error(self):
        """Test that invalid URLs raise a ValueError."""
        invalid_urls = ["https://invalid-url", "file:///local/path", "gs://bucket/path", "ftp://server/path"]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as context:
                    self.s3_storage_adapter.list_files(url)
                self.assertIn("Invalid S3 URL", str(context.exception))

                with self.assertRaises(ValueError) as context:
                    self.s3_storage_adapter.download_file(url, "/tmp/test.pdf")  # noqa: S108
                self.assertIn("Invalid S3 URL", str(context.exception))

    def test_s3_client_error_handling(self):
        """Test error handling for S3 client errors."""
        # Mock S3 client errors
        errors = [
            ("NoSuchBucket", "The specified bucket does not exist"),
            ("NoSuchKey", "The specified key does not exist"),
            ("AccessDenied", "Access Denied"),
        ]

        for error_code, error_message in errors:
            with self.subTest(error=error_code):
                # Mock error for list_files
                self.mock_paginator.paginate.side_effect = ClientError(
                    {"Error": {"Code": error_code, "Message": error_message}}, "ListObjectsV2"
                )

                with self.assertRaises(IOError) as context:
                    self.s3_storage_adapter.list_files("s3://test-bucket/path/")
                self.assertIn(error_message, str(context.exception))
                self.mock_logger.error.assert_called()

                # Mock error for download_file
                self.mock_s3_client.download_file.side_effect = ClientError(
                    {"Error": {"Code": error_code, "Message": error_message}}, "GetObject"
                )

                with self.assertRaises(IOError) as context:
                    self.s3_storage_adapter.download_file("s3://test-bucket/file.pdf", "/tmp/test.pdf")  # noqa: S108
                self.assertIn(error_message, str(context.exception))
                self.mock_logger.error.assert_called()


if __name__ == "__main__":
    unittest.main()
