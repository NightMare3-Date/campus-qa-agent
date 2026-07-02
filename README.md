# 🏫 校园知识问答 Agent

基于 LangGraph + RAG 的智能校园问答助手，支持向量检索本地知识库，实时流式回答。

## 功能特性

- **智能问答** — 基于 LangGraph 的 Agent 编排，自动判断调用知识库或网络搜索
- **RAG 知识库** — 基于 FAISS + bge-small-zh-v1.5 中文向量检索，支持语义匹配
- **流式响应** — 基于 SSE 的实时流式输出，工具调用过程可视化
- **反馈系统** — 自动检测回答质量，记录待补充问题到管理后台
- **知识隔离** — 知识文档本地私有，不上传到代码仓库

## 快速开始

### 环境要求

- Python 3.10+
- 8GB+ 内存（首次运行需下载 ~500MB 向量模型）

### 安装

`ash
# 克隆仓库
git clone https://github.com/你的用户名/campus-qa-agent.git
cd campus-qa-agent

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
`

### 配置

`ash
# 复制环境变量模板
cp .env.example .env
# Windows 用 copy 命令
# copy .env.example .env
`

编辑 .env，填入你的 API Key：

`
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
SERVER_PORT=8000
`

### 准备知识文档

在项目根目录创建 knowledge/ 文件夹，放入 Markdown 格式的校园知识文档（参考 knowledge/_template.md）。

### 启动

`ash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
`

浏览器打开 http://localhost:8000

## 项目结构

`
campus-qa-agent/
├── agent/                     # Agent 核心
│   ├── lang_agent.py          # LangGraph Agent 编排
│   ├── rag.py                 # RAG 向量检索引擎
│   ├── feedback.py            # 回答质量检测与反馈
│   └── tools/
│       ├── campus_tools.py    # 工具定义（search_knowledge, web_search）
│       └── __init__.py        # 工具注册
├── server/                    # 服务端
│   ├── main.py                # FastAPI + SSE 流式推送
│   └── static/
│       ├── index.html         # 聊天界面
│       └── admin.html         # 管理后台
├── docs/                      # 技术文档
├── .env.example               # 环境变量模板
├── .gitignore                 # Git 忽略规则
├── requirements.txt           # Python 依赖
├── start.bat                  # Windows 启动脚本
└── start.sh                   # Linux 启动脚本
`

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| OPENAI_API_KEY | API 密钥 | 必填 |
| OPENAI_BASE_URL | API 端点 | https://api.deepseek.com/v1 |
| OPENAI_MODEL | 模型名称 | deepseek-chat |
| SERVER_PORT | 服务端口 | 8000 |
| KNOWLEDGE_DIR | 知识文档路径（可选） | ./knowledge |
| CHROMA_DB_DIR | 向量索引路径（可选） | C:/aiagent_chroma_db |

## 技术栈

- **框架**: FastAPI + LangGraph + LangChain
- **向量检索**: FAISS + bge-small-zh-v1.5
- **模型**: DeepSeek Chat（兼容 OpenAI API）
- **前端**: 原生 HTML/JS + marked.js（Markdown 渲染）
- **数据存储**: SQLite（反馈系统）

## License

MIT
