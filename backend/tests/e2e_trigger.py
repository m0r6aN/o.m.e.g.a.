
import os
import json
import redis
import time

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

workflow_id = "wf_test_001"
channel = os.getenv("REDIS_CHANNEL_PROMPT", "prompt_channel")

message = {
    "type": "task",
    "task": {
        "workflow_id": workflow_id,
        "raw_prompt": "Use SQL to analyze product returns and identify top issues.",
        "target_agent": "prompt_optimizer"
    }
}

print(f"🚀 Sending prompt to {channel}...")
r.publish(channel, json.dumps(message))
print(f"✅ Published! Workflow ID: {workflow_id}")

# Listen for result on orchestrator_dispatch_channel
result_channel = os.getenv("REDIS_CHANNEL_ORCHESTRATE", "orchestrator_dispatch_channel")
print(f"🎧 Listening on {result_channel}... (Ctrl+C to stop)")

pubsub = r.pubsub()
pubsub.subscribe(result_channel)

try:
    for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
            if data.get("workflow_id") == workflow_id:
                print(f"📬 [{time.strftime('%X')}] Received response for {workflow_id}:")
                print(json.dumps(data, indent=2))
                break
        except Exception as e:
            print(f"⚠️ Error decoding message: {e}")
except KeyboardInterrupt:
    print("👋 Listener stopped.")
