# import files_ingestor.domain.ports.config as ConfigPort
import langchain
from langchain_ollama.chat_models import ChatOllama
from langchain.chat_models.base import BaseChatModel
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.llms.ollama import Ollama

from files_ingestor.domain.ports.llm import FunctionCallingLLMPort
from files_ingestor.domain.ports.logger_port import LoggerPort


class OllamaAdapter(FunctionCallingLLMPort):
    # def __init__(self, model_name: str): # , config: ConfigPort):
    #     self.config = config
    #     self.model_name = self.config.get(f"llm.{model_name}.name")
    #     self.ollama_model = Ollama(
    #         model=self.model_name,
    #         base_url=self.config.get(f"llm.{model_name}.base_url"),
    #         request_timeout=self.config.get(f"llm.{model_name}.timeout")
    #     )

    def __init__(self, model_name: str, logger: LoggerPort):
        self.logger = logger
        self.model_name = model_name
        llama_index_model = Ollama(model=self.model_name, base_url="http://localhost:11434", request_timeout=300)
        langchain_model = ChatOllama(model=self.model_name, base_url="http://localhost:11434", request_timeout=300)
        self.models = {"llamaindex": llama_index_model, "langchain": langchain_model}
        self.logger.info(f"Using Ollama model {self.model_name}")

    def get_model(self, library):
        if library not in FunctionCallingLLMPort.SUPPORTTED_LIBRARIES:
            raise ValueError(f"Unsupported library: {library}")  # noqa: TRY003

        return self.models[library]
