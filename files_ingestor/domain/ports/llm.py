from abc import ABC, abstractmethod

from llama_index.core.llms.function_calling import FunctionCallingLLM


class FunctionCallingLLMPort(ABC):
    SUPPORTTED_LIBRARIES = ["llama_index", "langchain"]  # type: ignore

    @abstractmethod
    def get_model(self, library: str) -> FunctionCallingLLM: ...

