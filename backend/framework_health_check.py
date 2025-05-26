#!/usr/bin/env python3
"""
OMEGA Framework Health Check & Tool Registration Verification
Checks all services and tools for proper deployment and registration.
"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

SERVICES = {
    "agent_registry": {"port": 9401, "type": "service"},
    "mcp_registry": {"port": 9402, "type": "service"},
    "orchestrator": {"port": 9000, "type": "agent"},
    "math_solver": {"port": 9002, "type": "agent"},
    "workflow_planner": {"port": 9004, "type": "agent"},
    "prompt_optimizer": {"port": 9006, "type": "agent"},
    "capability_matcher": {"port": 9008, "type": "agent"},
    "code_generator": {"port": 9014, "type": "agent"},
    "project_architect": {"port": 9016, "type": "agent"},
}

TOOLS = {
    "execute_sql": {"port": 9201, "type": "tool"},
    "calculator": {"port": 9202, "type": "tool"},
    "nlp_to_sql": {"port": 9203, "type": "tool"},
    "summarize_text": {"port": 9204, "type": "tool"},
    "translate_text": {"port": 9205, "type": "tool"},
    "web_search": {"port": 9206, "type": "tool"},
    "context7": {"port": 9207, "type": "tool"},
    "code_analyzer": {"port": 9208, "type": "tool"},
}

# ============================================================================
# HEALTH CHECK FUNCTIONS
# ============================================================================

async def check_service_health(name: str, port: int) -> Dict[str, Any]:
    """Check health of a single service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://localhost:{port}/health")
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": name,
                    "port": port,
                    "status": "healthy",
                    "response": data
                }
            else:
                return {
                    "name": name,
                    "port": port,
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "name": name,
            "port": port,
            "status": "offline",
            "error": str(e)
        }

async def check_registry_contents(registry_url: str, registry_type: str) -> Dict[str, Any]:
    """Check what's registered in a registry."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if registry_type == "agent":
                response = await client.get(f"{registry_url}/agents")
            else:  # mcp
                response = await client.get(f"{registry_url}/tools")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "registry": registry_type,
                    "status": "healthy",
                    "registered_count": len(data.get("agents", data.get("tools", []))),
                    "items": data
                }
            else:
                return {
                    "registry": registry_type,
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "registry": registry_type,
            "status": "offline",
            "error": str(e)
        }

async def test_capability_matcher() -> Dict[str, Any]:
    """Test the capability matcher with a sample query."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:9008/match",
                json={
                    "query": "I need help with mathematical calculations",
                    "min_score": 0.3,
                    "max_results": 3
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "capability_matcher",
                    "status": "success",
                    "matches_found": len(data.get("matches", [])),
                    "response": data
                }
            else:
                return {
                    "test": "capability_matcher",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "test": "capability_matcher",
            "status": "error",
            "error": str(e)
        }

async def test_workflow_planner() -> Dict[str, Any]:
    """Test the workflow planner with a sample request."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:9004/plan",
                json={
                    "prompt": "Create a simple calculator app",
                    "optimization_level": "balanced",
                    "include_agent_assignment": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "test": "workflow_planner",
                    "status": "success",
                    "tasks_generated": len(data.get("workflow_plan", {}).get("tasks", [])),
                    "response": data
                }
            else:
                return {
                    "test": "workflow_planner",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "test": "workflow_planner",
            "status": "error",
            "error": str(e)
        }

# ============================================================================
# MAIN HEALTH CHECK FUNCTION
# ============================================================================

async def run_full_health_check():
    """Run comprehensive health check of the OMEGA system."""
    print("🚀 OMEGA FRAMEWORK HEALTH CHECK INITIATED")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "tools": {},
        "registries": {},
        "tests": {}
    }
    
    # Check core services
    print("\n🔧 CHECKING CORE SERVICES...")
    for name, config in SERVICES.items():
        result = await check_service_health(name, config["port"])
        results["services"][name] = result
        
        status_icon = "✅" if result["status"] == "healthy" else "❌"
        print(f"  {status_icon} {name:20} Port {config['port']:4} - {result['status']}")
    
    # Check MCP tools
    print("\n🔧 CHECKING MCP TOOLS...")
    for name, config in TOOLS.items():
        result = await check_service_health(name, config["port"])
        results["tools"][name] = result
        
        status_icon = "✅" if result["status"] == "healthy" else "❌"
        print(f"  {status_icon} {name:20} Port {config['port']:4} - {result['status']}")
    
    # Check registry contents
    print("\n📊 CHECKING REGISTRY CONTENTS...")
    
    # Agent Registry
    agent_registry_result = await check_registry_contents("http://localhost:9401", "agent")
    results["registries"]["agent_registry"] = agent_registry_result
    if agent_registry_result["status"] == "healthy":
        count = agent_registry_result["registered_count"]
        print(f"  ✅ Agent Registry: {count} agents registered")
    else:
        print(f"  ❌ Agent Registry: {agent_registry_result['error']}")
    
    # MCP Registry
    mcp_registry_result = await check_registry_contents("http://localhost:9402", "mcp")
    results["registries"]["mcp_registry"] = mcp_registry_result
    if mcp_registry_result["status"] == "healthy":
        count = mcp_registry_result["registered_count"]
        print(f"  ✅ MCP Registry: {count} tools registered")
    else:
        print(f"  ❌ MCP Registry: {mcp_registry_result['error']}")
    
    # Run functional tests
    print("\n🧪 RUNNING FUNCTIONAL TESTS...")
    
    # Test Capability Matcher
    cap_match_result = await test_capability_matcher()
    results["tests"]["capability_matcher"] = cap_match_result
    if cap_match_result["status"] == "success":
        matches = cap_match_result["matches_found"]
        print(f"  ✅ Capability Matcher: Found {matches} matches")
    else:
        print(f"  ❌ Capability Matcher: {cap_match_result.get('error', 'Unknown error')}")
    
    # Test Workflow Planner
    workflow_result = await test_workflow_planner()
    results["tests"]["workflow_planner"] = workflow_result
    if workflow_result["status"] == "success":
        tasks = workflow_result["tasks_generated"]
        print(f"  ✅ Workflow Planner: Generated {tasks} tasks")
    else:
        print(f"  ❌ Workflow Planner: {workflow_result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 OMEGA HEALTH SUMMARY")
    print("=" * 60)
    
    # Count healthy services
    healthy_services = sum(1 for r in results["services"].values() if r["status"] == "healthy")
    total_services = len(results["services"])
    print(f"Core Services: {healthy_services}/{total_services} healthy")
    
    # Count healthy tools
    healthy_tools = sum(1 for r in results["tools"].values() if r["status"] == "healthy")
    total_tools = len(results["tools"])
    print(f"MCP Tools: {healthy_tools}/{total_tools} healthy")
    
    # Registry status
    for reg_name, reg_result in results["registries"].items():
        status = "✅" if reg_result["status"] == "healthy" else "❌"
        count = reg_result.get("registered_count", 0) if reg_result["status"] == "healthy" else 0
        print(f"{reg_name}: {status} ({count} registered)")
    
    # Test results
    successful_tests = sum(1 for r in results["tests"].values() if r["status"] == "success")
    total_tests = len(results["tests"])
    print(f"Functional Tests: {successful_tests}/{total_tests} passed")
    
    # Overall status
    overall_health = (healthy_services / total_services) * 100
    print(f"\n🌟 OVERALL SYSTEM HEALTH: {overall_health:.1f}%")
    
    if overall_health >= 80:
        print("🚀 OMEGA CONSTELLATION STATUS: OPERATIONAL")
    elif overall_health >= 60:
        print("⚠️  OMEGA CONSTELLATION STATUS: PARTIAL")
    else:
        print("❌ OMEGA CONSTELLATION STATUS: CRITICAL")
    
    return results

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("🌟 OMEGA Framework Health Check & Registration Verification")
    print("Built by the Dream Team Partnership 🤖🤝🤖")
    print()
    
    try:
        results = asyncio.run(run_full_health_check())
        
        # Optionally save results to file
        with open("omega_health_report.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed report saved to: omega_health_report.json")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Health check interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Health check failed: {e}")