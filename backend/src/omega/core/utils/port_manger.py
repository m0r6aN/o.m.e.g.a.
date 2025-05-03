import os
import json
import yaml
import socket
from typing import Dict, Optional, Tuple, Literal
from pathlib import Path


class PortManager:
    """
    Manages port allocations for agents, tools, and services.
    Keeps track of used ports and allocates new ones from predefined ranges.
    Also manages Docker Compose file generation and updates.
    """
    
    # Default port ranges
    DEFAULT_RANGES = {
        "agent": (9000, 9200),
        "tool": (9201, 9400),
        "service": (9401, 9600)
    }
    
    # Path to the port allocation file
    DEFAULT_PORT_FILE = "port_allocations.json"
    
    # Path to Docker Compose file
    DEFAULT_COMPOSE_FILE = "docker-compose.yml"
    
    def __init__(
        self,
        port_ranges: Optional[Dict[str, Tuple[int, int]]] = None,
        port_file: Optional[str] = None,
        compose_file: Optional[str] = None
    ):
        """
        Initialize the port manager with the given port ranges and file paths.
        
        Args:
            port_ranges: Optional custom port ranges for each component type
            port_file: Optional path to the port allocation file
            compose_file: Optional path to the Docker Compose file
        """
        self.port_ranges = port_ranges or self.DEFAULT_RANGES
        self.port_file = port_file or self.DEFAULT_PORT_FILE
        self.compose_file = compose_file or self.DEFAULT_COMPOSE_FILE
        
        # Initialize or load port allocations
        self.port_allocations = self._load_port_allocations()
    
    def _load_port_allocations(self) -> Dict[str, Dict[str, int]]:
        """
        Load port allocations from the JSON file.
        If the file doesn't exist, create a new empty allocations dict.
        
        Returns:
            Dict with component IDs as keys and port numbers as values
        """
        try:
            if os.path.exists(self.port_file):
                with open(self.port_file, 'r') as f:
                    return json.load(f)
            else:
                return {"agent": {}, "tool": {}, "service": {}}
        except Exception as e:
            print(f"⚠️ Error loading port allocations: {e}")
            return {"agent": {}, "tool": {}, "service": {}}
    
    def _save_port_allocations(self):
        """Save the current port allocations to the JSON file."""
        try:
            with open(self.port_file, 'w') as f:
                json.dump(self.port_allocations, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving port allocations: {e}")
    
    def is_port_available(self, port: int) -> bool:
        """
        Check if a port is available on the local machine.
        
        Args:
            port: Port number to check
            
        Returns:
            True if the port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Try to bind to the port
                s.bind(("127.0.0.1", port))
                return True
        except:
            return False
    
    def allocate_port(
        self,
        component_id: str,
        component_type: Literal["agent", "tool", "service"]
    ) -> int:
        """
        Allocate a port for a component.
        If the component already has a port allocated, return that.
        Otherwise, find the next available port in the appropriate range.
        
        Args:
            component_id: Unique identifier for the component
            component_type: Type of the component ("agent", "tool", or "service")
            
        Returns:
            Allocated port number
            
        Raises:
            ValueError: If the component type is invalid or no ports are available
        """
        # Check if we already have a port allocated for this component
        if component_id in self.port_allocations[component_type]:
            return self.port_allocations[component_type][component_id]
        
        # Get the port range for this component type
        if component_type not in self.port_ranges:
            raise ValueError(f"Invalid component type: {component_type}")
        
        min_port, max_port = self.port_ranges[component_type]
        
        # Find all used ports in this range
        used_ports = set(self.port_allocations[component_type].values())
        
        # Find the next available port
        for port in range(min_port, max_port + 1):
            if port not in used_ports and self.is_port_available(port):
                # Allocate this port
                self.port_allocations[component_type][component_id] = port
                self._save_port_allocations()
                return port
        
        # If we get here, no ports are available
        raise ValueError(f"No ports available in range {min_port}-{max_port}")
    
    def get_port(
        self,
        component_id: str,
        component_type: Literal["agent", "tool", "service"]
    ) -> Optional[int]:
        """
        Get the port allocated for a component.
        
        Args:
            component_id: Unique identifier for the component
            component_type: Type of the component
            
        Returns:
            Allocated port number or None if not allocated
        """
        return self.port_allocations.get(component_type, {}).get(component_id)
    
    def release_port(
        self,
        component_id: str,
        component_type: Literal["agent", "tool", "service"]
    ) -> bool:
        """
        Release a port allocation for a component.
        
        Args:
            component_id: Unique identifier for the component
            component_type: Type of the component
            
        Returns:
            True if the port was released, False otherwise
        """
        if component_id in self.port_allocations.get(component_type, {}):
            del self.port_allocations[component_type][component_id]
            self._save_port_allocations()
            return True
        return False
    
    def _load_docker_compose(self) -> Dict:
        """
        Load the Docker Compose file if it exists.
        
        Returns:
            Dict with the Docker Compose configuration or empty dict if not found
        """
        try:
            if os.path.exists(self.compose_file):
                with open(self.compose_file, 'r') as f:
                    return yaml.safe_load(f) or {"version": "3.8", "services": {}}
            else:
                return {"version": "3.8", "services": {}}
        except Exception as e:
            print(f"⚠️ Error loading Docker Compose file: {e}")
            return {"version": "3.8", "services": {}}
    
    def _save_docker_compose(self, config: Dict):
        """
        Save the Docker Compose configuration to file.
        
        Args:
            config: Docker Compose configuration dict
        """
        try:
            # Create directory if it doesn't exist
            compose_dir = os.path.dirname(self.compose_file)
            if compose_dir and not os.path.exists(compose_dir):
                os.makedirs(compose_dir)
            
            with open(self.compose_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"⚠️ Error saving Docker Compose file: {e}")
    
    def add_to_docker_compose(
        self,
        component_id: str,
        component_type: Literal["agent", "tool", "service"],
        image: Optional[str] = None,
        build_path: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[list] = None,
        depends_on: Optional[list] = None,
        command: Optional[str] = None,
        networks: Optional[list] = None,
        http_port: Optional[int] = None,
        mcp_port: Optional[int] = None
    ) -> bool:
        """
        Add or update a component in the Docker Compose file.
        
        Args:
            component_id: Unique identifier for the component
            component_type: Type of the component
            image: Optional Docker image to use
            build_path: Optional path to build context
            environment: Optional environment variables
            volumes: Optional volumes to mount
            depends_on: Optional services to depend on
            command: Optional command to run
            networks: Optional networks to join
            http_port: Optional HTTP port to expose
            mcp_port: Optional MCP port to expose
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load the current Docker Compose config
            compose_config = self._load_docker_compose()
            
            # Ensure services section exists
            if "services" not in compose_config:
                compose_config["services"] = {}
            
            # Ensure networks section exists
            if "networks" not in compose_config:
                compose_config["networks"] = {
                    "agent_network": {"driver": "bridge"}
                }
            
            # Check if we need to allocate ports
            if http_port is None:
                http_port = self.allocate_port(f"{component_id}_http", component_type)
            
            if mcp_port is None and component_type != "service":
                mcp_port = self.allocate_port(f"{component_id}_mcp", component_type)
            
            # Create the service configuration
            service_config = {}
            
            # Set image or build
            if image:
                service_config["image"] = image
            elif build_path:
                service_config["build"] = {
                    "context": build_path,
                    "dockerfile": "Dockerfile"
                }
            
            # Set environment variables
            service_env = environment or {}
            
            # Add standard environment variables
            service_env.update({
                "PORT": str(http_port),
                "HOST": component_id
            })
            
            # Add MCP port for agents and tools
            if component_type != "service" and mcp_port:
                service_env["MCP_PORT"] = str(mcp_port)
            
            # Add Redis for agents
            if component_type == "agent":
                service_env.update({
                    "REDIS_HOST": "redis",
                    "REDIS_PORT": "6379"
                })
            
            # Add registry URL
            service_env["REGISTRY_URL"] = "http://registry:9401"
            
            service_config["environment"] = [f"{k}={v}" for k, v in service_env.items()]
            
            # Set ports
            ports = []
            if http_port:
                ports.append(f"{http_port}:8000")
            if mcp_port:
                ports.append(f"{mcp_port}:9000")
            
            if ports:
                service_config["ports"] = ports
            
            # Set volumes
            if volumes:
                service_config["volumes"] = volumes
            
            # Set dependencies
            depends = depends_on or []
            
            # Add standard dependencies
            if component_type == "agent":
                depends.extend(["redis", "registry"])
            else:
                depends.append("registry")
            
            # Remove duplicates
            depends = list(set(depends))
            service_config["depends_on"] = depends
            
            # Set command
            if command:
                service_config["command"] = command
            
            # Set networks
            service_config["networks"] = networks or ["agent_network"]
            
            # Set restart policy
            service_config["restart"] = "always"
            
            # Add the service to the config
            compose_config["services"][component_id] = service_config
            
            # Save the updated config
            self._save_docker_compose(compose_config)
            
            return True
        
        except Exception as e:
            print(f"⚠️ Error adding to Docker Compose: {e}")
            return False


# Singleton instance of the port manager
_port_manager_instance = None

def get_port_manager(
    port_ranges: Optional[Dict[str, Tuple[int, int]]] = None,
    port_file: Optional[str] = None,
    compose_file: Optional[str] = None
) -> PortManager:
    """
    Get or create the singleton instance of the port manager.
    
    Args:
        port_ranges: Optional custom port ranges for each component type
        port_file: Optional path to the port allocation file
        compose_file: Optional path to the Docker Compose file
        
    Returns:
        Singleton instance of the port manager
    """
    global _port_manager_instance
    
    if _port_manager_instance is None:
        _port_manager_instance = PortManager(
            port_ranges=port_ranges,
            port_file=port_file,
            compose_file=compose_file
        )
    
    return _port_manager_instance