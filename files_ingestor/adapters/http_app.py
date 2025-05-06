import os

from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

from files_ingestor.application.commands.ingest_pdf import (
    IngestCloudStorageCmd,
    IngestFolderCmd,
    IngestPDFCmd,
)
from files_ingestor.application.handlers.handler import Handler
from files_ingestor.application.handlers.qa_handler import QAHandler
from files_ingestor.domain.ports.logger_port import LoggerPort


class FileProcessingRequest(BaseModel):
    file: str
    operations: str


class QueryRequest(BaseModel):
    question: str


class CloudStorageRequest(BaseModel):
    """Request model for cloud storage URL ingestion."""

    url: str
    recursive: bool = True


class HttpApp:
    def __init__(self, logger: LoggerPort, qa_handler: QAHandler, ingestor_handler: Handler):
        self.app = FastAPI()
        self.logger = logger
        self.query_handler = qa_handler
        self.ingestion_handler = ingestor_handler
        self._setup_routes()

    def _setup_routes(self):
        self.app.get("/status")(self._status)
        self.app.post("/ingest-pdf")(self._upload_pdf)
        self.app.post("/ingest-folder")(self._upload_folder)
        self.app.post("/ingest-cloud")(self._ingest_cloud_storage)

    async def _status(self):
        return {"status": "ok"}

    async def _upload_pdf(self, file: UploadFile):
        upload_dir = "./tmp/files_ingestor_uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        self.logger.info(f"Uploaded PDF: {file.filename}")

        try:
            self.ingestion_handler.handle(IngestPDFCmd(filename=file_path))
        except Exception as e:
            self.logger.error("Error processing PDF", error=e)  # noqa: TRY400
            return {"status": "error", "message": str(e)}
        else:
            return {"status": "success", "filename": file.filename}

    async def _upload_folder(self, folder_path: str):
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder {folder_path} does not exist")  # noqa: TRY003

        try:
            num_files = self.ingestion_handler.handle(IngestFolderCmd(folder_path=folder_path))
        except Exception as e:
            self.logger.error("Error processing folder", error=e)  # noqa: TRY400
            return {"status": "error", "message": str(e)}
        else:
            return {"status": "success", "num_files": num_files}

    async def _ingest_cloud_storage(self, request: CloudStorageRequest):
        """Ingest files from a cloud storage URL."""
        try:
            num_files = self.ingestion_handler.handle(
                IngestCloudStorageCmd(url=request.url, recursive=request.recursive)
            )
        except ValueError as e:
            self.logger.error("Invalid cloud storage request", e)  # noqa: TRY400
            return {"status": "error", "message": str(e)}
        except Exception as e:
            self.logger.error("Error processing cloud storage", error=e)  # noqa: TRY400
            return {"status": "error", "message": str(e)}
        else:
            return {"status": "success", "num_files": num_files}


def create_http_app(logger: LoggerPort, query_handler: QAHandler, ingestor_handler: Handler):
    """Creates an HTTP app for processing files."""
    http_app = HttpApp(logger=logger, qa_handler=query_handler, ingestor_handler=ingestor_handler)
    return http_app.app
