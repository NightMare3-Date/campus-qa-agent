"""FastAPI with SSE"""
import sys, os, json, uuid, re
from loguru import logger
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
load_dotenv(override=True)
from agent.config import settings
from agent.tools import TOOLS
from agent.lang_agent import build_agent, stream_agent
from agent.feedback import add_pending, get_pending, mark_answered, count_pending, detect_poor_answer

os.makedirs("logs", exist_ok=True)
logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>", level="DEBUG", colorize=True)
logger.add("logs/server_{time:YYYY-MM-DD}.log", rotation="1 day", retention="15 days", level="INFO", encoding="utf-8")

sessions = {}


def startup_checks():
    """服务启动自检"""
    passed = True
    
    # 1. 检查 API Key
    if not settings.openai_api_key or settings.openai_api_key == "your_api_key_here":
        logger.error("OPENAI_API_KEY 未配置，请在 .env 中设置")
        passed = False
    
    # 2. 检查知识目录
    from pathlib import Path
    kd = Path(settings.knowledge_dir)
    if not kd.exists():
        logger.warning("知识目录不存在: {}，请创建并放入 Markdown 文档", kd)
    else:
        md_files = list(kd.glob("**/*.md"))
        logger.info("知识目录: {} ({} 个文档)", kd, len(md_files))
    
    # 3. 检查向量索引
    vd = Path(settings.vector_db_dir)
    if vd.exists() and (vd / "index.faiss").exists():
        logger.info("向量索引已存在: {}", vd)
    else:
        logger.warning("向量索引不存在，首次查询时会自动构建")
    
    # 4. 检查日志目录
    os.makedirs("logs", exist_ok=True)
    
    if passed:
        logger.info("启动自检通过")
    else:
        logger.error("启动自检未通过，请修复上述错误后重启")
    
    return passed


app = FastAPI()


@app.on_event("startup")
async def on_startup():
    if not startup_checks():
        import sys
        sys.exit(1)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: {} {}", request.url, exc)
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def _stream(sid, text):
    import json as _json
    if sid not in sessions:
        a, c = build_agent(TOOLS)
        sessions[sid] = {"app": a, "cp": c}
    ag = sessions[sid]["app"]
    logger.info("User query: {}", text)
    try:
        async for ev in stream_agent(ag, text, sid):
            k = ev.get("event", "")
            if k == "on_chain_stream":
                chunk = ev.get("data", {}).get("chunk", {})
                if isinstance(chunk, dict):
                    msgs = chunk.get("messages", [])
                    if msgs:
                        last = msgs[-1]
                        msg_type = getattr(last, "type", "")
                        is_tc = getattr(last, "tool_calls", None)
                        if msg_type != "tool" and hasattr(last, "content") and last.content and not is_tc:
                            c = last.content
                            d = json.dumps({"type":"token","content":c}, ensure_ascii=False)
                            yield "data: " + d + "\n\n"
            elif k == "on_tool_start":
                inp = str(ev.get("data", {}).get("input", ""))
                tn = ev.get("name", "?")
                logger.info("Tool called: {} input={}", tn, inp[:100])
                d = json.dumps({"type":"tool_start","tool":tn,"input":inp[:200]}, ensure_ascii=False)
                yield "data: " + d + "\n\n"
            elif k == "on_tool_end":
                out = str(ev.get("data", {}).get("output", ""))
                d = json.dumps({"type":"tool_end","output":out[:500]}, ensure_ascii=False)
                yield "data: " + d + "\n\n"
        full = ""
        try:
            state = ag.get_state({"configurable":{"thread_id":sid}})
            for msg in reversed(state.values.get("messages",[])):
                if hasattr(msg, "content") and msg.content:
                    full = msg.content
                    break
        except Exception:
            pass
        if full and detect_poor_answer(text, full):
            logger.warning("Poor answer detected: q={}", text)
            add_pending(text, full, sid, "auto")
        yield "data: " + json.dumps({"type":"done"}) + "\n\n"
    except Exception as e:
        logger.exception("Stream error: {}", e)
        d = json.dumps({"type":"error","content":str(e)}, ensure_ascii=False)
        yield "data: " + d + "\n\n"


@app.get("/api/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, session_id="default", message=""):
    if not message: raise HTTPException(400)
    return StreamingResponse(_stream(session_id, message), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@app.post("/api/session/new")
@limiter.limit("30/minute")
async def new_session(request: Request):
    sid = uuid.uuid4().hex[:12]
    a, c = build_agent(TOOLS)
    sessions[sid] = {"app": a, "cp": c}
    return {"session_id": sid}

@app.get("/api/tools")
async def list_tools():
    return {"tools": [{"name": t.name} for t in TOOLS]}

@app.get("/")
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"), media_type="text/html; charset=utf-8")

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/favicon.ico")
async def favicon():
    from fastapi.responses import Response
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#3b82f6"/><text x="16" y="22" text-anchor="middle" fill="white" font-size="18" font-family="Arial">AI</text></svg>'
    return Response(content=svg, media_type="image/svg+xml")

@app.post("/api/feedback")
@limiter.limit("20/minute")
async def submit_feedback(request: Request, session_id: str = "", question: str = "", answer: str = ""):
    if question:
        add_pending(question, answer, session_id, "manual")
    return {"ok": True}

@app.get("/api/admin/pending")
@limiter.limit("30/minute")
async def admin_pending(request: Request):
    return {"questions": get_pending()}

@app.post("/api/admin/mark")
@limiter.limit("30/minute")
async def admin_mark(request: Request, id: int = 0, supplemented: str = ""):
    mark_answered(id, supplemented)
    return {"ok": True}

@app.get("/api/admin/count")
async def admin_count():
    return {"count": count_pending()}

@app.get("/admin")
async def admin_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "admin.html"), media_type="text/html; charset=utf-8")


if __name__ == "__main__":
    import uvicorn
    port = settings.server_port
    uvicorn.run(app, host="0.0.0.0", port=port)
