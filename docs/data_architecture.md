# 数据架构文档

> 负责人员: 开发人员②号
> 最后更新: 2026-06-30

---

## 1. 项目数据流总览

```
用户输入
  │
  ▼
┌─────────────────┐     ┌──────────────────┐
│  FastAPI Server  │────▶│  LangGraph Agent  │
│  (server/main.py)│     │  (agent/lang_agent.py)
└────────┬────────┘     └────────┬─────────┘
         │                       │
         │           ┌───────────┼───────────┐
         │           ▼           ▼           ▼
         │   ┌────────────┐ ┌────────┐ ┌──────────┐
         │   │ Campus工具  │ │ 网络搜索 │ │  RAG知识库 │
         │   │(campus_tools)│ │(web_search)│ │(rag.py)  │
         │   └────────────┘ └────────┘ └────┬─────┘
         │                                  │
         │                                  ▼
         │                         ┌──────────────┐
         │                         │  Chroma 向量库 │
         │                         │(.chroma_db/) │
         │                         └──────────────┘
         │
         ▼
┌─────────────────┐
│  反馈系统         │
│ (feedback.py)   │
│  → feedback.db  │
└─────────────────┘
```

---

## 2. 数据存储组件

### 2.1 知识文档 (knowledge/)

| 项目 | 说明 |
|------|------|
| 路径 | `knowledge/*.md` |
| 格式 | Markdown (UTF-8) |
| 用途 | RAG 的原始语料，存储学校/校园领域知识 |
| 当前文件 | `ai_agent_guide.md` — AI Agent 开发入门指南 |
| 处理方式 | DirectoryLoader 加载 → TextSplitter 切片 → Embedding → Chroma 入库 |

**扩展规则**: 所有 `.md` 文件放入 `knowledge/` 目录后，重启索引即可自动纳入 RAG。

### 2.2 Chroma 向量数据库 (.chroma_db/)

| 项目 | 说明 |
|------|------|
| 路径 | `.chroma_db/` (项目根目录) |
| 引擎 | Chroma (via langchain_community.vectorstores) |
| Embedding 模型 | BAAI/bge-small-zh-v1.5 (CPU, normalize_embeddings=True) |
| 存储内容 | 文档切片的向量 + 原始文本 + metadata (source路径) |
| 索引构建 | `CampusRAG.build_index()` |
| 检索方式 | `similarity_search(query, k=3)` → 返回 top-k 文档片段 |

**元数据 Schema**:
```python
{
    "source": str,   # 文档原始路径，如 "knowledge/ai_agent_guide.md"
}
```

### 2.3 反馈数据库 (feedback.db)

| 项目 | 说明 |
|------|------|
| 路径 | `feedback.db` |
| 引擎 | SQLite |
| 用途 | 记录 Agent 无法回答的问题，供人工补充知识 |

**表结构: `pending_questions`**

| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK AUTOINCREMENT | 主键 |
| question | TEXT NOT NULL | 用户问题 |
| agent_answer | TEXT | Agent 当时的回答 |
| session_id | TEXT | 会话 ID |
| reason | TEXT DEFAULT 'auto' | 标记原因: 'auto' / 'manual' |
| status | TEXT DEFAULT 'pending' | 状态: 'pending' / 'answered' |
| created_at | DATETIME DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| answered_at | DATETIME | 补充回答时间 |
| supplemented | TEXT | 人工补充的知识答案 |

**自动检测逻辑** (`detect_poor_answer`): 当 Agent 回答中包含以下关键词之一时，自动记录为待补充问题:
- "请在 campus_tools.py 中补充" / "请补充"
- "未找到相关信息" / "未找到相关结果"
- "知识库为空" / "搜索失败"
- "抱歉" / "无法回答" / "没有相关信息"

### 2.4 会话状态 (内存)

| 项目 | 说明 |
|------|------|
| 存储位置 | `server.main.sessions` (Python dict, 内存) |
| 键 | `session_id` (uuid hex[:12]) |
| 值 | `{"app": CompiledStateGraph, "cp": MemorySaver}` |
| 生命周期 | 服务重启后丢失 |

### 2.5 Agent 记忆数据库 (agent_memory.db)

| 项目 | 说明 |
|------|------|
| 路径 | `agent_memory.db` |
| 用途 | Agent 长期记忆存储 |
| 备注 | 由 agent 核心模块管理，当前实现待补充 |

---

## 3. 核心数据结构

### 3.1 文档切片 (Document Chunk)

```python
Document(
    page_content=str,        # 切片文本内容
    metadata={"source": str} # 源文件路径
)
```

### 3.2 Agent 消息 (MessagesState)

```python
# langgraph.graph.MessagesState
{
    "messages": [
        SystemMessage(content="系统提示词"),
        HumanMessage(content="用户输入"),
        AIMessage(content="Agent回复" [, tool_calls=[...]]),
        ToolMessage(content="工具返回结果"),
    ]
}
```

### 3.3 SSE 事件流格式

```javascript
// 服务端推送 (text/event-stream)
{"type":"token","content":"正在查询..."}
{"type":"tool_start","tool":"search_knowledge","input":"..."}
{"type":"tool_end","output":"..."}
{"type":"done"}
{"type":"error","content":"error message"}
```

---

## 4. Embedding 配置

| 参数 | 值 |
|------|-----|
| 模型 | BAAI/bge-small-zh-v1.5 |
| 设备 | cpu |
| 向量维度 | 512 |
| 归一化 | normalize_embeddings=True |
| 距离度量 | Cosine Similarity |

---

## 5. 环境变量

| 变量 | 说明 | 当前值 |
|------|------|--------|
| OPENAI_API_KEY | API 密钥 | sk-xxx (DeepSeek) |
| OPENAI_BASE_URL | API 端点 | https://api.deepseek.com/v1 |
| OPENAI_MODEL | 模型名称 | deepseek-chat |
| SERVER_PORT | 服务端口 | 8000 |

---

## 6. 数据流向时序

```
[用户] --问题--> [FastAPI SSE] --消息--> [LangGraph Agent]
                                              │
                    ┌─────────────────────────┼─────────────────────┐
                    ▼                         ▼                     ▼
            [search_knowledge]         [campus_tools]        [web_search]
                    │                         │                     │
                    ▼                         ▼                     ▼
            [Chroma 向量检索]          [内置数据字典]          [Bing 搜索]
                    │                         │                     │
                    └─────────────────────────┼─────────────────────┘
                                              ▼
                                       [LLM 生成回答]
                                              │
                                       [检测回答质量]
                                              │
                                     ┌────────┴────────┐
                                     ▼                  ▼
                                [质量合格]           [质量不合格]
                                → 返回流式结果     → 写入 feedback.db
                                                    → 返回流式结果
```

---

## 7. 文件清单

| 文件 | 角色 | 数据职责 |
|------|------|----------|
| `server/main.py` | API 层 | 请求入口、SSE 推送、反馈提交 |
| `agent/lang_agent.py` | Agent 编排 | 消息状态管理、工具路由 |
| `agent/rag.py` | RAG 引擎 | 文档加载、切片、向量化、检索 |
| `agent/tools/campus_tools.py` | 领域工具 | 校园信息数据字典 |
| `agent/feedback.py` | 反馈系统 | 问题记录、补充答案、质量检测 |
| `knowledge/*.md` | 知识语料 | RAG 原始文档 |
| `.chroma_db/` | 向量存储 | 持久化向量索引 |
| `feedback.db` | 反馈存储 | 待补充问题 |
| `.env` | 环境配置 | API 密钥、模型、端口 |

---

*本文档由开发人员②号维护，随项目迭代同步更新。*
