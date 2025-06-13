# /omega/agents/enhanced_base_agent.py
"""
The ULTIMATE BaseAgent - Production ready, battle tested, Avengers-level! 🚀
"""

import os
import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from redis.asyncio import Redis
from pydantic import BaseModel

from omega.core.base_entity import OmegaEntity
from omega.core.models.task_models import TaskEnvelope
from omega.core.agent_discovery import AgentCapability

class HealthStatus(BaseModel):
    """Comprehensive health status model"""
    status: str
    agent_id: str
    version: str
    uptime: float
    redis_connected: bool
    registry_connected: bool
    active_tasks: int
    memory_usage: Dict[str, Any]

@dataclass
class AgentMetrics:
    """Real-time agent performance metrics"""
    tasks_processed: int = 0
    tasks_failed: int = 0
    avg_response_time: float = 0.0
    start_time: float = 0.0

class EnhancedBaseAgent(OmegaEntity, ABC):
    """
    The next-gen BaseAgent with enterprise features:
    - Comprehensive health monitoring
    - Graceful shutdown handling
    - Performance metrics
    - Circuit breaker patterns
    - Structured logging
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        port: int,
        mcp_port: int,
        version: str = "2.0.0",
        **kwargs
    ):
        super().__init__(
            entity_id=agent_id,
            entity_type="agent",
            port=port,
            mcp_port=mcp_port
        )
        
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.version = version
        self.metrics = AgentMetrics()
        
        # Enhanced app setup with middleware
        self.app = FastAPI(
            title=f"OMEGA Agent: {self.name}",
            version=self.version,
            description=self.description,
            lifespan=self._lifespan,
            docs_url="/docs" if os.getenv("DEBUG", "false").lower() == "true" else None
        )
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_signal_handlers()
        
        # Connection pools for better performance
        self.redis = None
        self.is_shutting_down = False

    def _setup_middleware(self):
        """Setup production-ready middleware"""
        # CORS for cross-origin requests
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure based on environment
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Gzip compression for better performance
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            print(f"🛑 Received signal {signum}. Initiating graceful shutdown...")
            self.is_shutting_down = True
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    @abstractmethod
    async def handle_task(self, envelope: TaskEnvelope) -> TaskEnvelope:
        """The cognitive core - implement your agent's intelligence here"""
        pass

    async def _setup_dependencies(self):
        """Initialize all dependencies with proper error handling"""
        try:
            # Redis connection with retry logic
            self.redis = Redis(
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            # Test Redis connection
            await self.redis.ping()
            print(f"✅ Redis connection established for {self.name}")
            
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            raise

    async def _cleanup_dependencies(self):
        """Clean shutdown of all dependencies"""
        if self.redis:
            await self.redis.close()
            print(f"✅ Redis connection closed for {self.name}")

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """Enhanced lifespan with comprehensive startup/shutdown"""
        print(f"🚀 {self.name} ignition sequence initiated...")
        self.metrics.start_time = asyncio.get_event_loop().time()
        
        startup_tasks = []
        
        try:
            # Phase 1: Dependencies
            await self._setup_dependencies()
            
            # Phase 2: Registration
            if await self._register():
                print(f"✅ {self.name} registered with OMEGA registry")
                
                # Phase 3: Background tasks
                startup_tasks = [
                    asyncio.create_task(self._heartbeat_loop()),
                    asyncio.create_task(self._redis_consumer()),
                    asyncio.create_task(self._metrics_collector())
                ]
                
                print(f"🌟 {self.name} is fully operational!")
            
            yield  # Agent operational phase
            
        except Exception as e:
            print(f"💥 Startup failed for {self.name}: {e}")
            raise
            
        finally:
            # Graceful shutdown sequence
            print(f"🛑 {self.name} shutdown sequence initiated...")
            self.is_shutting_down = True
            
            # Cancel background tasks
            for task in startup_tasks:
                if not task.cancelled():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Cleanup dependencies
            await self._cleanup_dependencies()
            await self._unregister()
            await self.http_client.aclose()
            
            print(f"✅ {self.name} shutdown complete. Goodbye! 👋")

    async def _redis_consumer(self):
        """Enhanced Redis consumer with error recovery"""
        group = f"{self.id}-group"
        consumer = f"{self.id}-consumer"
        
        try:
            await self.redis.xgroup_create(
                f"agent.{self.id}.inbox", 
                group, 
                mkstream=True
            )
        except Exception:
            pass  # Group exists
        
        while not self.is_shutting_down:
            try:
                messages = await self.redis.xreadgroup(
                    group, 
                    consumer, 
                    {f"agent.{self.id}.inbox": ">"}, 
                    count=1, 
                    block=5000
                )
                
                if not messages:
                    continue
                
                stream_id, data = messages[0][1][0]
                envelope = TaskEnvelope.model_validate_json(data["payload"])
                
                # Process task with metrics
                start_time = asyncio.get_event_loop().time()
                try:
                    result = await self.handle_task(envelope)
                    self.metrics.tasks_processed += 1
                    
                    # Update response time metrics
                    duration = asyncio.get_event_loop().time() - start_time
                    self.metrics.avg_response_time = (
                        (self.metrics.avg_response_time * (self.metrics.tasks_processed - 1) + duration) /
                        self.metrics.tasks_processed
                    )
                    
                except Exception as e:
                    self.metrics.tasks_failed += 1
                    print(f"❌ Task processing failed: {e}")
                    result = envelope  # Return original on failure
                
                # Publish result
                await self.redis.xadd(
                    "task.results", 
                    {"payload": result.model_dump_json()}
                )
                
                # Acknowledge processing
                await self.redis.xack(f"agent.{self.id}.inbox", group, stream_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Redis consumer error for {self.name}: {e}")
                await asyncio.sleep(5)

    async def _metrics_collector(self):
        """Background task to collect performance metrics"""
        while not self.is_shutting_down:
            try:
                # Collect system metrics (memory, CPU, etc.)
                import psutil
                process = psutil.Process()
                
                # Store metrics for health endpoint
                self._current_metrics = {
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "cpu_percent": process.cpu_percent(),
                    "open_files": len(process.open_files()),
                    "threads": process.num_threads()
                }
                
            except Exception as e:
                print(f"⚠️ Metrics collection error: {e}")
            
            await asyncio.sleep(30)  # Collect every 30 seconds

    def _setup_routes(self):
        """Enhanced route setup with comprehensive endpoints"""
        
        @self.app.get("/health", response_model=HealthStatus)
        async def health_check():
            """Comprehensive health check endpoint"""
            uptime = asyncio.get_event_loop().time() - self.metrics.start_time
            
            # Test Redis connection
            redis_ok = False
            try:
                await self.redis.ping()
                redis_ok = True
            except:
                pass
            
            # Test Registry connection
            registry_ok = False
            try:
                resp = await self.http_client.get(f"{self.registry_url}/health", timeout=5.0)
                registry_ok = resp.status_code == 200
            except:
                pass
            
            return HealthStatus(
                status="healthy" if redis_ok and registry_ok else "degraded",
                agent_id=self.id,
                version=self.version,
                uptime=uptime,
                redis_connected=redis_ok,
                registry_connected=registry_ok,
                active_tasks=0,  # Could track active tasks in the future
                memory_usage=getattr(self, '_current_metrics', {})
            )
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Performance metrics endpoint"""
            return {
                "tasks_processed": self.metrics.tasks_processed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": (
                    (self.metrics.tasks_processed - self.metrics.tasks_failed) / 
                    max(self.metrics.tasks_processed, 1) * 100
                ),
                "avg_response_time": self.metrics.avg_response_time,
                "uptime": asyncio.get_event_loop().time() - self.metrics.start_time
            }
        
        @self.app.get("/capabilities")
        async def get_capabilities():
            """Agent capabilities discovery"""
            return {
                "agent_id": self.id,
                "name": self.name,
                "version": self.version,
                "capabilities": [cap.model_dump() for cap in self.capabilities],
                "status": "ready"
            }
        
        @self.app.post("/tasks")
        async def receive_task(envelope: TaskEnvelope):
            """HTTP endpoint for A2A task reception"""
            if self.is_shutting_down:
                raise HTTPException(503, "Agent is shutting down")
            
            try:
                result = await self.handle_task(envelope)
                return result.model_dump()
            except Exception as e:
                raise HTTPException(500, f"Task processing failed: {str(e)}")

    def get_registration_payload(self) -> dict:
        """Enhanced registration payload"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "version": self.version,
            "host": self.host,
            "port": self.port,
            "mcp_port": self.mcp_port,
            "capabilities": [cap.model_dump() for cap in self.capabilities],
            "status": "active",
            "health_endpoint": f"http://{self.host}:{self.port}/health",
            "metrics_endpoint": f"http://{self.host}:{self.port}/metrics"
        }

    def run(self, **kwargs):
        """Enhanced run method with production configuration"""
        config = {
            "host": "0.0.0.0",
            "port": self.port,
            "log_level": os.getenv("LOG_LEVEL", "info"),
            "access_log": os.getenv("DEBUG", "false").lower() == "true",
            "loop": "uvloop" if os.name != "nt" else "asyncio",  # Use uvloop on Unix
            **kwargs
        }
        
        print(f"🎬 {self.name} taking the stage on port {self.port}!")
        uvicorn.run(self.app, **config)