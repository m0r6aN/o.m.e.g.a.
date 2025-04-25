import os, json, uuid, asyncio
from fastapi import Body, FastAPI
from pydantic import BaseModel
import redis.asyncio as redis

REDIS = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), decode_responses=True)
TASK_STREAM = "tasks"
RESULT_STREAM = "results"

class RunRequest(BaseModel):
    text: str
    target_lang: str = "es"

app = FastAPI(title="Orchestrator – MCP + A2A Demo")

@app.post("/run")
async def run(req: RunRequest = Body(...)):
    task_id = str(uuid.uuid4())
    await REDIS.xadd(TASK_STREAM, {
        "task_id": task_id,
        "type": "summarize",
        "payload": req.text,
        "reply_to": RESULT_STREAM,
        "follow_up": json.dumps({
            "type": "translate",
            "target_lang": req.target_lang
        })
    })
    # Wait for final result
    while True:
        res = await REDIS.xread({RESULT_STREAM: 0}, count=1, block=0)
        for _, entries in res:
            for _, fields in entries:
                if fields.get("task_id") == task_id and fields.get("stage") == "done":
                    return {"summary_and_translation": fields["result"]}
                
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orchestrator:app", host="0.0.0.0", port=8000, reload=False)
