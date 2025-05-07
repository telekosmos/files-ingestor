import os

# from llama_index.embeddings.huggingface_api.base import HuggingFaceInferenceAPIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceInferenceAPIEmbedding

from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort


class HuggingfaceEmbeddingModel(EmbeddingModelPort):
    def __init__(self, model: str = "BAAI/bge-m3"):
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self._model = HuggingFaceInferenceAPIEmbedding(model_name=model, token=hf_token)

    def get_model(self) -> HuggingFaceInferenceAPIEmbedding:
        return self._model
