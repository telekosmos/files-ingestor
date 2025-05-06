import os

from files_ingestor.domain.ports.cloud_storage_port import CloudStoragePort
from files_ingestor.domain.ports.logger_port import LoggerPort


class LocalStorageAdapter(CloudStoragePort):
    """Local filesystem implementation of the CloudStoragePort."""

    def __init__(self, logger: LoggerPort):
        self.logger = logger

    def is_cloud_url(self, url: str) -> bool:
        """Check if the URL represents a local file location."""
        return url.startswith("file://")

    def _parse_local_url(self, url: str) -> str:
        """Parse file:// URL into local path."""
        if not url.startswith("file://"):
            raise ValueError(f"Invalid file URL: {url}")  # noqa: TRY003
        return url[7:]  # Strip file:// prefix

    def list_files(self, url: str, recursive: bool = False) -> list[str]:
        """Lists files in local directory."""
        path = self._parse_local_url(url)

        if not os.path.exists(path):
            raise ValueError(f"Local path not found: {path}")  # noqa: TRY003

        files = []
        if recursive:
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    files.append(f"file://{file_path}")
        else:
            for entry in os.listdir(path):
                file_path = os.path.join(path, entry)
                if os.path.isfile(file_path):
                    files.append(f"file://{file_path}")
        return files

    def download_file(self, url: str, local_path: str) -> str:
        """Creates a hard link for local files."""
        source_path = self._parse_local_url(url)

        if not os.path.exists(source_path):
            raise ValueError(f"Local file not found: {source_path}")  # noqa: TRY003

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if source_path != local_path:
            os.link(source_path, local_path)  # Hard link for local files

        return local_path
