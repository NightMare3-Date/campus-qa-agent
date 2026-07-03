# 🏫 校园知识问答 Agent

基于 LangGraph + RAG 的智能校园问答助手，支持向量检索本地知识库，实时流式回答。

---

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [Docker 部署](#Docker-部署)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [详细配置说明](#详细配置说明)
- [项目结构](#项目结构)
- [知识文档编写指南](#知识文档编写指南)
- [管理后台](#管理后台)
- [常见问题](#常见问题)

---

## 项目简介

本项目是一个面向校园场景的智能问答系统。用户可以用自然语言提问，Agent 自动判断从本地知识库（RAG 向量检索）或互联网搜索获取信息，生成带格式的回答。

**典型使用场景：**

- "宿舍水费怎么交？" → 从知识库检索宿舍指南文档并回答
- "计算机学院在哪栋楼？" → 从知识库检索教学楼信息
- "今年录取分数线多少？" → 从知识库检索招生数据

---

## 功能特性

| 特性 | 说明 |
|------|------|
| **智能 Agent 编排** | 基于 LangGraph 的 StateGraph，自动决策调用哪个工具（知识库 / 网页搜索） |
| **RAG 向量检索** | 基于 FAISS + bge-small-zh-v1.5 中文向量模型，支持语义匹配（"宿舍" ↔ "寝室"） |
| **流式响应（SSE）** | 实时输出回答内容，工具调用过程可视化 |
| **回答质量检测** | 自动判断 Agent 是否未能回答，记录到反馈数据库 |
| **管理后台** | Web 界面查看待补充问题，支持手动补充答案 |
| **Markdown 格式化** | 回答支持加粗、列表、表格、引用等格式 |
| **点赞/踩反馈** | 用户可对回答点赞或反馈"没帮到我"，支持补充说明 |
| **知识隔离** | 知识文档不上传到代码仓库，支持环境变量指向外部路径 |

---

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| 后端框架 | FastAPI + Uvicorn |
| Agent 编排 | LangGraph |
| 向量检索 | FAISS（langchain-community） |
| Embedding 模型 | BAAI/bge-small-zh-v1.5 |
| 大语言模型 | DeepSeek Chat（兼容 OpenAI API） |
| 前端 | 原生 HTML + JavaScript + marked.js（Markdown 渲染）|
| 数据存储 | SQLite |
| 网络请求 | httpx + BeautifulSoup4 |

---

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- 8GB 以上内存（首次运行需下载约 500MB 的向量模型）
- 稳定的网络连接（用于下载模型和调用 API）

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/campus-qa-agent.git
cd campus-qa-agent
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
# python3 -m venv venv
# source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements-lock.txt
```

### 4. 配置环境变量

```bash
# Windows
copy .env.example .env

# Linux / Mac
# cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥：

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
SERVER_PORT=8000
```

### 5. 准备知识文档

在 `knowledge/` 文件夹中放入 Markdown 格式的校园知识文档（参考 `knowledge/_template.md`）。

### 6. 启动服务

```bash
# 方式一：直接启动（开发调试用）
# Windows
start.bat

# Linux / Mac
# chmod +x start.sh
# ./start.sh

# 方式二：Docker 启动（生产部署用）
docker compose up -d
```

浏览器打开 http://localhost:8000

---

## Docker 部署

### 前提条件

- 安装 Docker Engine 20.10+ 和 Docker Compose v2+
- 确保 `.env` 文件已配置好 API Key

### 构建并启动

```bash
# 首次构建并后台启动
docker compose up -d

# 查看实时日志
docker compose logs -f

# 停止服务
docker compose down
```

### 数据持久化

- **知识文档**：宿主机的 `./knowledge/` 目录挂载到容器内 `/app/knowledge`
- **向量索引**：通过 Docker 命名卷 `chroma_data` 持久化在 `/app/chroma_db`
- **环境配置**：自动加载宿主机的 `.env` 文件

### healthcheck

服务每 30 秒自动健康检查，如果异常会自动重启容器。


## 详细配置说明

### 环境变量一览

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| OPENAI_API_KEY | ✅ | — | API 密钥 |
| OPENAI_BASE_URL | 否 | https://api.deepseek.com/v1 | API 端点地址 |
| OPENAI_MODEL | 否 | deepseek-chat | 模型名称 |
| SERVER_PORT | 否 | 8000 | 服务监听端口 |
| KNOWLEDGE_DIR | 否 | ./knowledge | 知识文档目录路径 |
| CHROMA_DB_DIR | 否 | C:/aiagent_chroma_db | 向量索引持久化路径 |

### 配置注意事项

**1. 编码问题（Windows 用户）**

- `.env` 文件请用 UTF-8 编码保存，不要使用 GBK
- 如果出现中文乱码，用记事本打开 → 另存为 → 编码选择 UTF-8

**2. 中文路径问题**

FAISS C++ 底层不支持包含中文字符的文件路径。`CHROMA_DB_DIR` 默认使用纯 ASCII 路径 `C:/aiagent_chroma_db`，通常无需修改。

**3. 首次启动慢**

首次需要下载 `bge-small-zh-v1.5` 模型（约 30MB），下载完成后缓存到本地。后续启动只需 3-5 秒。

---

## 项目结构

```
campus-qa-agent/
│
├── agent/                          # Agent 核心代码
│   ├── lang_agent.py               # Agent 编排（build_agent, stream_agent, SYSTEM_PROMPT）
│   ├── rag.py                      # RAG 引擎（build_index, search, get_rag）
│   ├── feedback.py                 # 质量检测与反馈（detect_poor_answer, add_pending）
│   └── tools/
│       ├── __init__.py             # 工具注册
│       └── campus_tools.py         # search_knowledge + web_search
│
├── server/                         # 服务端
│   ├── main.py                     # FastAPI 应用（SSE 流式聊天接口、管理接口）
│   └── static/
│       ├── index.html              # 聊天界面
│       └── admin.html              # 管理后台
│
├── knowledge/                      # 知识文档（私有，不上传 Git）
│   └── _template.md                # 文档格式模板
│
├── docs/                           # 技术文档
│   ├── data_architecture.md        # 数据架构说明
│   └── rag_chunking.md             # RAG 切割策略
│
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 忽略规则
├── requirements.in                   # 核心依赖（不锁版本，供参考）
├── requirements-lock.txt             # 锁定版本（精确依赖）
├── start.bat                       # Windows 启动脚本
├── start.sh                        # Linux 启动脚本
└── README.md                       # 本文件
```

---

## 知识文档编写指南

### 格式规范

使用 Markdown 格式，UTF-8 编码保存：

```markdown
# 文档标题
> 更新: 2026-07-01

---

## 章节一
具体内容...

## 章节二
具体内容...
```

### 注意事项

1. 每个 `##` 标题下的内容会被 RAG 作为一个检索单元
2. 一个文件一个主题（宿舍、食堂、招生分开）
3. 覆盖常见问题即可，不需要写长篇文章

---

## 管理后台

访问 http://localhost:8000/admin

- **自动检测**：Agent 回答中出现"抱歉"、"未找到"等关键词时自动记录
- **手动反馈**：用户点击"没帮到我"按钮手动提交
- **补充答案**：管理员在后台填写补充知识

---

## 常见问题

### Q: 启动报错 "utf-8 codec can't decode byte"

文件编码问题。确保所有 `.py` 和 `.md` 文件使用 UTF-8 编码保存。

### Q: 提示知识库未初始化

向量索引不存在，手动重建：

```bash
python -c "from agent.rag import rebuild_index; rebuild_index()"
```

### Q: Agent 回答是纯文本没有格式

检查浏览器控制台是否有 marked.js 加载错误。

### Q: 如何更换为 OpenAI GPT？

修改 `.env` 中的 `OPENAI_BASE_URL` 和 `OPENAI_MODEL`。

### Q: 知识文档改了但搜索还是旧内容

需要重建索引：重启服务或手动执行 `rebuild_index()`。

---

## License

MIT
