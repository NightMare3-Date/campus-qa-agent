import os, sqlite3, json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feedback.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            agent_answer TEXT,
            session_id TEXT,
            reason TEXT DEFAULT 'auto',
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            answered_at DATETIME,
            supplemented TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_pending(question: str, agent_answer: str = "", session_id: str = "", reason: str = "auto"):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO pending_questions (question, agent_answer, session_id, reason) VALUES (?, ?, ?, ?)",
        (question, agent_answer, session_id, reason)
    )
    conn.commit()
    conn.close()

def get_pending(limit: int = 50):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, question, agent_answer, reason, status, created_at FROM pending_questions WHERE status='pending' ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"id": r[0], "question": r[1], "agent_answer": r[2], "reason": r[3], "status": r[4], "created_at": r[5]} for r in rows]

def mark_answered(question_id: int, supplemented: str = ""):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE pending_questions SET status='answered', answered_at=datetime('now'), supplemented=? WHERE id=?",
        (supplemented, question_id)
    )
    conn.commit()
    conn.close()

def count_pending():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM pending_questions WHERE status='pending'").fetchone()[0]
    conn.close()
    return count

# Auto-detect: did the agent fail?
def detect_poor_answer(question: str, answer: str) -> bool:
    poor_phrases = [
        "请在 campus_tools.py 中补充",
        "请补充",
        "未找到相关信息",
        "知识库为空",
        "未找到相关结果",
        "搜索失败",
        "抱歉",
        "无法回答",
        "没有相关信息",
    ]
    return any(p in answer for p in poor_phrases)
