
from backend_v2.core.agents.openai_client import client
from backend_v2.core.agents.finance_agent import create_finance_agent
from backend_v2.services.mcp import check_for_tool_call, execute_tool

if __name__ == "__main__":
    agent = create_finance_agent()
    msg = "Can you check the account balance?"
    print(f"\n FinanceAgent Task: {msg}")
    agent.receive(msg)

    reply = agent.respond(client)
    print(f"\n Initial Reply:\n{reply}")

    tool_call = check_for_tool_call(reply)
    if tool_call:
        print("\n MCP Intercepted Tool Call!")
        tool_result = execute_tool(tool_call)
        print(f"\n Tool Result:\n{tool_result}")

        agent.receive(tool_result)
        final_reply = agent.respond(client)
        print(f"\n Final Reply:\n{final_reply}")
