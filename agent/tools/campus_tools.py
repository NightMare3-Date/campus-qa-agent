"""校园知识问答专用工具集"""
from langchain_core.tools import tool
from agent.rag import get_rag
NL = chr(10)


@tool
def search_knowledge(query: str) -> str:
    """从知识库中搜索校园相关信息（宿舍、教学楼、招生、食堂等）"""
    try:
        rag = get_rag()
        return rag.search(query)
    except Exception as e:
        return f"搜索失败: {e}"



@tool
def web_search(query: str) -> str:
    """搜索互联网获取学校公开信息"""
    import httpx
    from bs4 import BeautifulSoup
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            r = c.get("https://www.bing.com/search", params={"q": query}, headers={"User-Agent": "Mozilla/5.0"})
            s = BeautifulSoup(r.text, "html.parser")
            items = []
            for x in s.select("li.b_algo")[:3]:
                t = x.select_one("h2 a")
                p = x.select_one(".b_caption p")
                items.append("- " + (t.get_text(strip=True) if t else "") + NL + "  " + (p.get_text(strip=True) if p else ""))
            return "搜索结果:" + NL + NL.join(items) if items else "未找到"
    except Exception as e:
        return f"搜索失败: {e}"
