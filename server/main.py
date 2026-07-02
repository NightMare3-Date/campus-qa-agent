"""FastAPI with SSE"""
import sys, os, json, uuid, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
load_dotenv(override=True)
from agent.tools import TOOLS
from agent.lang_agent import build_agent, stream_agent
from agent.feedback import add_pending, get_pending, mark_answered, count_pending, detect_poor_answer

sessions = {}
app = FastAPI()

async def _stream(sid, text):
    import json as _json
    if sid not in sessions:
        a, c = build_agent(TOOLS)
        sessions[sid] = {"app": a, "cp": c}
    ag = sessions[sid]["app"]
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
            add_pending(text, full, sid, "auto")
        yield "data: " + json.dumps({"type":"done"}) + "\n\n"
    except Exception as e:
        d = json.dumps({"type":"error","content":str(e)}, ensure_ascii=False)
        yield "data: " + d + "\n\n"


@app.get("/api/chat/stream")
async def chat_stream(session_id="default", message=""):
    if not message: raise HTTPException(400)
    return StreamingResponse(_stream(session_id, message), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@app.post("/api/session/new")
async def new_session():
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
async def submit_feedback(session_id: str = "", question: str = "", answer: str = ""):
    if question:
        add_pending(question, answer, session_id, "manual")
    return {"ok": True}

@app.get("/api/admin/pending")
async def admin_pending():
    return {"questions": get_pending()}

@app.post("/api/admin/mark")
async def admin_mark(id: int = 0, supplemented: str = ""):
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
    port = int(os.getenv("SERVER_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


