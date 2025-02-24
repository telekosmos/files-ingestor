import sys
import os
from dotenv import load_dotenv

import dotenv
from langchain_community.document_loaders.pdf import PyPDFLoader
from llama_index.core import Document
from llama_index.core.ingestion.pipeline import IngestionPipeline
from llama_index.core.node_parser.text.sentence import SentenceSplitter
from llama_index.core.storage.docstore.simple_docstore import SimpleDocumentStore
from llama_index.extractors.entity import EntityExtractor

from files_ingestor.adapters.embedding_models.ollama import OllamaEmbeddingModel
from files_ingestor.adapters.qdrant import QdrantRepository
from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.file_processor_port import FileProcessorPort
from files_ingestor.domain.ports.file_reader_port import FileReaderPort
from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort

dotenv.load_dotenv()

class FileProcessorService(FileProcessorPort):
    """Service to process files and count words or characters."""
    
    def __init__(self, logger: LoggerPort,
                vector_store_repo: VectorStorePort,
                embeddings_port: EmbeddingModelPort,
                file_reader: 'FileReaderPort'):
        self.file_reader = file_reader  # Dependency injection of the file reader
        self.logger = logger
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
        if ["words", "characters"] == operations:
            result = {"characters": self.count_characters(content), "words": self.count_words(content)}

        return result
    
    def count_words(self, content: str) -> int:
        """Counts the number of words in the content."""
        return len(content.split())
    
    def count_characters(self, content: str) -> int:
        """Counts the number of characters in the content."""
        return len(content)
    
    def ingest_pdf(self, pdf_filepath: str) -> list[Document]:
        langchain_documents = PyPDFLoader(file_path=pdf_filepath).load()
        documents = [ Document.from_langchain_format(doc) for doc in langchain_documents ]
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=128)
        entity_extractor = EntityExtractor()
        # embedding_model: EmbeddingModelPort = OllamaEmbeddingModel()
        document_store = SimpleDocumentStore(namespace="aws")
        # vector_repository: VectorStorePort = QdrantRepository(os.getenv("QDRANT_SERVER"))


        pipeline = IngestionPipeline(transformations=[
            splitter,
            # entity_extractor,
            self.embeddings.get_model()],
            docstore=document_store,
            vector_store=self.vector_store_repo.get_vector_store("aws-overview"))
        self.logger.info(f"Running ingestion pipeline (splitter, extractor, embeddings) for {len(documents)} documents.")
        nodes = pipeline.run(documents=documents, show_progress=True)
        self.logger.info(f"Produced {len(nodes)} nodes after processing.")

        return nodes
