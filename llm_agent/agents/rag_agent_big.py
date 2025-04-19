from typing import TypedDict, List
from uuid import uuid4
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from llm_agent.utils.prompt_builder_big import build_prompts
from llm_agent import config


class GraphState(TypedDict):
    messages: List[BaseMessage]


class WebSearchTool:
    def __init__(self, top_k: int = 20):
        self.top_k = top_k

    def search(self, query: str) -> str:
        # TODO: Replace this placeholder with actual search API call (e.g., SerpAPI, Tavily, Bing)
        return f"Top {self.top_k} web search results for query: '{query}' (placeholder results)."


def create_agent(document_type: str, query: str, additional_info: str = "", session_id: str = ""):
    prompts = build_prompts(document_type, query, additional_info)
    model = ChatOllama(model=config.MODEL)
    web_tool = WebSearchTool(top_k=20)

    def invoke_tool(state: GraphState) -> GraphState:
        user_query = state["messages"][-1].content
        search_results = web_tool.search(user_query)
        tool_message = SystemMessage(content=search_results)
        return {"messages": state["messages"] + [tool_message]}

    def call_model(state: GraphState) -> GraphState:
        response = model.invoke(state["messages"])
        return {"messages": state["messages"] + [response]}

    workflow = StateGraph(GraphState)
    workflow.add_node("web_search", RunnableLambda(invoke_tool))
    workflow.add_node("generate", RunnableLambda(call_model))
    workflow.set_entry_point("web_search")
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


def run_web_rag(document_type: str, user_query: str, additional_info: str = "", session_id: str = ""):
    session_id = session_id or str(uuid4())
    try:
        agent = create_agent(document_type, user_query, additional_info, session_id)
        return agent.invoke({"messages": [HumanMessage(content=user_query)]})
    except Exception as e:
        return {"error": str(e)}
