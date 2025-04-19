from llama_index.embeddings.ollama.base import OllamaEmbedding

from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort


class OllamaEmbeddingModel(EmbeddingModelPort):
    def __init__(self, url: str = "http://localhost:11434", model: str = "bge-m3:latest"):
        self._model = OllamaEmbedding(base_url=url, model_name=model)
        self._model_name = model

    def get_model(self) -> OllamaEmbedding:
        return self._model
