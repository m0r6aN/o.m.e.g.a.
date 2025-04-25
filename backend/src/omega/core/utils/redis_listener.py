import redis
import os
import json

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True
)

CHANNELS = [
    os.getenv("REDIS_CHANNEL_WEB_SEARCH", "web_search_channel"),
    os.getenv("REDIS_CHANNEL_MOD", "moderation_channel"),
    os.getenv("REDIS_CHANNEL_RES", "responses_channel"),
    os.getenv("REDIS_CHANNEL_ARB", "arbitration_channel"),
]

pubsub = redis_client.pubsub()
pubsub.subscribe(*CHANNELS)

print(f"🔊 Listening for events on Redis channels: {', '.join(CHANNELS)}")

for message in pubsub.listen():
    if message["type"] != "message":
        continue
    try:
        channel = message["channel"]
        data = json.loads(message["data"])
        print(f"📡 [{channel}] {data['event']}: {data}")
    except Exception as e:
        print(f"⚠️ Error parsing message: {e}")
