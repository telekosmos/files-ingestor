from typing import Optional

from langchain_anthropic.chat_models import ChatAnthropic

# from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.llms.anthropic import Anthropic

from files_ingestor.domain.ports.config import ConfigPort
from files_ingestor.domain.ports.llm import FunctionCallingLLMPort
from files_ingestor.domain.ports.logger_port import LoggerPort


class AnthropicAdapter(FunctionCallingLLMPort):
    def __init__(self, config: ConfigPort, logger: LoggerPort, model_name: Optional[str] = None):
        self.config = config
        self.logger = logger
        self.model_name = model_name if model_name is not None else self.config.get("llm.anthropic.name", None)
        api_key = self.config.get("llm.anthropic.api_key", None)
        llama_index_model = Anthropic(model=self.model_name, api_key=api_key)
        langchain_model = ChatAnthropic(model_name=self.model_name, api_key=api_key, timeout=None, stop=None)
        self.models = {"llamaindex": llama_index_model, "langchain": langchain_model}
        self.logger.info(f"Using Anthropic {self.model_name}")

    def get_model(self, library: str):  # type: ignore # noqa: PGH003
        if library not in FunctionCallingLLMPort.__SUPPORTED_LIBRARIES:
            raise ValueError(f"Unsupported library: {library}")  # noqa: TRY003

        return self.models[library]
