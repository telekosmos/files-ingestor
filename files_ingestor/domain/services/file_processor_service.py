import os
import re
import tempfile
from typing import Sequence, Union

import dotenv
from langchain_community.document_loaders.pdf import PyPDFLoader
from llama_index.core import Document
from llama_index.core.ingestion.pipeline import IngestionPipeline
from llama_index.core.node_parser.text.sentence import SentenceSplitter
from llama_index.core.schema import BaseNode
from llama_index.core.storage.docstore.simple_docstore import SimpleDocumentStore

from files_ingestor.application.commands import Command
from files_ingestor.application.commands.ingest_pdf import IngestCloudStorageCmd, IngestFolderCmd, IngestPDFCmd
from files_ingestor.domain.ports.cloud_storage_port import CloudStoragePort
from files_ingestor.domain.ports.config import ConfigPort
from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.file_processor_port import FileProcessorPort
from files_ingestor.domain.ports.file_reader_port import FileReaderPort
from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort

dotenv.load_dotenv()


class FileProcessorService(FileProcessorPort):
    """Service to process files and count words or characters."""

    def __init__(
        self,
        logger: LoggerPort,
        config: ConfigPort,
        vector_store_repo: VectorStorePort,
        embeddings_port: EmbeddingModelPort,
        file_reader: FileReaderPort,
        s3_storage: CloudStoragePort,
        local_storage: CloudStoragePort,
    ):
        self.file_reader = file_reader
        self.logger = logger
        self.config = config
        self.vector_store_repo = vector_store_repo
        self.embeddings = embeddings_port
        self.s3_storage = s3_storage
        self.local_storage = local_storage

    # def process(self, file_name: str, operations: list[str]) -> dict:
    #     """Processes the file and counts words and/or characters."""
    #     content = self.file_reader.read(file_name)
    #     result = {}
    #     self.logger.info(f"operations: {operations}")
    #     if "words" in operations:
    #         result["words"] = self.count_words(content)
    #     if "characters" in operations:
    #         result["characters"] = self.count_characters(content)
    #     if operations == ["words", "characters"]:
    #         result = {"characters": self.count_characters(content), "words": self.count_words(content)}

    #     return result

    def process(self, cmd: Command) -> Sequence[BaseNode] | int:
        match cmd:
            case IngestPDFCmd():
                return self.ingest_pdf(cmd.file_name)
            case IngestFolderCmd():
                return self.ingest_folder(cmd.folder_path)
            case IngestCloudStorageCmd():
                return self.ingest_cloud_storage(cmd.url, cmd.recursive)
            case _:
                raise ValueError(f"Unknown command type: {type(cmd)}")

    def _get_storage_adapter(self, url: str) -> CloudStoragePort:
        """Get the appropriate storage adapter for the URL."""
        if url.startswith('s3://'):
            return self.s3_storage
        elif url.startswith('file://'):
            return self.local_storage
        else:
            raise ValueError(f'Unsupported URL scheme: {url}')

    def ingest_cloud_storage(self, url: str, recursive: bool = False) -> int:
        """Ingests files from a cloud storage URL."""
        try:
            # Get appropriate storage adapter
            storage = self._get_storage_adapter(url)
            
            # List all files at the URL
            files = storage.list_files(url, recursive=recursive)
            
            # Filter for PDF files
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            if not pdf_files:
                self.logger.warn(f"No PDF files found at {url}")
                return 0
                
            processed = 0
            temp_dir = tempfile.mkdtemp(prefix='cloud_storage_')
            
            try:
                for file_url in pdf_files:
                    # Download to temp location
                    filename = os.path.basename(file_url)
                    local_path = os.path.join(temp_dir, filename)
                    
                    try:
                        storage.download_file(file_url, local_path)
                        self.ingest_pdf(local_path)
                        processed += 1
                    except (ValueError, IOError) as e:
                        self.logger.error(f"Failed to process {file_url}: {str(e)}")
                        continue
                    finally:
                        # Clean up downloaded file
                        if os.path.exists(local_path):
                            os.unlink(local_path)
                            
                return processed
            finally:
                # Clean up temp directory
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                    
        except Exception as e:
            self.logger.error(f"Error processing cloud storage: {str(e)}")
            raise

    def ingest_pdf(self, pdf_filepath: str) -> Sequence[BaseNode]:
        langchain_documents = PyPDFLoader(file_path=pdf_filepath).load()
        documents = [Document.from_langchain_format(doc) for doc in langchain_documents]

        doc_store_name = self.config.get("documentStores.bookstore.name", "")
        persist_path = self.config.get("documentStores.bookstore.props.path", "data")
        collection_name = self.config.get("collections.book-library", "book-library")

        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=128)
        document_store = SimpleDocumentStore(namespace=doc_store_name)
        embeddings_model = self.embeddings.get_model()
        model_name = embeddings_model.model_name
        pipeline = IngestionPipeline(
            transformations=[splitter, embeddings_model],
            docstore=document_store,
            vector_store=self.vector_store_repo.get_vector_store(collection_name=collection_name),
        )

        pipeline.load(persist_path) if os.path.exists(persist_path) else None

        self.logger.info(
            f"Running ingestion pipeline (splitter, extractor, {model_name}) for {len(documents)} documents."
        )
        nodes = pipeline.run(documents=documents, show_progress=True)
        self.logger.info(f"Produced {len(nodes)} nodes after processing.")
        pipeline.persist(persist_path)

        return nodes

    def ingest_folder(self, folder_path: str) -> int:
        num_files = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".pdf"):
                    self.logger.info(f"Ingesting {file} from {folder_path}")
                    pdf_filepath = os.path.join(root, file)
                    self.ingest_pdf(pdf_filepath)
                    num_files += 1
                else:
                    self.logger.warn(f"Skipping non-pdf file: {file}")

        self.logger.info(f"Ingested {num_files} files from folder {folder_path}")
        return num_files
