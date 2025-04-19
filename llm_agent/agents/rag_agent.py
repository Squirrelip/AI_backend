from typing import TypedDict, List
from uuid import uuid4
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from llm_agent.tools.rag_tool import RAGTool
from llm_agent.tools.doc_ingest import ingest_pdf_from_path
from llm_agent.utils.prompt_builder_small import build_prompts
from llm_agent import config

class GraphState(TypedDict):
    messages: List[BaseMessage]

def run_content_generation(
    file_path: str,
    document_type: str,
    user_query: str,
    additional_info: str = "",
    session_id: str = ""
):
    session_id = session_id
    ingest_pdf_from_path(file_path, collection_name=session_id)

    try:
        agent = build_graph(document_type, user_query, additional_info, session_id)
        return agent.invoke({
            "messages": [HumanMessage(content=user_query)]
        })
    finally:
        # 💣 Auto-delete the session-specific vector store
        from llm_agent.utils.vectorstore import VectorStore
        VectorStore(session_id).delete()


def build_graph(document_type: str, user_query: str, additional_info: str, session_id: str):
    rag = RAGTool(collection_name=session_id)
    context = rag.get_context(user_query)

    system_prompt, user_prompt = build_prompts(
        document_type=document_type,
        context=context,
        additional_info=additional_info
    )

    llm = ChatOllama(model=config.OLLAMA_MODEL)

    def run_agent(state: GraphState) -> GraphState:
        return {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
        }

    graph = StateGraph(GraphState)
    graph.add_node("prep", RunnableLambda(run_agent))
    graph.add_node("llm", RunnableLambda(lambda state: {"messages": llm.invoke(state["messages"])}))
    graph.set_entry_point("prep")
    graph.add_edge("prep", "llm")
    graph.add_edge("llm", END)

    return graph.compile()
