# /agents/code_generator/internal/llm_adapter.py

from fastapi import FastAPI, Request
from agents.code_generator.internal.llm_adapter import llm_adapter

app = FastAPI()

@app.post("/generate")
async def generate_code(request: Request):
    body = await request.json()
    prompt = body.get("prompt")

    if not prompt:
        return {"error": "Missing 'prompt' in request body"}

    try:
        result = llm_adapter.generate(prompt=prompt, task_type="coding")
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}
