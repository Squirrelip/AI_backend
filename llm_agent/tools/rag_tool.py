from langchain.tools import Tool
from llm_agent.utils.embedding import EmbeddingModel
from llm_agent.utils.vectorstore import VectorStore

class RAGTool:
    def __init__(self, collection_name: str):
        self.embedder = EmbeddingModel()
        self.vectorstore = VectorStore(collection_name=collection_name)

    def get_context(self, query: str) -> str:
        query_embedding = self.embedder.embed_texts([query])[0]
        results = self.vectorstore.query(query_embedding)
        docs = results.get("documents", [[]])[0]
        return "\n\n".join(docs) if docs else "No relevant context found."

def get_rag_tool(collection_name: str):
    rag_tool = RAGTool(collection_name)
    return Tool(
        name="RAGSearch",
        func=rag_tool.get_context,
        description="Retrieves context from a session-specific vector store for document generation."
    )
