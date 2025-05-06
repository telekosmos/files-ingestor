import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from files_ingestor.application.commands.ingest_pdf import IngestCloudStorageCmd
from files_ingestor.domain.services.file_processor_service import FileProcessorService


class TestFileProcessorService(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.config = MagicMock()
        self.vector_store = MagicMock()
        self.embeddings = MagicMock()
        self.file_reader = MagicMock()
        self.s3_storage = MagicMock()
        self.local_storage = MagicMock()

        # Mock embeddings model
        embeddings_model = MagicMock()
        embeddings_model.model_name = "test-model"
        self.embeddings.get_model.return_value = embeddings_model

        # Mock config values
        self.config.get.side_effect = lambda key, default: {
            "documentStores.bookstore.name": "test-store",
            "documentStores.bookstore.props.path": "test-path",
            "collections.book-library": "test-collection",
        }.get(key, default)

        self.service = FileProcessorService(
            logger=self.logger,
            config=self.config,
            vector_store_repo=self.vector_store,
            embeddings_port=self.embeddings,
            file_reader=self.file_reader,
            s3_storage=self.s3_storage,
            local_storage=self.local_storage,
        )

    def test_ingest_cloud_storage_s3(self):
        # Arrange
        url = "s3://bucket/folder/"
        pdf_files = [
            "s3://bucket/folder/doc1.pdf",
            "s3://bucket/folder/doc2.pdf",
        ]
        self.s3_storage.list_files.return_value = pdf_files

        # Create temp dir for downloads
        temp_dir = tempfile.mkdtemp()
        try:
            # Mock download to return paths in temp dir
            def mock_download(url, path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write("dummy content")
                return path

            self.s3_storage.download_file.side_effect = mock_download

            # Mock ingest_pdf method
            with patch.object(self.service, "ingest_pdf") as mock_ingest_pdf:
                mock_ingest_pdf.return_value = []  # Return empty list of nodes

                # Act
                cmd = IngestCloudStorageCmd(url=url, recursive=True)
                result = self.service.process(cmd)

                # Assert
                self.assertEqual(result, 2)  # Processed 2 files
                self.s3_storage.list_files.assert_called_once_with(url, recursive=True)
                self.assertEqual(self.s3_storage.download_file.call_count, 2)
                self.assertEqual(mock_ingest_pdf.call_count, 2)
                self.local_storage.list_files.assert_not_called()
                self.local_storage.download_file.assert_not_called()

        finally:
            # Cleanup temp directory and its contents
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    os.unlink(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_dir)

    def test_ingest_cloud_storage_local(self):
        # Arrange
        temp_dir = tempfile.mkdtemp()
        url = f"file://{temp_dir}"

        try:
            # Create test files
            pdf_path = os.path.join(temp_dir, "test.pdf")
            with open(pdf_path, "w") as f:
                f.write("dummy content")

            txt_path = os.path.join(temp_dir, "test.txt")
            with open(txt_path, "w") as f:
                f.write("dummy txt")

            self.local_storage.list_files.return_value = [f"file://{pdf_path}"]

            # Mock ingest_pdf method
            with patch.object(self.service, "ingest_pdf") as mock_ingest_pdf:
                mock_ingest_pdf.return_value = []  # Return empty list of nodes

                # Act
                cmd = IngestCloudStorageCmd(url=url, recursive=False)
                result = self.service.process(cmd)

                # Assert
                self.assertEqual(result, 1)  # Processed 1 PDF file
                self.local_storage.list_files.assert_called_once_with(url, recursive=False)
                self.local_storage.download_file.assert_called_once()
                mock_ingest_pdf.assert_called_once()
                self.s3_storage.list_files.assert_not_called()
                self.s3_storage.download_file.assert_not_called()

        finally:
            # Cleanup
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
            if os.path.exists(txt_path):
                os.unlink(txt_path)
            os.rmdir(temp_dir)

    def test_ingest_cloud_storage_no_pdfs(self):
        # Arrange
        url = "s3://bucket/empty/"
        self.s3_storage.list_files.return_value = ["s3://bucket/empty/doc.txt"]

        # Act
        cmd = IngestCloudStorageCmd(url=url, recursive=True)
        result = self.service.process(cmd)

        # Assert
        self.assertEqual(result, 0)  # No PDFs processed
        self.logger.warn.assert_called_once_with(f"No PDF files found at {url}")
        self.local_storage.list_files.assert_not_called()

    def test_ingest_cloud_storage_error_handling(self):
        # Arrange
        url = "s3://bucket/error/"
        self.s3_storage.list_files.return_value = ["s3://bucket/error/doc.pdf"]
        self.s3_storage.download_file.side_effect = OSError("Network error")

        # Act
        cmd = IngestCloudStorageCmd(url=url, recursive=False)
        result = self.service.process(cmd)

        # Assert
        self.assertEqual(result, 0)  # No files processed due to error
        self.logger.error.assert_called_once()
        self.local_storage.list_files.assert_not_called()

    def test_ingest_cloud_storage_unsupported_scheme(self):
        # Arrange
        url = "ftp://server/folder/"

        # Act & Assert
        cmd = IngestCloudStorageCmd(url=url, recursive=True)
        with self.assertRaises(ValueError) as ctx:
            self.service.process(cmd)
        self.assertIn("Unsupported URL scheme", str(ctx.exception))
