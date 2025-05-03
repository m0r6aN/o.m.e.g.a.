# tools/web_search/tool.py
import os
import requests
import redis
import json
from dotenv import load_dotenv
from omega.core.registerable_mcp_tool import RegisterableMCPTool

load_dotenv()

# Redis configuration
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True
)
cache_ttl = 60 * 60 * 6  # 6 hours
redis_channel = os.getenv("REDIS_CHANNEL_WEB_SEARCH", "web_search_channel")

def publish_event(query: str, source: str = "search", cached: bool = False):
    """Publish web search event to Redis channel"""
    payload = json.dumps({
        "event": "web_search_performed",
        "query": query,
        "cached": cached,
        "source": source,
    })
    redis_client.publish(redis_channel, payload)

def web_search(query: str, num_results: int = 3) -> str:
    """
    Perform a real-time web search using Serper.dev.
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 3)
        
    Returns:
        Formatted search results
    """
    query = query.strip()
    cache_key = f"web_search:{query.lower()}"
    
    # Check cache first
    cached = redis_client.get(cache_key)
    if cached:
        publish_event(query, cached=True)
        return f"(Cached)\n{cached}"
    
    # Get API key
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "Web search failed: Missing SERPER_API_KEY"

    # Perform search
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query}
    
    try:
        res = requests.post("https://google.serper.dev/search", json=payload, headers=headers)
        data = res.json()
        results = data.get("organic", [])
        
        if not results:
            return "No search results found."

        # Format results
        top_results = "\n".join(
            f"- [{r['title']}]({r['link']}) — {r.get('snippet', '')}"
            for r in results[:num_results]
        )
        full_result = f"Top search results for '{query}':\n{top_results}"
        
        # Cache results
        redis_client.setex(cache_key, cache_ttl, full_result)
        publish_event(query, cached=False)
        
        return full_result
    
    except Exception as e:
        return f"Search error: {str(e)}"

# Create the tool
tool = RegisterableMCPTool(
    tool_id="web_search",
    name="Web Search Tool",
    description="Performs real-time web searches using Serper.dev API",
    version="1.0.0",
    tags=["search", "web", "information"]
)

# Add the web search function
tool.add_tool(
    name="search",
    description="Perform a web search",
    func=web_search,
    parameters={
        "query": {
            "type": "string", 
            "description": "Search query"
        },
        "num_results": {
            "type": "integer", 
            "description": "Number of results to return",
            "required": False,
            "default": 3
        }
    }
)

# Run the tool server
if __name__ == "__main__":
    tool.run()