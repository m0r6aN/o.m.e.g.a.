# /tests/inject_task.py

import redis
from omega.core.models import TaskEnvelope, TaskHeader, TaskCore

# Connect to the Redis container
r = redis.Redis(host='localhost', port=6379, db=0)

# The agent's dedicated inbox stream key
stream_key = "agent.mock_agent_001.inbox"

# Create the task envelope, same as before
envelope = TaskEnvelope(
    header=TaskHeader(conversation_id="redis-test-convo", sender="injector-script"),
    task=TaskCore(id="redis-task-001", name="Verify Redis C&C", description="Verify Redis C&C")
)

# The payload MUST be a dictionary with a "payload" key
message = {"payload": envelope.model_dump_json()}

# Add the message to the stream
r.xadd(stream_key, message)

print(f"Task {envelope.task.id} injected into stream '{stream_key}'")