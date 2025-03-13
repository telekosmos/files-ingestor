
import os
from typing import Union

import dotenv
from langchain_community.document_loaders.pdf import PyPDFLoader
from llama_index.core import Document
from llama_index.core.ingestion.pipeline import IngestionPipeline
from llama_index.core.node_parser.text.sentence import SentenceSplitter
from llama_index.core.storage.docstore.simple_docstore import SimpleDocumentStore
from llama_index.extractors.entity import EntityExtractor

from files_ingestor.domain.ports.config import ConfigPort
from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.file_processor_port import FileProcessorPort
from files_ingestor.domain.ports.file_reader_port import FileReaderPort
from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort

dotenv.load_dotenv()

class FileProcessorService(FileProcessorPort):
    """Service to process files and count words or characters."""

    def __init__(self, logger: LoggerPort, config: ConfigPort,
                vector_store_repo: Union[VectorStorePort, None],
                embeddings_port: Union[EmbeddingModelPort, None],
                file_reader: 'FileReaderPort'):
        self.file_reader = file_reader  # Dependency injection of the file reader
        self.logger = logger
        self.config = config
        self.vector_store_repo = vector_store_repo
        self.embeddings = embeddings_port

    def process(self, file_name: str, operations: list[str]) -> dict:
        """Processes the file and counts words and/or characters."""
        content = self.file_reader.read(file_name)
        result = {}
        self.logger.info(f"operations: {operations}")
        if "words" in operations:
            result["words"] = self.count_words(content)
        if "characters" in operations:
            result["characters"] = self.count_characters(content)
        if operations == ["words", "characters"]:
            result = {"characters": self.count_characters(content), "words": self.count_words(content)}

        return result

    def count_words(self, content: str) -> int:
        """Counts the number of words in the content."""
        return len(content.split())

    def count_characters(self, content: str) -> int:
        """Counts the number of characters in the content."""
        return len(content)

    def ingest_pdf(self, pdf_filepath: str):
        langchain_documents = PyPDFLoader(file_path=pdf_filepath).load()
        documents = [ Document.from_langchain_format(doc) for doc in langchain_documents ]

        doc_store_name = self.config.get("documentStores.bookstore.name", "")
        persist_path = self.config.get("documentStores.bookstore.props.path", "data")
        collection_name = self.config.get("collections.book-library", "book-library")

        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=128)
        document_store = SimpleDocumentStore(namespace=doc_store_name)
        embeddings_model = self.embeddings.get_model() # type: ignore  # noqa: PGH003
        model_name = embeddings_model.model_name
        pipeline = IngestionPipeline(transformations=[splitter, embeddings_model],
            docstore=document_store,
            vector_store=self.vector_store_repo.get_vector_store(collection_name=collection_name)) # type: ignore  # noqa: PGH003

        pipeline.load(persist_path) if os.path.exists(persist_path) else None

        self.logger.info(f"Running ingestion pipeline (splitter, extractor, {model_name}) for {len(documents)} documents.")
        nodes = pipeline.run(documents=documents, show_progress=True)
        self.logger.info(f"Produced {len(nodes)} nodes after processing.")
        pipeline.persist(persist_path)

        return nodes

    def ingest_folder(self, folder_path:str):
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
