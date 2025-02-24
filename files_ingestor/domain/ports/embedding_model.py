from abc import ABC, abstractmethod

from llama_index.core.embeddings import BaseEmbedding


class EmbeddingModelPort(ABC):
    @abstractmethod
    def get_model(self) -> BaseEmbedding: ...
