import os
import warnings
from pathlib import Path
from typing import Optional

from agent.config import settings

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"  # 模型已缓存，避免联网检查超时


class CampusRAG:
    """基于 FAISS + bge-small-zh-v1.5 的 RAG 引擎"""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = str(knowledge_dir or settings.knowledge_dir)
        self.vector_dir = settings.vector_db_dir
        self.db: Optional[object] = None
        self.embeddings: Optional[object] = None
        self._embedding_error: Optional[str] = None

    # ------------------------------------------------------------------
    # Embedding 模型初始化（带 try/except 保护）
    # ------------------------------------------------------------------
    def _init_embeddings(self):
        if self.embeddings is not None:
            return self.embeddings
        if self._embedding_error is not None:
            return None
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings

            self.embeddings = HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-zh-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            return self.embeddings
        except Exception as e:
            self._embedding_error = str(e)
            warnings.warn(f"Embedding 模型初始化失败: {e}")
            return None

    # ------------------------------------------------------------------
    # 构建索引：加载 → 切片 → Embedding → FAISS 持久化
    # ------------------------------------------------------------------
    def build_index(self) -> int:
        # 1) 加载文档
        from langchain_community.document_loaders import DirectoryLoader, TextLoader

        loader = DirectoryLoader(
            self.knowledge_dir,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
            use_multithreading=False,
        )
        docs = loader.load()
        if not docs:
            return 0

        # 2) 切片
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50
        )
        chunks = splitter.split_documents(docs)
        if not chunks:
            return 0

        # 3) Embedding 模型
        emb = self._init_embeddings()
        if emb is None:
            # 模型加载失败，尝试已有索引
            if os.path.isdir(self.vector_dir) and self.load_existing():
                cnt = (
                    self.db.index.ntotal
                    if self.db is not None
                    else 0
                )
                return cnt
            raise RuntimeError(
                "Embedding 模型初始化失败（torch DLL 可能无法加载）\n"
                f"错误: {self._embedding_error}\n"
                "且没有可用的已有索引。\n"
                "建议: 1) 重新安装 torch (pip install --force-reinstall torch)\n"
                "      2) 或先确保模型能正确下载并加载"
            )

        # 4) 写入 FAISS（并持久化）
        from langchain_community.vectorstores import FAISS

        os.makedirs(self.vector_dir, exist_ok=True)
        self.db = FAISS.from_documents(
            documents=chunks,
            embedding=emb,
        )
        self.db.save_local(self.vector_dir)
        return len(chunks)

    # ------------------------------------------------------------------
    # 加载已有持久化索引
    # ------------------------------------------------------------------
    def load_existing(self) -> bool:
        if not os.path.isdir(self.vector_dir):
            return False
        emb = self._init_embeddings()
        if emb is None:
            warnings.warn("Embedding 模型不可用，无法加载已有索引查询")
            return False
        try:
            from langchain_community.vectorstores import FAISS

            self.db = FAISS.load_local(
                folder_path=self.vector_dir,
                embeddings=emb,
                allow_dangerous_deserialization=True,
            )
            # 验证索引有数据
            _ = self.db.index.ntotal
            return True
        except Exception as e:
            warnings.warn(f"加载已有索引失败: {e}")
            self.db = None
            return False

    # ------------------------------------------------------------------
    # 检索
    # ------------------------------------------------------------------
    def search(self, query: str, k: int = 3) -> str:
        if self.db is None:
            if os.path.isdir(self.vector_dir):
                self.load_existing()
        if self.db is None:
            return "知识库未初始化，请先调用 rebuild_index()"

        try:
            results = self.db.similarity_search(query, k=k)
        except Exception as e:
            return f"搜索失败: {e}"

        if not results:
            return "未找到相关信息"

        parts = []
        for i, doc in enumerate(results, 1):
            src = Path(doc.metadata.get("source", "unknown")).name
            txt = doc.page_content[:400]
            parts.append(f"[{i}] {src}\n{txt}")
        return "\n\n".join(parts)


# ------------------------------------------------------------------
# 全局单例
# ------------------------------------------------------------------
_RAG: Optional[CampusRAG] = None


def get_rag() -> CampusRAG:
    global _RAG
    if _RAG is None:
        _RAG = CampusRAG()
    return _RAG


def rebuild_index() -> int:
    global _RAG
    _RAG = CampusRAG()
    return _RAG.build_index()
