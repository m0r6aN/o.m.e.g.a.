# examples/test_capability_matching.py

import asyncio
import json
import aiohttp
from pprint import pprint

async def test_matching():
    """Test the capability matching system"""
    print("🔍 Testing capability matching system...")
    
    registry_url = "http://localhost:8080"  # Adjust to your registry URL
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Match a specific capability
        print("\n📋 Test 1: Match 'weather forecast'")
        async with session.post(
            f"{registry_url}/registry/capabilities/match",
            json={"text": "weather forecast", "min_score": 0.6}
        ) as response:
            if response.status == 200:
                matches = await response.json()
                print(f"Found {len(matches)} matches:")
                pprint(matches)
            else:
                print(f"❌ Error: {response.status}")
        
        # Test 2: Match with tags
        print("\n📋 Test 2: Match with tags ['severe', 'warning']")
        async with session.post(
            f"{registry_url}/registry/capabilities/match",
            json={"text": "alert", "tags": ["severe", "warning"], "min_score": 0.6}
        ) as response:
            if response.status == 200:
                matches = await response.json()
                print(f"Found {len(matches)} matches:")
                pprint(matches)
            else:
                print(f"❌ Error: {response.status}")
        
        # Test 3: Use a capability example
        print("\n📋 Test 3: Match using an example query")
        async with session.post(
            f"{registry_url}/registry/capabilities/match",
            json={"text": "What's the weather like in New York?", "min_score": 0.6}
        ) as response:
            if response.status == 200:
                matches = await response.json()
                print(f"Found {len(matches)} matches:")
                pprint(matches)
            else:
                print(f"❌ Error: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_matching())