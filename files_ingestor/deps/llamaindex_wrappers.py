from typing import Callable

from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core.indices.vector_store import VectorIndexAutoRetriever, VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.core.tools import QueryEngineTool, ToolMetadata

# from llama_index.tools.database import DatabaseToolSpec
# from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.vector_stores import MetadataInfo, VectorStoreInfo
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from files_ingestor.domain.ports.embedding_model import EmbeddingModelPort
from files_ingestor.domain.ports.llm import FunctionCallingLLMPort
from files_ingestor.domain.ports.vectorstore import VectorStorePort

# from files_ingestor.domain.ports.sql_repository import SQLRepositoryPort


class LlamaIndexWrapper:
    @staticmethod
    def mk_index(
        collection_name: str, vector_store: VectorStorePort, embedding_model: EmbeddingModelPort
    ) -> VectorStoreIndex:
        qdrant_vector_store: BasePydanticVectorStore = vector_store.get_vector_store(collection_name)
        # storage_context = StorageContext.from_defaults(vector_store=qdrant_vector_store)
        index = VectorStoreIndex.from_vector_store(
            vector_store=qdrant_vector_store,
            embed_model=embedding_model.get_model(),
            show_progress=True,
            use_async=False,
        )
        return index

    @staticmethod
    def mk_vector_retriever(
        collection_name: str, similarity_top_k: int, vector_store: VectorStorePort, embedding_model: EmbeddingModelPort
    ) -> VectorIndexRetriever:
        index = LlamaIndexWrapper.mk_index(collection_name, vector_store, embedding_model)
        retriever = VectorIndexRetriever(
            index=index, similarity_top_k=similarity_top_k, embed_model=embedding_model.get_model()
        )
        return retriever

    @staticmethod
    def mk_autovector_retrieval_tool(
        collection_name: str,
        num_nodes: int,
        vector_store: VectorStorePort,
        embedding_model: EmbeddingModelPort,
        llm: FunctionCallingLLMPort,
    ) -> QueryEngineTool:
        fullindex = LlamaIndexWrapper.mk_index(collection_name, vector_store, embedding_model)
        vector_store_info = VectorStoreInfo(
            content_info="Information and news about Fortune 100 companies",
            metadata_info=[
                MetadataInfo(name="company_name", description="The company name", type="str"),
                MetadataInfo(name="company_id", description="The company id", type="str"),
                MetadataInfo(name="description", description="The company description", type="str"),
                MetadataInfo(name="title", description="The news title and topic", type="str"),
                # MetadataInfo(name="sector", description="The company sector", type="str")
            ],
        )
        retriever = VectorIndexAutoRetriever(
            index=fullindex,
            similarity_top_k=num_nodes,
            llm=llm.get_model("llamaindex"),
            vector_store_info=vector_store_info,
        )
        retriever_query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=get_response_synthesizer(llm=llm.get_model("llamaindex"), verbose=True),
        )

        tool_metadata = ToolMetadata(
            description="Provides information and news about Fortune 100 companies", name="fortune100_info_news"
        )
        vector_tool = QueryEngineTool(query_engine=retriever_query_engine, metadata=tool_metadata)
        return vector_tool

    @staticmethod
    def create_query_engine(
        collection_name: str,
        topk: int,
        vector_store: VectorStorePort,
        embedding_model: EmbeddingModelPort,
        llm: FunctionCallingLLMPort,
    ) -> tuple[RetrieverQueryEngine, VectorIndexRetriever]:
        retriever = LlamaIndexWrapper.mk_vector_retriever(collection_name, topk, vector_store, embedding_model)
        response_synthesizer = get_response_synthesizer(
            response_mode=ResponseMode.TREE_SUMMARIZE, llm=llm.get_model("llamaindex"), verbose=True
        )
        return RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        ), retriever

    @staticmethod
    def create_retrieval_tool(
        vector_store: VectorStorePort, embedding_model: EmbeddingModelPort, llm: FunctionCallingLLMPort
    ) -> Callable[[str, str, int], QueryEngineTool]:
        # collection_name: str, tool_description: str, topk: int)

        def _mk_tool(collection_name: str, tool_description: str, topk: int) -> QueryEngineTool:
            query_engine, _ = LlamaIndexWrapper.create_query_engine(
                collection_name, topk, vector_store, embedding_model, llm
            )

            return QueryEngineTool(
                query_engine=query_engine,
                metadata=ToolMetadata(
                    name=f"{collection_name}-tool",
                    description=tool_description,
                ),
            )

        return _mk_tool
