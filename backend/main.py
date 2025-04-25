
from backend_v2.core.agents.orchestrator import process_request

if __name__ == "__main__":
    task = "What is 22 times 5, and why might that number be useful?"
    final_output = process_request(task)
    print(f"\n✅ Final Output:\n{final_output}")
