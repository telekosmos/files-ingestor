from abc import ABC, abstractmethod

from llama_index.core.vector_stores.types import BasePydanticVectorStore


class VectorStorePort(ABC):
    @abstractmethod
    def collection_exist(self, collection_name: str) -> bool: ...
    @abstractmethod
    def get_collections(self) -> list[str]: ...
    @abstractmethod
    def get_vector_store(self, collection_name: str) -> BasePydanticVectorStore: ...
