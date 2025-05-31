# D:/Repos/o.m.e.g.a/backend/src/omega/tools/code_analyzer/tool.py

"""
CodeAnalyzerTool: A RegisterableMCPTool for the OMEGA Framework.
Scans repositories, identifies languages, parses files, extracts structure and dependencies.

Author: The OMEGA Dream Team
Version: 1.0.0
"""

import os
import ast
import logging
import uuid
import time
import threading
import requests
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

# FastAPI and Pydantic imports
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Try importing optional dependencies
try:
    import esprima
    HAS_ESPRIMA = True
except ImportError:
    HAS_ESPRIMA = False
    esprima = None

try:
    from pymongo import MongoClient
    HAS_MONGODB = True
except ImportError:
    HAS_MONGODB = False
    MongoClient = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC DATA MODELS
# ============================================================================

class Component(BaseModel):
    """Represents a code component (file, class, function, etc.)"""
    type: str = Field(..., description="Type of component (file, class, function, export)")
    name: str = Field(..., description="Name of the component")
    path: str = Field(..., description="Full path identifier for the component")
    line_number: Optional[int] = Field(None, description="Line number where component is defined")
    size: Optional[int] = Field(None, description="Size in lines of code")

class Dependency(BaseModel):
    """Represents a dependency relationship between components"""
    source: str = Field(..., description="Source component path")
    target: str = Field(..., description="Target component or module being depended on")
    dependency_type: str = Field("import", description="Type of dependency (import, call, inheritance)")
    line_number: Optional[int] = Field(None, description="Line number where dependency occurs")

class AnalysisResult(BaseModel):
    """Complete analysis result for a repository"""
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    repository_path: str = Field(..., description="Path to the analyzed repository")
    timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    file_tree: Dict[str, Any] = Field(default_factory=dict, description="Nested file structure")
    components: List[Component] = Field(default_factory=list, description="Extracted components")
    dependencies: List[Dependency] = Field(default_factory=list, description="Dependency relationships")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Analysis statistics")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during analysis")

class ToolCapability(BaseModel):
    """Model for MCP tool capability"""
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    returns: Dict[str, Any] = {}

# ============================================================================
# MONGODB CLIENT (OPTIONAL)
# ============================================================================

class SimpleMongoClient:
    """Simple MongoDB client wrapper"""
    def __init__(self, connection_string: str, database_name: str):
        if not HAS_MONGODB:
            logger.warning("MongoDB client not available - results will not be persisted")
            self.db = None
            return
            
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            logger.info(f"Connected to MongoDB: {database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.db = None
    
    def insert_one(self, collection_name: str, document: dict):
        """Insert a document into the specified collection"""
        if self.db is None:
            logger.warning("MongoDB not available - skipping document insertion")
            return
        
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            logger.info(f"Inserted document with ID: {result.inserted_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to insert document: {e}")
            return None

# ============================================================================
# REGISTERABLE MCP TOOL - SELF CONTAINED
# ============================================================================

class RegisterableMCPTool:
    """
    Self-contained MCP tool that automatically registers with a central registry
    and sends periodic heartbeats to maintain its registered status.
    """
    
    def __init__(
        self,
        tool_id: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        tags: List[str] = None
    ):
        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.version = version
        self.tags = tags or []
        
        # FastAPI setup
        self.app = FastAPI(
            title=f"OMEGA {name}",
            description=description,
            version=version
        )
        
        # Enable CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Registry service configuration
        self.registry_url = os.getenv("REGISTRY_URL", "http://mcp_registry:9402")
        self.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
        
        # Flag to control the heartbeat thread
        self.running = False
        self.heartbeat_thread = None
        self.registered = False
        
        # Store capabilities and tools
        self.capabilities = []
        self.tools = {}
        
        # Set up routes
        self._setup_routes()
        
        # Set up lifespan
        self.app.router.lifespan_context = self._lifespan
    
    def _setup_routes(self):
        """Set up FastAPI routes"""
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "tool_id": self.tool_id,
                "name": self.name,
                "registered": self.registered,
                "capabilities": len(self.capabilities),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/capabilities")
        async def get_capabilities():
            """Return this tool's capabilities"""
            return {"capabilities": [cap.model_dump() for cap in self.capabilities]}
        
        @self.app.post("/call/{tool_name}")
        async def call_tool(tool_name: str, payload: dict):
            """Call a specific tool function"""
            if tool_name not in self.tools:
                return {"error": f"Tool '{tool_name}' not found"}
            
            try:
                func = self.tools[tool_name]["func"]
                params = payload.get("parameters", {})
                result = func(**params)
                return {"result": result, "success": True}
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {"error": str(e), "success": False}
    
    @asynccontextmanager
    async def _lifespan(self, _app):
        """Lifespan context manager to handle startup and shutdown events."""
        logger.info(f"🚀 Starting {self.name}")
        
        # Wait a bit for other services to be ready
        await asyncio.sleep(5)
        
        # Register with the registry service
        if self.register_with_registry():
            # Start sending heartbeats
            self.start_heartbeat_thread()
        
        yield
        
        # Stop the heartbeat thread and unregister
        self.stop_heartbeat_thread()
        self.unregister()
        logger.info(f"👋 {self.name} shutdown complete")
    
    def add_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Dict[str, Any] = None
    ):
        """Add a tool to the MCP server and update capabilities."""
        
        # Store the tool
        self.tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {}
        }
        
        # Update capabilities
        capability = ToolCapability(
            name=name,
            description=description,
            parameters=parameters or {},
            returns={"type": "object"}  # Default return type
        )
        
        self.capabilities.append(capability)
        logger.info(f"🔧 Added tool '{name}' to {self.name}")
        
        # If we're already registered, update the registration
        if self.registered:
            self.register_with_registry()
    
    def _get_registration_payload(self):
        """Create the registration payload for the registry service"""
        host = os.getenv("HOST", "code_analyzer")
        port = int(os.getenv("PORT", "8000"))
        
        return {
            "id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": [cap.model_dump() for cap in self.capabilities],
            "host": host,
            "port": port,
            "tags": self.tags,
            "endpoints": {
                "health": f"http://{host}:{port}/health",
                "capabilities": f"http://{host}:{port}/capabilities"
            }
        }
    
    def register_with_registry(self):
        """Register this tool with the registry service"""
        try:
            payload = self._get_registration_payload()
            response = requests.post(
                f"{self.registry_url}/registry/mcp/register",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ {self.name} registered successfully with registry")
                self.registered = True
                return True
            else:
                logger.error(f"❌ Failed to register {self.name}: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error registering {self.name}: {str(e)}")
            return False
    
    def send_heartbeat(self):
        """Send a heartbeat to the registry service"""
        try:
            response = requests.post(
                f"{self.registry_url}/registry/mcp/heartbeat",
                json={"id": self.tool_id},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"💓 Heartbeat sent for {self.name}")
            else:
                logger.warning(f"⚠️ Heartbeat failed for {self.name}: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Heartbeat error for {self.name}: {str(e)}")
    
    def heartbeat_loop(self):
        """Background thread function to send periodic heartbeats"""
        while self.running:
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)
    
    def unregister(self):
        """Unregister this tool from the registry service"""
        try:
            response = requests.delete(
                f"{self.registry_url}/registry/mcp/unregister/{self.tool_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"👋 {self.name} unregistered from registry")
                self.registered = False
            else:
                logger.warning(f"⚠️ Failed to unregister {self.name}: {response.status_code}")
        
        except Exception as e:
            logger.warning(f"⚠️ Error unregistering {self.name}: {str(e)}")
    
    def start_heartbeat_thread(self):
        """Start the background thread for sending heartbeats"""
        if not self.heartbeat_thread:
            self.running = True
            self.heartbeat_thread = threading.Thread(
                target=self.heartbeat_loop,
                daemon=True
            )
            self.heartbeat_thread.start()
            logger.info(f"💓 Started heartbeat thread for {self.name}")
    
    def stop_heartbeat_thread(self):
        """Stop the heartbeat thread"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)
            self.heartbeat_thread = None
            logger.info(f"🛑 Stopped heartbeat thread for {self.name}")
    
    def run(self):
        """Run the FastAPI server"""
        try:
            port = int(os.getenv("PORT", "8000"))
            logger.info(f"🌟 Starting {self.name} on port {port}")
            uvicorn.run(self.app, host="0.0.0.0", port=port)
        finally:
            # Ensure we stop the heartbeat thread and unregister
            self.stop_heartbeat_thread()
            self.unregister()

# ============================================================================
# CODE ANALYZER CLASSES (SAME AS BEFORE)
# ============================================================================

class CodeAnalyzer:
    """Main analyzer class that orchestrates the repository analysis process."""
    
    def __init__(self, repo_path: str, analysis_id: str):
        """Initialize the CodeAnalyzer."""
        self.repo_path = Path(repo_path)
        self.analysis_id = analysis_id
        self.components: List[Component] = []
        self.dependencies: List[Dependency] = []
        self.file_tree: Dict = {}
        self.errors: List[str] = []
        
        # Validate repository path
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not self.repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")
    
    def _count_files(self, tree: Dict) -> int:
        """Helper method to count files in the file tree."""
        count = 0
        for key, value in tree.items():
            if isinstance(value, dict) and not value:
                count += 1
            elif isinstance(value, dict):
                count += self._count_files(value)
        return count
    
    def build_file_tree(self) -> Dict:
        """Build a nested dictionary representing the file structure."""
        tree = {}
        
        try:
            for root, dirs, files in os.walk(self.repo_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                # Get the relative path from the repo root
                rel_path = os.path.relpath(root, self.repo_path)
                
                # Create nested dict path
                current = tree
                if rel_path != '.':
                    path_parts = rel_path.replace('\\', '/').split('/')
                    for part in path_parts:
                        current = current.setdefault(part, {})
                
                # Add files
                for file in files:
                    if not file.startswith('.') and not file.endswith(('.pyc', '.pyo', '.pyd')):
                        current[file] = {}
        
        except Exception as e:
            error_msg = f"Error building file tree: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return tree
    
    def extract_components_and_dependencies(self):
        """Walk the repo and extract components and dependencies."""
        for root, _, files in os.walk(self.repo_path):
            if any(part.startswith('.') for part in Path(root).parts):
                continue
                
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                
                try:
                    rel_path = file_path.relative_to(self.repo_path)
                    rel_path_str = str(rel_path).replace('\\', '/')
                    
                    # Add basic file component
                    file_component = Component(
                        type="file",
                        name=file_path.name,
                        path=rel_path_str
                    )
                    self.components.append(file_component)
                    
                    # Parse based on file type
                    if file.endswith('.py'):
                        self._parse_python_file(file_path, rel_path_str)
                    elif file.endswith(('.js', '.jsx', '.ts', '.tsx')) and HAS_ESPRIMA:
                        self._parse_javascript_file(file_path, rel_path_str)
                        
                except Exception as e:
                    error_msg = f"Error processing file {file_path}: {e}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
    
    def _parse_python_file(self, file_path: Path, rel_path: str):
        """Parse Python files using ast module."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
                visitor = PythonComponentVisitor(rel_path, self.components, self.dependencies)
                visitor.visit(tree)
            except SyntaxError as e:
                error_msg = f"Syntax error in {rel_path}: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
            
        except Exception as e:
            error_msg = f"Error parsing Python file {rel_path}: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
    
    def _parse_javascript_file(self, file_path: Path, rel_path: str):
        """Parse JavaScript files using esprima."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = esprima.parseModule(content, {'loc': True, 'range': True})
                visitor = JavaScriptComponentVisitor(rel_path, self.components, self.dependencies)
                visitor.visit(tree)
            except Exception as parse_error:
                error_msg = f"JavaScript parsing error in {rel_path}: {parse_error}"  
                logger.error(error_msg)
                self.errors.append(error_msg)
                
        except Exception as e:
            error_msg = f"Error parsing JavaScript file {rel_path}: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)

    def analyze(self) -> AnalysisResult:
        """Performs the code analysis and returns the result."""
        logger.info(f"Starting analysis for repository: {self.repo_path}")
        
        # Build file tree
        self.file_tree = self.build_file_tree()
        
        # Extract components and dependencies
        self.extract_components_and_dependencies()
        
        # Calculate statistics
        stats = {
            "total_files": self._count_files(self.file_tree),
            "total_components": len(self.components),
            "total_dependencies": len(self.dependencies),
            "component_types": {},
            "file_extensions": {}
        }
        
        # Count component types
        for component in self.components:
            comp_type = component.type
            stats["component_types"][comp_type] = stats["component_types"].get(comp_type, 0) + 1
        
        # Count file extensions
        for component in self.components:
            if component.type == "file":
                ext = Path(component.name).suffix.lower()
                if ext:
                    stats["file_extensions"][ext] = stats["file_extensions"].get(ext, 0) + 1
        
        logger.info(f"Analysis complete: {len(self.components)} components, {len(self.dependencies)} dependencies")

        # Create and return the analysis result
        result = AnalysisResult(
            analysis_id=self.analysis_id,
            repository_path=str(self.repo_path),
            file_tree=self.file_tree,
            components=self.components,
            dependencies=self.dependencies,
            statistics=stats,
            errors=self.errors
        )
        
        return result

# ============================================================================
# PYTHON AST VISITOR
# ============================================================================

class PythonComponentVisitor(ast.NodeVisitor):
    """AST visitor for Python files to extract components and dependencies."""
    
    def __init__(self, file_path: str, components: List[Component], dependencies: List[Dependency]):
        self.file_path = file_path
        self.components = components
        self.dependencies = dependencies
        self.current_class = None
        self.current_function = None
        self.imported_names = {}
        self.local_names = set()
        self.aliases = {}
        
    def visit_ClassDef(self, node):
        """Extract class definitions."""
        prev_class = self.current_class
        self.current_class = node.name
        class_path = f"{self.file_path}:{node.name}"
        
        self.components.append(Component(
            type="class",
            name=node.name,
            path=class_path,
            line_number=node.lineno
        ))
        
        self.local_names.add(node.name)
        
        # Check for inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                if base_name in self.aliases:
                    base_name = self.aliases[base_name]
                
                self.dependencies.append(Dependency(
                    source=class_path,
                    target=base_name,
                    dependency_type="inheritance",
                    line_number=node.lineno
                ))
        
        self.generic_visit(node)
        self.current_class = prev_class
        
    def visit_FunctionDef(self, node):
        """Extract function definitions."""
        prev_function = self.current_function
        self.current_function = node.name
        
        if self.current_class:
            func_path = f"{self.file_path}:{self.current_class}.{node.name}"
        else:
            func_path = f"{self.file_path}:{node.name}"
        
        self.components.append(Component(
            type="function",
            name=node.name,
            path=func_path,
            line_number=node.lineno
        ))
        
        self.local_names.add(node.name)
        self.generic_visit(node)
        self.current_function = prev_function
        
    def visit_Import(self, node):
        """Extract import statements."""
        source_path = f"{self.file_path}:{self.current_function}" if self.current_function else self.file_path
        
        for name in node.names:
            module_name = name.name
            alias = name.asname or module_name
            
            self.imported_names[alias] = module_name
            
            if name.asname:
                self.aliases[name.asname] = module_name
            
            self.dependencies.append(Dependency(
                source=source_path,
                target=module_name,
                dependency_type="import",
                line_number=node.lineno
            ))
            
    def visit_ImportFrom(self, node):
        """Extract from import statements."""
        source_path = f"{self.file_path}:{self.current_function}" if self.current_function else self.file_path
        
        if node.module:
            module_name = node.module
            for name in node.names:
                imported_name = name.name
                alias = name.asname or imported_name
                full_name = f"{module_name}.{imported_name}"
                
                self.imported_names[alias] = full_name
                
                if name.asname:
                    self.aliases[name.asname] = full_name
                
                self.dependencies.append(Dependency(
                    source=source_path,
                    target=full_name,
                    dependency_type="import",
                    line_number=node.lineno
                ))

# ============================================================================
# JAVASCRIPT VISITOR (SIMPLIFIED)
# ============================================================================

class JavaScriptComponentVisitor:
    """Simple JavaScript AST visitor for components and dependencies."""
    
    def __init__(self, file_path: str, components: List[Component], dependencies: List[Dependency]):
        self.file_path = file_path
        self.components = components
        self.dependencies = dependencies
        
    def visit(self, node):
        """Visit a node in the AST."""
        if not hasattr(node, 'type'):
            return
            
        # Handle function declarations
        if node.type == 'FunctionDeclaration' and hasattr(node, 'id') and node.id:
            func_name = node.id.name
            line_number = getattr(node.loc, 'start', {}).get('line') if hasattr(node, 'loc') else None
            
            self.components.append(Component(
                type="function",
                name=func_name,
                path=f"{self.file_path}:{func_name}",
                line_number=line_number
            ))
        
        # Recursively visit children
        for key, value in node.__dict__.items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, 'type'):
                        self.visit(item)
            elif hasattr(value, 'type'):
                self.visit(value)

# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

def analyze_repo(repo_path: str, analysis_id: str = None) -> dict:
    """Analyze a code repository and return its structure."""
    if analysis_id is None:
        analysis_id = str(uuid.uuid4())
        
    logger.info(f"Starting code analysis for repo: {repo_path}, analysis_id: {analysis_id}")
    
    try:
        analyzer = CodeAnalyzer(repo_path, analysis_id)
        result = analyzer.analyze()
        
        # Persist to MongoDB if available
        try:
            mongo_url = os.getenv("MONGODB_URL", "mongodb://omega:omegapass@mongo:27017/omega?authSource=admin")
            db = SimpleMongoClient(mongo_url, "omega")
            if db.db is not None:
                db.insert_one("analyses", result.model_dump())
                logger.info(f"Analysis result saved to MongoDB, analysis_id: {analysis_id}")
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")
        
        return result.model_dump()
        
    except Exception as e:
        error_msg = f"Analysis failed for {repo_path}: {str(e)}"
        logger.error(error_msg)
        
        error_result = AnalysisResult(
            analysis_id=analysis_id,
            repository_path=repo_path,
            errors=[error_msg]
        )
        return error_result.model_dump()

def get_analysis_stats(repo_path: str) -> dict:
    """Get quick statistics about a repository without full analysis."""
    try:
        repo = Path(repo_path)
        if not repo.exists():
            return {"error": f"Repository path does not exist: {repo_path}"}
            
        stats = {
            "total_files": 0,
            "file_extensions": {},
            "directory_count": 0,
            "size_bytes": 0
        }
        
        for root, dirs, files in os.walk(repo):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            stats["directory_count"] += len(dirs)
            
            for file in files:
                if not file.startswith('.'):
                    stats["total_files"] += 1
                    
                    ext = Path(file).suffix.lower()
                    if ext:
                        stats["file_extensions"][ext] = stats["file_extensions"].get(ext, 0) + 1
                    else:
                        stats["file_extensions"]["no_extension"] = stats["file_extensions"].get("no_extension", 0) + 1
                    
                    try:
                        file_path = Path(root) / file
                        stats["size_bytes"] += file_path.stat().st_size
                    except:
                        pass
        
        stats["size_mb"] = round(stats["size_bytes"] / (1024 * 1024), 2)
        return stats
        
    except Exception as e:
        return {"error": f"Failed to get repository stats: {str(e)}"}

def health_check() -> dict:
    """Health check function for container deployment"""
    return {
        "status": "healthy",
        "tool_id": "code_analyzer",
        "capabilities": ["python_analysis", "repository_stats"],
        "optional_dependencies": {
            "esprima": HAS_ESPRIMA,
            "mongodb": HAS_MONGODB
        },
        "javascript_analysis": HAS_ESPRIMA,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# We need to import asyncio at module level for the lifespan handler
import asyncio

if __name__ == "__main__":
    print("🔍 OMEGA Code Analyzer Tool Starting Up!")
    print(f"📊 Python AST Analysis: ✅ Available")
    print(f"📊 JavaScript Analysis: {'✅ Available' if HAS_ESPRIMA else '❌ esprima not installed'}")
    print(f"💾 MongoDB Persistence: {'✅ Available' if HAS_MONGODB else '❌ pymongo not installed'}")
    print()
    
    # Create and configure the tool
    tool = RegisterableMCPTool(
        tool_id="code_analyzer",
        name="Code Analyzer",
        description="Analyzes code repositories for structure and dependencies, supporting Python and JavaScript",
        version="1.0.0",
        tags=["analysis", "code", "repository", "dependencies", "python", "javascript"]
    )

    # Add tool functions
    tool.add_tool(
        name="analyze",
        description="Perform deep analysis of a code repository",
        func=analyze_repo,
        parameters={
            "repo_path": {
                "type": "string", 
                "description": "Path to the local repository to analyze"
            },
            "analysis_id": {
                "type": "string", 
                "description": "Unique ID for this analysis (optional - will generate if not provided)",
                "required": False
            }
        }
    )

    tool.add_tool(
        name="get_stats",
        description="Get quick statistics about a repository without full analysis",
        func=get_analysis_stats,
        parameters={
            "repo_path": {
                "type": "string", 
                "description": "Path to the local repository"
            }
        }
    )

    tool.add_tool(
        name="health",
        description="Check the health status of the code analyzer tool",
        func=health_check,
        parameters={}
    )

    # Run the tool server
    logger.info("🚀 Starting Code Analyzer MCP Tool Server...")
    tool.run()