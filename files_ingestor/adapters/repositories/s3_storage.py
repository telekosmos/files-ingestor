import os
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from files_ingestor.domain.ports.cloud_storage_port import CloudStoragePort
from files_ingestor.domain.ports.config import ConfigPort
from files_ingestor.domain.ports.logger_port import LoggerPort


class S3StorageAdapter(CloudStoragePort):
    """
    S3 implementation of the CloudStoragePort.
    Handles interactions with Amazon S3 cloud storage.
    """

    def __init__(self, logger: LoggerPort, config: ConfigPort):
        """
        Initialize S3 storage adapter.

        Args:
            logger (LoggerPort): Logger for recording operations
            config (ConfigPort): Configuration for AWS credentials and settings
        """
        self.logger = logger
        self.config = config

        # Attempt to get AWS credentials from config or environment
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

        # Create S3 client
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )

    def _parse_s3_url(self, url: str) -> tuple[str, str]:
        """Parse S3 URL into bucket and key."""
        if not url.startswith("s3://"):
            raise ValueError(f"Invalid S3 URL: {url}")  # noqa: TRY003

        parsed = urlparse(url)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        return bucket, key

    def is_cloud_url(self, url: str) -> bool:
        """
        Check if the URL represents an S3 location.

        Args:
            url (str): URL to check

        Returns:
            bool: True if the URL is an S3 URL, False otherwise
        """
        return url.startswith("s3://")

    def list_files(self, url: str, recursive: bool = False) -> list[str]:
        """Lists files in S3 bucket."""
        bucket, prefix = self._parse_s3_url(url)

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            files = []

            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    if not recursive and "/" in obj["Key"][len(prefix) :].lstrip("/"):
                        continue
                    files.append(f"s3://{bucket}/{obj['Key']}")

        except ClientError as e:
            self.logger.error("Error listing S3 bucket", e)  # noqa: TRY400
            raise OSError(f"Failed to list {url}: {e!s}") from e  # noqa: TRY003
        else:
            return files

    def download_file(self, url: str, local_path: str) -> str:
        """Downloads a file from S3."""
        bucket, key = self._parse_s3_url(url)

        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(bucket, key, local_path)
        except ClientError as e:
            self.logger.error("Error downloading from S3", e)  # noqa: TRY400
            raise OSError(f"Failed to download {url}: {e!s}") from e  # noqa: TRY003
        else:
            return local_path
