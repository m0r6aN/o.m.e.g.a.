import os
import requests
import redis
import json
from backend_v2.core.tools.tool_base import Tool
from backend_v2.core.utils.event_schema import format_event
from dotenv import load_dotenv

load_dotenv()

class WebSearchTool(Tool):
    name = "web_search"
    description = "Performs a real-time web search using Serper.dev."
    
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        self.cache_ttl = 60 * 60 * 6  # 6 hours
        self.channel = os.getenv("REDIS_CHANNEL_WEB_SEARCH", "web_search_channel")
        
    def publish_event(self, query: str, source: str = "search", cached: bool = False):
        payload = json.dumps({
            "event": "web_search_performed",
            "query": query,
            "cached": cached,
            "source": source,
        })
        self.redis.publish(self.channel, payload)

    def run(self, input_data: str) -> str:
        query = input_data.strip().lower()
        cached = self.redis.get(f"web_search:{query}")
        if cached:
            return f"(Cached)\n{cached}"
        
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return "Web search failed: Missing SERPER_API_KEY"

        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {"q": input_data}
        try:
            res = requests.post("https://google.serper.dev/search", json=payload, headers=headers)
            data = res.json()
            results = data.get("organic", [])
            if not results:
                return "No search results found."

            top_results = "\n".join(
                f"- [{r['title']}]({r['link']}) — {r.get('snippet', '')}"
                for r in results[:3]
            )
            full_result = f"Top search results for '{query}':\n{top_results}"
            self.redis.setex(f"web_search:{query}", self.cache_ttl, full_result)
            self.publish_event(query, cached=False)
            return full_result
        except Exception as e:
            return f"Search error: {str(e)}"
