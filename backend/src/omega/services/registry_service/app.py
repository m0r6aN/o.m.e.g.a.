from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis
import json
import os

app = FastAPI()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

class Registration(BaseModel):
    name: str
    endpoint: str
    type: str  # "tool" or "agent"

@app.post("/register")
async def register(registration: Registration):
    key = f"registry:{registration.name}"
    await r.set(key, registration.json(), ex=60)  # expire in 60 sec unless refreshed
    return {"message": "Registered successfully."}

@app.get("/find")
async def find(name: str):
    key = f"registry:{name}"
    data = await r.get(key)
    if not data:
        raise HTTPException(status_code=404, detail="Not found.")
    return json.loads(data)

@app.get("/list")
async def list_all():
    keys = await r.keys("registry:*")
    results = []
    for key in keys:
        data = await r.get(key)
        results.append(json.loads(data))
    return results