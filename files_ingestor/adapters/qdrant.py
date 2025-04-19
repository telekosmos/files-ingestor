from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient, QdrantClient

from files_ingestor.domain.ports.logger_port import LoggerPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort


class QdrantRepository(VectorStorePort):
    def __init__(self, connection_string: str, logger: LoggerPort):
        self.logger = logger
        self.qdrant_client = QdrantClient(location=connection_string)
        self.async_qdrant_client = AsyncQdrantClient(location=":memory:")
        self.logger.info(f"Created Qdrant client: {self.qdrant_client.info()}")

    def collection_exist(self, collection_name: str) -> bool:
        try:
            self.qdrant_client.get_collection(collection_name=collection_name)
        except Exception as _:
            return False
        else:
            return True

    def get_collections(self) -> list[str]:
        collections = self.qdrant_client.get_collections()
        return [collection.name for collection in collections]

    def get_vector_store(self, collection_name: str) -> BasePydanticVectorStore:
        vector_store = (
            QdrantVectorStore(
                client=self.qdrant_client, aclient=self.async_qdrant_client, collection_name=collection_name
            )
            if self.async_qdrant_client is not None
            else QdrantVectorStore(client=self.qdrant_client, collection_name=collection_name)
        )
        return vector_store
