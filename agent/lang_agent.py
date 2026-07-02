"""LangGraph Agent - 校园知识问答（Stream + Checkpoint）"""
import os, json
from typing import Literal
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv(override=True)

# ---------- LLM (懒加载，避免慢导入) ----------
_llm = None
def _get_llm():
    global _llm
    if _llm is None:
        from langchain_openai import ChatOpenAI
        _llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
            temperature=0.3,
            streaming=True,
        )
    return _llm

SYSTEM_PROMPT = """你是校园知识问答助手。

规则：
1. 优先用 search_knowledge 查知识库
2. 查不到时用 web_search 搜索
3. 涉及建筑位置用 search_building
4. 涉及宿舍/食堂/招生用对应工具
5. 依赖工具结果回答，不编造
6. 不知道就承认不知道

回答格式要求：
- 关键信息用 **加粗** 突出
- 并列信息用列表展示
- 涉及费用、对比、多条目信息时用表格
- 需要给出温馨提示时用 > 引用格式
- 保持回答简洁自然
"""


def build_agent(tools: list):
    """创建 LangGraph Agent，工具直接执行（无需人工审批），返回 (app, checkpointer)"""
    from langgraph.prebuilt import ToolNode
    llm = _get_llm().bind_tools(tools)

    def call_model(state: MessagesState) -> dict:
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [llm.invoke(msgs)]}

    def should_continue(state: MessagesState) -> Literal["tools", END]:
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("call_model", call_model)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "call_model")
    graph.add_conditional_edges("call_model", should_continue)
    graph.add_edge("tools", "call_model")

    checkpointer = MemorySaver()

    app = graph.compile(checkpointer=checkpointer)
    return app, checkpointer


def stream_agent(app, user_input: str, thread_id: str):
    """流式运行，返回 async generator of events"""
    return app.astream_events(
        {"messages": [HumanMessage(content=user_input)]},
        config={"configurable": {"thread_id": thread_id}},
        version="v2",
    )

