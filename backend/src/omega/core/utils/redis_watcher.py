import redis
import os

CHANNELS = [
    os.getenv("REDIS_CHANNEL_PROMPT", "prompt_channel"),
    os.getenv("REDIS_CHANNEL_PLAN", "workflow_plan_channel"),
    os.getenv("REDIS_CHANNEL_DISPATCH", "workflow_dispatch_channel"),
    os.getenv("REDIS_CHANNEL_OVERLOCK", "overclock_dispatch_channel")
]

r = redis.Redis(host="localhost", port=6379, db=0)
pubsub = r.pubsub()

def print_message(message):
    if message['type'] == 'message':
        print(f"\n📡 [{message['channel'].decode()}] {message['data'].decode()}")

for channel in CHANNELS:
    pubsub.subscribe(**{channel: print_message})

print("👁️  Redis Watcher online. Monitoring Z.E.R.O. channels...")
pubsub.run_in_thread(sleep_time=0.1)
