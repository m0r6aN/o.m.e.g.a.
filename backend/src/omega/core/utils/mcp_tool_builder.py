import os
import shutil
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic, Union, Tuple
from pathlib import Path
from registerable_mcp_tool import RegisterableMCPTool
from fastmcp import text_response
from port_manager import get_port_manager

# Type for tool function
T = TypeVar('T')
ToolFunc = Callable[..., Union[str, Dict[str, Any]]]

class MCPToolBuilder:
    """
    An enhanced builder class for creating MCP tools with deployment support.
    Makes it easy to create and configure tools with minimal boilerplate.
    """
    
    def __init__(self, tool_id: str, name: str):
        """
        Initialize the builder with a tool ID and name.
        
        Args:
            tool_id: Unique identifier for the tool
            name: Human-readable name for the tool
        """
        self.tool_id = tool_id
        self.name = name
        self.description = f"{name} MCP Tool"
        self.version = "1.0.0"
        self.tags: List[str] = []
        self.functions: List[Dict[str, Any]] = []
        
        # Deployment options
        self.output_dir: Optional[str] = None
        self.http_port: Optional[int] = None
        self.mcp_port: Optional[int] = None
        self.dependencies: List[str] = []
        self.environment: Dict[str, str] = {}
        self.volumes: List[str] = []
        self.requirements: List[str] = []
        self.auto_docker_compose: bool = False
    
    def with_description(self, description: str) -> 'MCPToolBuilder':
        """Set the tool description"""
        self.description = description
        return self
    
    def with_version(self, version: str) -> 'MCPToolBuilder':
        """Set the tool version"""
        self.version = version
        return self
    
    def with_tags(self, *tags: str) -> 'MCPToolBuilder':
        """Add tags to the tool"""
        self.tags.extend(tags)
        return self
    
    def add_function(
        self,
        name: str,
        func: ToolFunc,
        description: str,
        parameters: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> 'MCPToolBuilder':
        """
        Add a function to the tool.
        
        Args:
            name: Name of the function
            func: The function implementation (will be wrapped with @text_response)
            description: Description of what the function does
            parameters: Optional parameter definitions
            
        Returns:
            Self for chaining
        """
        self.functions.append({
            "name": name,
            "func": func,
            "description": description,
            "parameters": parameters or {}
        })
        return self
    
    def with_output_dir(self, directory: str) -> 'MCPToolBuilder':
        """
        Set the output directory for generated files.
        
        Args:
            directory: Path to the output directory
            
        Returns:
            Self for chaining
        """
        self.output_dir = directory
        return self
    
    def with_ports(self, http_port: Optional[int] = None, mcp_port: Optional[int] = None) -> 'MCPToolBuilder':
        """
        Set specific ports for the tool.
        If not set, ports will be automatically allocated.
        
        Args:
            http_port: HTTP port for the FastAPI server
            mcp_port: Port for the MCP server
            
        Returns:
            Self for chaining
        """
        self.http_port = http_port
        self.mcp_port = mcp_port
        return self
    
    def with_dependencies(self, *services: str) -> 'MCPToolBuilder':
        """
        Add services that this tool depends on.
        
        Args:
            *services: Names of services this tool depends on
            
        Returns:
            Self for chaining
        """
        self.dependencies.extend(services)
        return self
    
    def with_environment(self, **env_vars) -> 'MCPToolBuilder':
        """
        Add environment variables for the tool.
        
        Args:
            **env_vars: Environment variables as keyword arguments
            
        Returns:
            Self for chaining
        """
        self.environment.update(env_vars)
        return self
    
    def with_volumes(self, *volumes: str) -> 'MCPToolBuilder':
        """
        Add volumes to mount in the container.
        
        Args:
            *volumes: Volume mappings (e.g., "./data:/app/data")
            
        Returns:
            Self for chaining
        """
        self.volumes.extend(volumes)
        return self
    
    def with_requirements(self, *packages: str) -> 'MCPToolBuilder':
        """
        Add Python packages to the requirements.txt file.
        
        Args:
            *packages: Package names (e.g., "requests>=2.0.0")
            
        Returns:
            Self for chaining
        """
        self.requirements.extend(packages)
        return self
    
    def with_docker_compose(self, auto_add: bool = True) -> 'MCPToolBuilder':
        """
        Configure whether to automatically add this tool to docker-compose.yml.
        
        Args:
            auto_add: Whether to add the tool to docker-compose.yml
            
        Returns:
            Self for chaining
        """
        self.auto_docker_compose = auto_add
        return self
    
    def build(self) -> RegisterableMCPTool:
        """
        Build the MCP tool with all configured options.
        
        Returns:
            A configured RegisterableMCPTool instance
        """
        # Create the tool instance
        tool = RegisterableMCPTool(
            tool_id=self.tool_id,
            name=self.name,
            description=self.description,
            version=self.version,
            tags=self.tags
        )
        
        # Add all functions
        for func_info in self.functions:
            # Wrap the function with text_response
            wrapped_func = text_response(func_info["func"])
            
            # Add to the tool
            tool.add_tool(
                name=func_info["name"],
                description=func_info["description"],
                func=wrapped_func,
                parameters=func_info["parameters"]
            )
        
        return tool
    
    def deploy(self) -> Tuple[Optional[RegisterableMCPTool], Dict[str, Any]]:
        """
        Deploy the tool and generate the necessary files.
        
        Returns:
            Tuple of (tool instance, deployment info)
        """
        # Get the port manager
        port_manager = get_port_manager()
        
        # Allocate ports if needed
        if self.http_port is None:
            self.http_port = port_manager.allocate_port(f"{self.tool_id}_http", "tool")
        
        if self.mcp_port is None:
            self.mcp_port = port_manager.allocate_port(f"{self.tool_id}_mcp", "tool")
        
        # Create output directory if specified
        if self.output_dir:
            output_dir = Path(self.output_dir) / self.tool_id
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate the main tool file
            self._generate_tool_file(output_dir)
            
            # Generate Dockerfile
            self._generate_dockerfile(output_dir)
            
            # Generate requirements.txt
            self._generate_requirements(output_dir)
            
            # Add to docker-compose.yml if requested
            if self.auto_docker_compose:
                port_manager.add_to_docker_compose(
                    component_id=self.tool_id,
                    component_type="tool",
                    build_path=str(output_dir),
                    environment=self.environment,
                    volumes=self.volumes,
                    depends_on=self.dependencies,
                    http_port=self.http_port,
                    mcp_port=self.mcp_port
                )
        
        # Return deployment info
        deployment_info = {
            "tool_id": self.tool_id,
            "http_port": self.http_port,
            "mcp_port": self.mcp_port,
            "output_dir": str(output_dir) if self.output_dir else None,
            "docker_compose": self.auto_docker_compose
        }
        
        # Build and return the tool instance along with deployment info
        return self.build(), deployment_info
    
    def _generate_tool_file(self, output_dir: Path):
        """
        Generate the main tool file.
        
        Args:
            output_dir: Path to the output directory
        """
        tool_file = output_dir / "tool.py"
        
        with open(tool_file, "w") as f:
            f.write(f"""import os
from registerable_mcp_tool import RegisterableMCPTool
from fastmcp import text_response


def main():
    # Create the {self.name}
    tool = RegisterableMCPTool(
        tool_id="{self.tool_id}",
        name="{self.name}",
        description="{self.description}",
        version="{self.version}",
        tags={self.tags}
    )
    
    # Add tool functions
""")
            
            # Add each function
            for func_info in self.functions:
                func_name = func_info["name"]
                func_desc = func_info["description"]
                func_params = func_info["parameters"]
                
                f.write(f"""
    @text_response
    def {func_name}({self._format_params(func_params)}):
        \"\"\"
        {func_desc}
        \"\"\"
        # Add your implementation here
        {self._get_function_body(func_info["func"])}
    
    tool.add_tool(
        name="{func_name}",
        description="{func_desc}",
        func={func_name},
        parameters={func_params}
    )
""")
            
            # Add main block
            f.write("""
if __name__ == "__main__":
    main()
""")
    
    def _format_params(self, params: Dict[str, Dict[str, Any]]) -> str:
        """
        Format parameters for function declaration.
        
        Args:
            params: Parameter definitions
            
        Returns:
            Formatted parameter string
        """
        if not params:
            return ""
        
        param_strs = []
        for name, param in params.items():
            param_type = param.get("type", "Any")
            if param_type == "string":
                param_type = "str"
            elif param_type == "number":
                param_type = "float"
            elif param_type == "integer":
                param_type = "int"
            elif param_type == "boolean":
                param_type = "bool"
            
            param_strs.append(f"{name}: {param_type}")
        
        return ", ".join(param_strs)
    
    def _get_function_body(self, func: Callable) -> str:
        """
        Extract the function body from a callable.
        
        Args:
            func: The function
            
        Returns:
            Function body as string
        """
        import inspect
        
        # Get the source code
        try:
            source = inspect.getsource(func)
            
            # Remove the function declaration line
            lines = source.split("\n")
            if lines and "def " in lines[0]:
                lines = lines[1:]
            
            # Remove leading whitespace
            if lines:
                min_indent = min((len(line) - len(line.lstrip()) for line in lines if line.strip()))
                lines = [line[min_indent:] for line in lines]
            
            return "\n        ".join(lines)
        except Exception:
            # If we can't get the source, use a placeholder
            return "pass"
    
    def _generate_dockerfile(self, output_dir: Path):
        """
        Generate a Dockerfile for the tool.
        
        Args:
            output_dir: Path to the output directory
        """
        dockerfile = output_dir / "Dockerfile"
        
        with open(dockerfile, "w") as f:
            f.write("""FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy tool code
COPY . .

# Set environment variables with defaults
ENV PORT=8000
ENV MCP_PORT=9000
ENV REGISTRY_URL=http://registry:9401
ENV HOST=localhost

# Run the tool
CMD ["python", "tool.py"]
""")
    
    def _generate_requirements(self, output_dir: Path):
        """
        Generate a requirements.txt file for the tool.
        
        Args:
            output_dir: Path to the output directory
        """
        req_file = output_dir / "requirements.txt"
        
        # Standard requirements
        standard_reqs = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "aiohttp",
            "python-a2a",
            "fastmcp"
        ]
        
        # Combine with custom requirements
        all_reqs = standard_reqs + self.requirements
        
        with open(req_file, "w") as f:
            f.write("\n".join(all_reqs))