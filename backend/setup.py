#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA Framework Setup Script - Windows Compatible
Handles installation, environment setup, and initial configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List

# Force UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    import locale
    if locale.getpreferredencoding().lower() != 'utf-8':
        os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_command(cmd: List[str], cwd: str = None) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        print(f"[SUCCESS] {' '.join(cmd)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return False

def check_requirements() -> bool:
    """Check if required system tools are installed."""
    print("Checking system requirements...")
    
    required_tools = {
        "python": ["python", "--version"],
        "docker": ["docker", "--version"],
        "docker-compose": ["docker-compose", "--version"]
    }
    
    missing_tools = []
    for tool, cmd in required_tools.items():
        if not shutil.which(cmd[0]):
            missing_tools.append(tool)
        else:
            if run_command(cmd):
                continue
    
    if missing_tools:
        print(f"[ERROR] Missing required tools: {', '.join(missing_tools)}")
        print("\nPlease install:")
        if "python" in missing_tools:
            print("- Python 3.12+ from https://python.org")
        if "docker" in missing_tools:
            print("- Docker from https://docker.com")
        if "docker-compose" in missing_tools:
            print("- Docker Compose from https://docs.docker.com/compose/install/")
        return False
    
    print("[SUCCESS] All required tools are installed!")
    return True

def setup_environment() -> bool:
    """Setup Python environment and install dependencies."""
    print("\nSetting up Python environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 12:
        print(f"[ERROR] Python 3.12+ required, found {python_version.major}.{python_version.minor}")
        return False
    
    # Install package in development mode
    print("Installing OMEGA package...")
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."]):
        return False
    
    # Install development dependencies
    print("Installing development dependencies...")
    if not run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev,test]"]):
        print("[WARNING] Dev dependencies failed, continuing...")
    
    return True

def create_env_file() -> bool:
    """Create .env file with default configuration."""
    print("\nCreating environment configuration...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("[SUCCESS] .env file already exists")
        return True
    
    env_template = """# OMEGA Framework Environment Configuration
# Copy this file to .env and update with your values

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
MONGO_USERNAME=omega
MONGO_PASSWORD=omegapass

# External APIs
WEATHER_API_KEY=your_weather_api_key_here
SEARCH_API_KEY=your_search_api_key_here
CONTEXT7_API_KEY=your_context7_api_key_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# MongoDB Configuration
MONGODB_URL=mongodb://omega:omegapass@localhost:27017
MONGODB_NAME=omega

# Logging
LOG_LEVEL=info

# Development Settings
DEBUG=true
ENVIRONMENT=development

# Registry URLs (for development)
AGENT_REGISTRY_URL=http://localhost:9401
MCP_REGISTRY_URL=http://localhost:9402
WORKFLOW_REGISTRY_URL=http://localhost:9403

# UI Configuration
UI_PORT=7860
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_template)
        print("[SUCCESS] Created .env template file")
        print("   Please update it with your actual API keys!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create .env file: {e}")
        return False

def setup_docker_environment() -> bool:
    """Setup Docker environment and build base images."""
    print("\nSetting up Docker environment...")
    
    # Create docker network
    print("Creating Docker network...")
    run_command(["docker", "network", "create", "omega_network"])
    
    print("[SUCCESS] Docker environment ready")
    return True

def create_project_structure() -> bool:
    """Ensure all required directories exist."""
    print("\nChecking project structure...")
    
    required_dirs = [
        "src/omega/cli",
        "src/omega/core/schemas", 
        "src/omega/workflows/templates",
        "logs",
        "data",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files where needed
    init_files = [
        "src/omega/__init__.py",
        "src/omega/cli/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = Path(init_file)
        if not init_path.exists():
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write("# OMEGA Framework\n")
    
    print("[SUCCESS] Project structure verified")
    return True

def create_cli_scripts() -> bool:
    """Create CLI entry point scripts."""
    print("\nCreating CLI scripts...")
    
    cli_dir = Path("src/omega/cli")
    
    # Main CLI script
    main_cli = cli_dir / "main.py"
    if not main_cli.exists():
        main_cli_content = '''#!/usr/bin/env python3
"""OMEGA Framework CLI."""

import click

@click.group()
@click.version_option()
def main():
    """OMEGA Framework - Orchestrated Multi-Expert Gen Agents."""
    pass

@main.command()
def status():
    """Check OMEGA system status."""
    click.echo("OMEGA Framework Status Check")
    # Add status checking logic here

@main.command()
def start():
    """Start OMEGA services."""
    click.echo("Starting OMEGA services...")
    # Add startup logic here

@main.command()
def stop():
    """Stop OMEGA services."""
    click.echo("Stopping OMEGA services...")
    # Add shutdown logic here

if __name__ == "__main__":
    main()
'''
        with open(main_cli, 'w', encoding='utf-8') as f:
            f.write(main_cli_content)
    
    # Agent CLI script
    agent_cli = cli_dir / "agent.py"
    if not agent_cli.exists():
        agent_cli_content = '''#!/usr/bin/env python3
"""OMEGA Agent CLI."""

import click

@click.group()
def main():
    """OMEGA Agent Management."""
    pass

@main.command()
@click.argument('agent_name')
def start(agent_name):
    """Start a specific agent."""
    click.echo(f"Starting {agent_name} agent...")

@main.command()
@click.argument('agent_name') 
def stop(agent_name):
    """Stop a specific agent."""
    click.echo(f"Stopping {agent_name} agent...")

@main.command()
def list():
    """List all available agents."""
    click.echo("Available OMEGA agents:")

if __name__ == "__main__":
    main()
'''
        with open(agent_cli, 'w', encoding='utf-8') as f:
            f.write(agent_cli_content)
    
    print("[SUCCESS] CLI scripts created")
    return True

def run_tests() -> bool:
    """Run basic tests to verify installation."""
    print("\nRunning verification tests...")
    
    # Check if we can import the package
    try:
        import omega
        print("[SUCCESS] OMEGA package imports successfully")
    except ImportError as e:
        print(f"[WARNING] Failed to import OMEGA: {e}")
        print("This is normal if core modules aren't implemented yet")
    
    return True

def print_success_message():
    """Print success message with next steps."""
    print("\n" + "="*60)
    print("OMEGA FRAMEWORK SETUP COMPLETE!")
    print("="*60)
    print("""
Next Steps:

1. Update your .env file with real API keys:
   - OPENAI_API_KEY (required)
   - WEATHER_API_KEY (optional)
   - CONTEXT7_API_KEY (optional)

2. Start the OMEGA ecosystem:
   cd backend && docker-compose up -d

3. Access the UI:
   http://localhost:7860

4. Check system status:
   omega status

5. View available commands:
   omega --help

Welcome to the OMEGA multiverse, partner! LFG!
    """)

def main():
    """Main setup function."""
    print("OMEGA Framework Setup")
    print("=" * 50)
    
    steps = [
        ("Checking requirements", check_requirements),
        ("Creating project structure", create_project_structure), 
        ("Setting up environment", setup_environment),
        ("Creating environment config", create_env_file),
        ("Creating CLI scripts", create_cli_scripts),
        ("Setting up Docker", setup_docker_environment),
        ("Running verification tests", run_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"\n[STEP] {step_name}...")
        if not step_func():
            print(f"[ERROR] Setup failed at: {step_name}")
            sys.exit(1)
    
    print_success_message()

if __name__ == "__main__":
    main()