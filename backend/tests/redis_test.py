import os, json, redis
from dotenv import load_dotenv

load_dotenv()

# 👉 make sure you hit the same instance EchoAgent uses
r = redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True)

payload = {
    "type": "task",
    "task": {
    "workflow_id": "wf_test_001",
    "raw_prompt": "Use SQL to analyze product returns and identify top issues.",
    "target_agent": "prompt_optimizer"
  }
}

r.publish("responses_channel", json.dumps(payload))
print("✅ Published to responses_channel")
