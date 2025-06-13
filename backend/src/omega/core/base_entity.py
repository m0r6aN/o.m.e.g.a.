# /omega/core/base_entity.py

import os
import asyncio
import httpx  # Standardize on httpx for async requests
from fastapi import FastAPI
from contextlib import asynccontextmanager

class OmegaEntity:
    """The foundational class for all networked components in the OMEGA ecosystem."""

    def __init__(self, entity_id: str, entity_type: str, port: int, mcp_port: int = None):
        self.id = entity_id
        self.type = entity_type
        self.host = os.getenv("DOCKER_SERVICE_NAME", entity_id) # Use Docker's DNS
        self.port = port
        self.mcp_port = mcp_port
        
        self.registry_url = os.getenv("REGISTRY_URL")
        self.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", 30))
        self.app = FastAPI(lifespan=self._lifespan)
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self._heartbeat_task = None
        
        self._setup_base_routes()

    def _setup_base_routes(self):
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "id": self.id, "type": self.type}

    def get_registration_payload(self) -> dict:
        """Subclasses will override this to provide their specific details."""
        raise NotImplementedError("Subclasses must implement get_registration_payload")

    async def _register(self):
        payload = self.get_registration_payload()
        try:
            resp = await self.http_client.post(f"{self.registry_url}/registry/register", json=payload)
            if resp.status_code == 200:
                print(f"✅ {self.id} registered successfully.")
                return True
            print(f"❌ Registration failed for {self.id}: {resp.status_code} - {resp.text}")
            return False
        except httpx.RequestError as e:
            print(f"❌ Registry connection failed for {self.id}: {e}")
            return False

    async def _unregister(self):
        # Implementation to unregister on shutdown
        pass # Add the DELETE call here

    async def _heartbeat_loop(self):
        """Pure asyncio heartbeat. No more mixing threads."""
        while True:
            try:
                await self.http_client.post(f"{self.registry_url}/registry/heartbeat", json={"id": self.id})
            except httpx.RequestError:
                print(f"⚠️ Heartbeat failed for {self.id}. Will retry.")
            await asyncio.sleep(self.heartbeat_interval)

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        # Startup
        if await self._register():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            print(f"💓 Heartbeat started for {self.id}")
        
        yield  # The application runs
        
        # Shutdown
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        await self._unregister()
        await self.http_client.aclose()
        print(f"🛑 {self.id} shutdown complete.")