from typing import Any, Dict, Sequence

from llama_index.core.agent import ReActAgent
from llama_index.core.memory.types import BaseMemory
from llama_index.core.tools import QueryEngineTool

from files_ingestor.deps.llamaindex_wrappers import LlamaIndexWrapper
from files_ingestor.domain.ports.config import ConfigPort
from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.llm import FunctionCallingLLMPort
from files_ingestor.domain.ports.logger_port import LoggerPort

# from files_ingestor.domain.ports.sql_repository import SQLRepositoryPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort


class ReactAgent:
    def __init__(self,
                 embedding_model: EmbeddingModelPort,
                 llm: FunctionCallingLLMPort,
                 config: ConfigPort,
                 logger: LoggerPort,
                 # db: SQLRepositoryPort,
                 vector_store: VectorStorePort):
        self.llm = llm
        self.config = config
        self.logger = logger
        # self.db = db
        self.embedding_model = embedding_model
        self.vector_store = vector_store

        agent_config = self.config.get("agent")
        agent_collections = agent_config["useCollections"]
        agent_context = agent_config["context"]

        collections_cfg: dict[str, Any] = self.config.get("vectorstore.qdrant.collections")
        collections_info: Sequence[Any] = list(collections_cfg.values())
        mk_tool = LlamaIndexWrapper.create_retrieval_tool(self.vector_store,
                                                          self.embedding_model, self.llm)
        retrieval_tools = [mk_tool(f"{coll_info["name"]}", coll_info["tool_description"], topk=5) 
                           for coll_info in collections_info if coll_info["name"] in agent_collections]
        # fullindex_tool = LlamaIndexWrapper.mk_autovector_retrieval_tool(
        #     collection_name=agent_collections[0],
        #     num_nodes=8,
        #     embedding_model=self.embedding_model.get_model(),
        #     llm=self.llm.get_model(),
        #     vector_store=self.vector_store
        # )
        self.tools: Sequence[QueryEngineTool] = [
            # LlamaIndexWrapper.create_sql_tool(self.db, self.llm, self.embedding_model)
        ] + retrieval_tools

        tool_names = [ tool.metadata.name for tool in self.tools ]
        self.logger.info(f"Tools provided to the agent: {tool_names}")
        # context=("You are a financial and economic analyst expert in Fortune 100 companies." 
        #     "Your will answer the questions about these companies and the market they belong to from a financial and economic point of view as a veteran finantial investor")
        llm_for_agent = self.llm.get_model("llamaindex")
        self.agent: ReActAgent = ReActAgent(
            tools=self.tools,
            llm=llm_for_agent,
            verbose=True,
            max_iterations=15,
            context=agent_context,
            memory=BaseMemory.from_defaults(llm=llm_for_agent))

    def query(self, question: str) -> str:
        self.logger.info(f"Question received: {question}")
        response = self.agent.chat(question)
        return response
