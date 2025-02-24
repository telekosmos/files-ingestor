import os
from typing import Annotated

from fastapi import FastAPI, File, Query, UploadFile
from pydantic import BaseModel

from files_ingestor.application.commands.ingest_pdf import IngestPDFCmd
from files_ingestor.application.handlers.count_file_handler import CountFileHandler
from files_ingestor.application.handlers.ingestion_handler import IngestionHandler
from files_ingestor.application.handlers.qa_handler import QAHandler
from files_ingestor.application.queries.count_file_query import CountFileQuery
from files_ingestor.application.queries.question_query import QuestionQuery
from files_ingestor.domain.ports.logger_port import LoggerPort


class FileProcessingRequest(BaseModel):
    file: str
    operations: str

class QueryRequest(BaseModel):
    question: str

class HttpApp:
    def __init__(self, logger: LoggerPort, qa_handler: QAHandler, ingestor_handler: IngestionHandler):
        self.app = FastAPI()
        self.logger = logger
        self.query_handler = qa_handler
        self.ingestion_handler = ingestor_handler
        # self.react_agent = react_agent.ReactAgent(logger=logger)

        @self.app.get("/status")
        async def status():
            return {"status": "ok"}

        # @self.app.get("/process-file")
        # async def process_file(request: Annotated[FileProcessingRequest, Query()]):
        #     query = CountFileQuery(file_name=request.file, operations=request.operations.split(","))
        #     self.logger.info(f"query: CountFileQuery({query.file_name}, {query.operations})")
        #     result = query_handler.handle(query)
        #     return {"result": result}

        @self.app.get("/query")
        async def query(request: Annotated[QueryRequest, Query()]):
            # response = self.react_agent.query(question.question)
            self.logger.info(f"Question parameter: {request.question}")
            response = self.query_handler.handle(query=QuestionQuery(query=request.question))
            return {"response": response.response}

        @self.app.post("/ingest-pdf")
        async def upload_pdf(file: UploadFile = File(...)):
            # Create a temporary directory to store uploaded files
            upload_dir = "./tmp/files_ingestor_uploads"
            os.makedirs(upload_dir, exist_ok=True)

            # Save the uploaded file
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            # Log the file upload
            self.logger.info(f"Uploaded PDF: {file.filename}")

            # Process the file using IngestionHandler
            try:
                self.ingestion_handler.handle(IngestPDFCmd(filename=file_path))
            except Exception as e:
                self.logger.error(f"Error processing PDF: {str(e)}")  # noqa: TRY400 RUF010
                return {"status": "error", "message": str(e)}
            else:
                return {"status": "success", "filename": file.filename}


def create_http_app(logger: LoggerPort, query_handler: QAHandler, ingestor_handler: IngestionHandler):
    """Creates an HTTP app for processing files."""
    http_app = HttpApp(logger=logger, qa_handler=query_handler, ingestor_handler=ingestor_handler)
    return http_app.app
