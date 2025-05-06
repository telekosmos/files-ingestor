import os
from typing import Annotated

from fastapi import FastAPI, File, Form, Query, UploadFile
from llama_index.core.llms import ChatMessage
from ollama import ChatResponse
from pydantic import BaseModel

from files_ingestor.adapters.config import ConfigConfig
from files_ingestor.adapters.llms.anthropic import AnthropicAdapter
from files_ingestor.adapters.llms.ollama import OllamaAdapter
from files_ingestor.application.commands.ingest_pdf import (
    IngestCloudStorageCmd,
    IngestFolderCmd,
    IngestPDFCmd,
)
from files_ingestor.application.handlers.count_file_handler import CountFileHandler
from files_ingestor.application.handlers.handler import Handler
from files_ingestor.application.handlers.ingestion_handler import IngestionHandler
from files_ingestor.application.handlers.qa_handler import QAHandler
from files_ingestor.application.queries.count_file_query import CountFileQuery
from files_ingestor.application.queries.question_query import QuestionQuery
from files_ingestor.domain.ports.llm import FunctionCallingLLMPort
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
        # self.react_agent = react_agent.ReactAgent(logger=logger)

        @self.app.get("/status")
        async def status():
            return {"status": "ok"}

        # @self.app.get("/query")
        # async def query(request: Annotated[QueryRequest, Query()]):
        #     # response = self.react_agent.query(question.question)
        #     self.logger.info(f"Question parameter: {request.question}")
        #     response = self.query_handler.handle(query=QuestionQuery(query=request.question))
        #     return {"response": response.response}

        @self.app.post("/ingest-pdf")
        async def upload_pdf(file: UploadFile = File(...)):
            # Create a temporary directory to store uploaded files
            upload_dir = "./tmp/files_ingestor_uploads"
            os.makedirs(upload_dir, exist_ok=True)

            # Save the uploaded file
            file_path = os.path.join(upload_dir, file.filename)  # type: ignore
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            # Log the file upload
            self.logger.info(f"Uploaded PDF: {file.filename}")

            # Process the file using IngestionHandler
            try:
                self.ingestion_handler.handle(IngestPDFCmd(filename=file_path))
            except Exception as e:
                self.logger.error("Error processing PDF", error=e)  # noqa: TRY400
                return {"status": "error", "message": str(e)}
            else:
                return {"status": "success", "filename": file.filename}

        @self.app.post("/ingest-folder")
        async def upload_folder(folder_path: str):
            if not os.path.exists(folder_path):
                raise ValueError(f"Folder {folder_path} does not exist")  # noqa: TRY003

            try:
                num_files = self.ingestion_handler.handle(IngestFolderCmd(folder_path=folder_path))
            except Exception as e:
                self.logger.error("Error processing folder", error=e)  # noqa: TRY400
                return {"status": "error", "message": str(e)}
            else:
                return {"status": "success", "num_files": num_files}

        @self.app.post("/ingest-cloud")
        async def ingest_cloud_storage(request: CloudStorageRequest):
            """
            Ingest files from a cloud storage URL.

            Args:
                request (CloudStorageRequest): Request containing cloud storage URL and options

            Returns:
                dict: Status and count of processed files
            """
            try:
                num_files = self.ingestion_handler.handle(
                    IngestCloudStorageCmd(
                        url=request.url,
                        recursive=request.recursive
                    )
                )
                return {"status": "success", "num_files": num_files}
            except ValueError as e:
                self.logger.error("Invalid cloud storage request", error=e)
                return {"status": "error", "message": str(e)}
            except Exception as e:
                self.logger.error("Error processing cloud storage", error=e)  # noqa: TRY400
                return {"status": "error", "message": str(e)}


def create_http_app(logger: LoggerPort, query_handler: QAHandler, ingestor_handler: Handler):
    """Creates an HTTP app for processing files."""
    http_app = HttpApp(logger=logger, qa_handler=query_handler, ingestor_handler=ingestor_handler)
    return http_app.app
