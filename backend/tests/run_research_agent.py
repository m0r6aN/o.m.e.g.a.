from backend_v2.core.agents.openai_client import client
from backend_v2.services.mcp import check_for_tool_call, execute_tool
from backend_v2.core.agents.research_agent import create_research_agent
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

if __name__ == "__main__":
    agent = create_research_agent()

    # input_text = """
    # The Industrial Revolution was a period of major industrialization that took place during the late 1700s and early 1800s.
    # This period saw the mechanization of agriculture, textile manufacturing, and a revolution in power, including steamships and railroads.
    # These changes had a profound effect on socioeconomic and cultural conditions.
    # """
    
    prompt = task = "latest AI news"
    agent.receive(prompt)
    reply = agent.respond(client)
    print(f"\n🧠 Initial Reply:\n{reply}")

    tool_call = check_for_tool_call(reply)
    if tool_call:
        print("\n⚙️ MCP Intercepted Tool Call!")
        tool_result = execute_tool(tool_call)
        print(f"\n🛠️ Tool Result:\n{tool_result}")
        
        agent.receive(tool_result)
        final_reply = agent.respond(client)
        print(f"\n✅ Final Reply:\n{final_reply}")
