from typing import List, Iterator, Protocol
from abc import ABC, abstractmethod


class CloudStoragePort(Protocol):
    """Port for cloud storage operations."""

    @abstractmethod
    def download_file(self, url: str, local_path: str) -> str:
        """Downloads a file from cloud storage to local path.
        
        Args:
            url: The cloud storage URL (s3://, file://, etc.)
            local_path: Where to save the file locally
            
        Returns:
            str: Path to the downloaded file
            
        Raises:
            ValueError: If URL is invalid or file not found
            IOError: If download fails
        """
        pass

    @abstractmethod
    def list_files(self, url: str, recursive: bool = False) -> list[str]:
        """Lists files in a cloud storage path.
        
        Args:
            url: The cloud storage URL (s3://, file://, etc.)
            recursive: Whether to list files recursively
            
        Returns:
            list[str]: List of file URLs
            
        Raises:
            ValueError: If URL is invalid
            IOError: If listing fails
        """
        pass

    @abstractmethod
    def is_cloud_url(self, url: str) -> bool:
        """
        Check if the given URL represents a cloud storage location.

        Args:
            url (str): URL to check

        Returns:
            bool: True if the URL is a cloud storage location, False otherwise
        """
        pass
