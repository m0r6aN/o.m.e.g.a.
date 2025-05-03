"""
OMEGA Framework Setup Script

This script bootstraps the OMEGA framework by:
1. Creating necessary directory structure
2. Setting up core components (registry, port manager)
3. Deploying essential MCP tools
4. Deploying base agents
5. Generating Docker Compose file

Just run this script and watch the magic happen!
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


def print_banner():
    """Print the badass OMEGA banner"""
    print("\n" + "=" * 70)
    print("""
   ██████╗ ███╗   ███╗███████╗ ██████╗  █████╗ 
  ██╔═══██╗████╗ ████║██╔════╝██╔════╝ ██╔══██╗
  ██║   ██║██╔████╔██║█████╗  ██║  ███╗███████║
  ██║   ██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║
  ╚██████╔╝██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║
   ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
                                                
  Orchestrated Multi-Expert Gen Agents
    """)
    print("=" * 70)
    print("\n🚀 Setting up the OMEGA Framework...\n")


def create_directory_structure():
    """Create the necessary directory structure for the framework"""
    print("📁 Creating directory structure...")
    
    directories = [
        "agents",
        "agents/orchestrator",
        "agents/weather",
        "agents/finance",
        "agents/math_solver",
        "tools",
        "tools/calculator",
        "tools/translation",
        "registry",
        "lib",
        "lib/core",
        "data"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ Created {directory}/")
    
    print("📁 Directory structure created successfully!\n")


def setup_core_components():
    """Set up the core components of the framework"""
    print("🧠 Setting up core components...")
    
    # Copy core files
    core_files = [
        ("port_manager.py", "lib/core/"),
        ("enhanced_tool_builder.py", "lib/core/"),
        ("enhanced_dual_mode_agent.py", "lib/core/"),
        ("registerable_mcp_tool.py", "lib/core/"),
        ("agent_registry_service.py", "registry/")
    ]
    
    for file, dest in core_files:
        if os.path.exists(file):
            shutil.copy(file, dest)
            print(f"  ✅ Copied {file} to {dest}")
        else:
            print(f"  ⚠️ Warning: {file} not found, skipping...")
    
    # Create registry Dockerfile
    with open("registry/Dockerfile", "w") as f:
        f.write("""FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy registry code
COPY . .

# Set environment variables
ENV PORT=8080
ENV MONGODB_URL=mongodb://mongo:27017/
ENV MONGODB_NAME=agent_registry

# Run the registry
CMD ["python", "agent_registry_service.py"]
""")
    
    # Create registry requirements.txt
    with open("registry/requirements.txt", "w") as f:
        f.write("""fastapi
uvicorn
pydantic
pymongo
aiohttp
pyyaml
""")
    
    print("🧠 Core components set up successfully!\n")


def create_init_script():
    """Create the initialization script for the framework"""
    print("📜 Creating initialization script...")
    
    with open("init.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
OMEGA Framework Initialization Script

This script deploys components of the OMEGA framework:
1. MCP tools
2. A2A agents
3. Updates Docker Compose file
\"\"\"

import os
import sys
from pathlib import Path

# Add the lib directory to the path
sys.path.append(str(Path(__file__).parent / "lib"))
sys.path.append(str(Path(__file__).parent / "lib/core"))

from enhanced_tool_builder import EnhancedToolBuilder
from port_manager import get_port_manager


def deploy_calculator_tool():
    \"\"\"
    Deploy a calculator tool with automatic port allocation and docker-compose integration.
    \"\"\"
    print("🚀 Creating and deploying Calculator Tool...")
    
    # Define calculator functions
    def add(a: float, b: float) -> str:
        \"\"\"Add two numbers together\"\"\"
        result = a + b
        return f"The sum of {a} and {b} is {result}"
    
    def subtract(a: float, b: float) -> str:
        \"\"\"Subtract b from a\"\"\"
        result = a - b
        return f"The result of {a} minus {b} is {result}"
    
    def multiply(a: float, b: float) -> str:
        \"\"\"Multiply two numbers\"\"\"
        result = a * b
        return f"The product of {a} and {b} is {result}"
    
    def divide(a: float, b: float) -> str:
        \"\"\"Divide a by b\"\"\"
        if b == 0:
            return "Error: Cannot divide by zero"
        result = a / b
        return f"The result of {a} divided by {b} is {result}"
    
    # Create the calculator tool using the enhanced builder
    calculator_builder = (EnhancedToolBuilder("calculator", "Calculator Tool")
        .with_description("A tool for performing mathematical calculations")
        .with_version("1.0.0")
        .with_tags("math", "calculator", "arithmetic")
        .add_function(
            "add", 
            add, 
            "Add two numbers together",
            {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            }
        )
        .add_function(
            "subtract", 
            subtract, 
            "Subtract the second number from the first",
            {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Number to subtract"}
            }
        )
        .add_function(
            "multiply", 
            multiply, 
            "Multiply two numbers together",
            {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            }
        )
        .add_function(
            "divide", 
            divide, 
            "Divide the first number by the second",
            {
                "a": {"type": "number", "description": "Numerator"},
                "b": {"type": "number", "description": "Denominator"}
            }
        )
        .with_output_dir("./tools")
        .with_docker_compose(True)
        .with_requirements("numpy>=1.22.0")
        .with_dependencies("registry")
    )
    
    # Deploy the tool
    _, deployment_info = calculator_builder.deploy()
    
    print(f"✅ Calculator Tool deployed successfully")
    print(f"📁 Output directory: {deployment_info['output_dir']}")
    print(f"🌐 HTTP port: {deployment_info['http_port']}")
    print(f"🔌 MCP port: {deployment_info['mcp_port']}")
    print(f"🐳 Added to docker-compose: {deployment_info['docker_compose']}")


def deploy_translation_tool():
    \"\"\"
    Deploy a translation tool with automatic port allocation and docker-compose integration.
    \"\"\"
    print("🚀 Creating and deploying Translation Tool...")
    
    # Define translation functions
    def translate_text(text: str, source_lang: str, target_lang: str) -> str:
        \"\"\"Translate text from source language to target language\"\"\"
        # In a real implementation, this would use a translation API
        # For this example, we'll just return a mock response
        return f"Translated '{text}' from {source_lang} to {target_lang}"
    
    def detect_language(text: str) -> str:
        \"\"\"Detect the language of the provided text\"\"\"
        # In a real implementation, this would use a language detection API
        # For this example, we'll just return a mock response
        return f"Detected language for '{text}' is English"
    
    # Create the translation tool using the enhanced builder
    translation_builder = (EnhancedToolBuilder("translation", "Translation Tool")
        .with_description("A tool for translating text between languages")
        .with_version("1.0.0")
        .with_tags("language", "translation", "nlp")
        .add_function(
            "translate", 
            translate_text, 
            "Translate text from one language to another",
            {
                "text": {"type": "string", "description": "Text to translate"},
                "source_lang": {"type": "string", "description": "Source language code (e.g., 'en')"},
                "target_lang": {"type": "string", "description": "Target language code (e.g., 'fr')"}
            }
        )
        .add_function(
            "detect_language", 
            detect_language, 
            "Detect the language of the given text",
            {
                "text": {"type": "string", "description": "Text to analyze"}
            }
        )
        .with_output_dir("./tools")
        .with_docker_compose(True)
        .with_requirements("langdetect>=1.0.9")
        .with_dependencies("registry")
    )
    
    # Deploy the tool
    _, deployment_info = translation_builder.deploy()
    
    print(f"✅ Translation Tool deployed successfully")
    print(f"📁 Output directory: {deployment_info['output_dir']}")
    print(f"🌐 HTTP port: {deployment_info['http_port']}")
    print(f"🔌 MCP port: {deployment_info['mcp_port']}")
    print(f"🐳 Added to docker-compose: {deployment_info['docker_compose']}")


def deploy_weather_agent():
    \"\"\"
    Deploy a weather agent with automatic port allocation and docker-compose integration.
    \"\"\"
    print("🚀 Creating and deploying Weather Agent...")
    
    # Create output directory for the agent
    output_dir = Path("./agents/weather")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get port manager and allocate ports
    port_manager = get_port_manager()
    http_port = port_manager.allocate_port("weather_agent_http", "agent")
    mcp_port = port_manager.allocate_port("weather_agent_mcp", "agent")
    
    # Create agent.py
    with open(output_dir / "agent.py", "w") as f:
        f.write(\"""import os
import sys
from pathlib import Path

# Add the lib directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "lib"))
sys.path.append(str(Path(__file__).parent.parent.parent / "lib/core"))

from enhanced_dual_mode_agent import RegisterableDualModeAgent
from omega.core.models.task_models import TaskEnvelope

class WeatherAgent(RegisterableDualModeAgent):
    \"""
    Example weather agent that provides weather information.
    \"""
    
    def __init__(self):
        super().__init__(
            agent_id="weather_agent",
            tool_name="weather",
            description="Provides weather information for locations worldwide",
            version="1.0.0",
            skills=["get_weather", "get_forecast"],
            agent_type="agent",
            tags=["weather", "forecast"]
        )
    
    def _register_a2a_capabilities(self):
        # A2A capabilities would be registered here
        pass
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        try:
            # Extract input from the task envelope
            input_text = env.input.get("text", "") if env.input else ""
            
            if "weather" in input_text.lower() and "in" in input_text.lower():
                # Extract location
                location = input_text.split("in", 1)[1].strip().rstrip("?.")
                
                # Mock weather response
                response = f"The weather in {location} is currently 72°F and sunny with a light breeze."
                
                # Set the output
                env.output = {"text": response}
                env.status = "COMPLETED"
            
            elif "forecast" in input_text.lower() and "in" in input_text.lower():
                # Extract location
                location = input_text.split("in", 1)[1].strip().rstrip("?.")
                
                # Mock forecast response
                response = f"Weather forecast for {location}:\\n\\n"
                response += "Today: 72°F, Sunny\\n"
                response += "Tomorrow: 75°F, Partly Cloudy\\n"
                response += "Day after: 68°F, Chance of Rain"
                
                # Set the output
                env.output = {"text": response}
                env.status = "COMPLETED"
            
            else:
                # Default response
                env.output = {
                    "text": (
                        "I'm a weather agent. You can ask for:\\n"
                        "- Weather in [location]\\n"
                        "- Forecast in [location]"
                    )
                }
                env.status = "COMPLETED"
            
            return env
            
        except Exception as e:
            # Handle errors
            env.output = {"text": f"Error processing request: {str(e)}"}
            env.status = "ERROR"
            return env

if __name__ == "__main__":
    # Create and run the weather agent
    agent = WeatherAgent()
    agent.run()
\""")
    
    # Create Dockerfile
    with open(output_dir / "Dockerfile", "w") as f:
        f.write(\"""FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY . .

# Set environment variables with defaults
ENV PORT=8000
ENV MCP_PORT=9000
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REGISTRY_URL=http://registry:9401
ENV HOST=localhost

# Run the agent
CMD ["python", "agent.py"]
\""")
    
    # Create requirements.txt
    with open(output_dir / "requirements.txt", "w") as f:
        f.write(\"""fastapi
uvicorn
redis
pydantic
aiohttp
python-a2a
fastmcp
asyncio
\""")
    
    # Add to docker-compose.yml
    port_manager.add_to_docker_compose(
        component_id="weather_agent",
        component_type="agent",
        build_path=str(output_dir),
        depends_on=["redis", "registry"],
        http_port=http_port,
        mcp_port=mcp_port
    )
    
    print(f"✅ Weather Agent deployed successfully")
    print(f"📁 Output directory: {output_dir}")
    print(f"🌐 HTTP port: {http_port}")
    print(f"🔌 MCP port: {mcp_port}")
    print(f"🐳 Added to docker-compose: True")


if __name__ == "__main__":
    # Create output directory structure
    os.makedirs("./tools", exist_ok=True)
    os.makedirs("./agents", exist_ok=True)
    
    # Deploy tools and agents
    deploy_calculator_tool()
    print("\\n" + "="*50 + "\\n")
    deploy_translation_tool()
    print("\\n" + "="*50 + "\\n")
    deploy_weather_agent()
    
    print("\\n🎉 All components deployed successfully!")
    print("🚀 Run 'docker-compose up' to start the system")
""")
    
    # Make the script executable
    os.chmod("init.py", 0o755)
    
    print("📜 Initialization script created successfully!\n")


def create_docker_compose_base():
    """Create the base Docker Compose file"""
    print("🐳 Creating base Docker Compose file...")
    
    with open("docker-compose.yml", "w") as f:
        f.write("""version: '3.8'

services:
  # Central registry service
  registry:
    build:
      context: ./registry
      dockerfile: Dockerfile
    environment:
      - PORT=8080
      - MONGODB_URL=mongodb://mongo:27017/
      - MONGODB_NAME=agent_registry
    ports:
      - "8080:8080"
    depends_on:
      - mongo
    networks:
      - agent_network
    restart: always

  # MongoDB for registry storage
  mongo:
    image: mongo:latest
    volumes:
      - mongo_data:/data/db
    networks:
      - agent_network
    restart: always

  # Redis for agent communication
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    networks:
      - agent_network
    restart: always

volumes:
  mongo_data:

networks:
  agent_network:
    driver: bridge
""")
    
    print("🐳 Base Docker Compose file created successfully!\n")


def create_readme():
    """Create the README.md file"""
    print("📚 Creating README.md...")
    
    # Check if README.md already exists
    if os.path.exists("README.md"):
        backup_path = "README.md.bak"
        shutil.copy("README.md", backup_path)
        print(f"  ⚠️ Existing README.md found, backed up to {backup_path}")
    
    # Copy the README content from the artifact we created earlier
    if os.path.exists("omega_readme.md"):
        shutil.copy("omega_readme.md", "README.md")
        print("  ✅ Created README.md from template")
    else:
        print("  ⚠️ Warning: README template not found, skipping...")
    
    print("📚 README.md created successfully!\n")


def create_orchestrator_agent():
    """Create the orchestrator agent"""
    print("🧠 Creating orchestrator agent...")
    
    # Create output directory for the agent
    output_dir = Path("./agents/orchestrator")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create agent.py
    with open(output_dir / "agent.py", "w") as f:
        f.write("""import os
import sys
import asyncio
from pathlib import Path

# Add the lib directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "lib"))
sys.path.append(str(Path(__file__).parent.parent.parent / "lib/core"))

from enhanced_dual_mode_agent import RegisterableDualModeAgent
from omega.core.models.task_models import TaskEnvelope

class OrchestratorAgent(RegisterableDualModeAgent):
    """
    Orchestrator agent that coordinates other agents and tools.
    This is the brain of the OMEGA framework.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="orchestrator",
            tool_name="orchestrator",
            description="Main orchestrator that coordinates agents and tools",
            version="1.0.0",
            skills=["orchestrate", "execute_workflow"],
            agent_type="agent",
            tags=["orchestration", "workflow"]
        )
    
    def _register_a2a_capabilities(self):
        # A2A capabilities would be registered here
        pass
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        try:
            # Extract input from the task envelope
            input_text = env.input.get("text", "") if env.input else ""
            
            if "weather" in input_text.lower():
                # This looks like a weather-related query, delegate to the weather agent
                weather_agent = await self.find_agent_by_capability("get_weather")
                
                if weather_agent:
                    # Forward the query to the weather agent
                    weather_result = await self.forward_to_agent(weather_agent["id"], input_text)
                    env.output = {"text": weather_result.get("text", "Error getting weather information")}
                else:
                    env.output = {"text": "I couldn't find a weather agent to handle your query."}
                
                env.status = "COMPLETED"
                
            elif "calculate" in input_text.lower() or any(op in input