import aiohttp
import os

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry_service:8500")

async def register_self(name: str, endpoint: str, type_: str = "tool"):
    async with aiohttp.ClientSession() as session:
        await session.post(f"{REGISTRY_URL}/register", json={
            "name": name,
            "endpoint": endpoint,
            "type": type_
        })

async def find_tool(name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{REGISTRY_URL}/find", params={"name": name}) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return None