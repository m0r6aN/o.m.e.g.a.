import os, asyncio, redis.asyncio as redis
from googletrans import Translator

REDIS = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), decode_responses=True)
TASK_STREAM = "tasks"
RESULT_STREAM = "results"
translator = Translator()

# googletrans v4.x is actually *async*—so we just await it directly.
async def translate(text: str, target_lang: str) -> str:
    trans = await translator.translate(text, dest=target_lang, src="en")
    return trans.text

async def main():
    last_id = "$"
    while True:
        res = await REDIS.xread({TASK_STREAM: last_id}, block=0)
        for _, entries in res:
            for msg_id, fields in entries:
                last_id = msg_id
                if fields.get("type") != "translate":
                    continue
                result = await translate(fields["payload"], fields["target_lang"])
                await REDIS.xadd(fields["reply_to"], {
                    "task_id": fields["task_id"],
                    "stage": "done",
                    "result": result
                })

asyncio.run(main())