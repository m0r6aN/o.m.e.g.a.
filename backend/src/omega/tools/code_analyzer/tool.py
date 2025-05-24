"""
CodeAnalyzerTool: A RegisterableMCPTool for the OMEGA Framework.
Scans repositories, identifies languages, parses files, extracts structure and dependencies.

Author: Claude
Version: 1.0.0
"""

import os
import ast
import logging
import uuid
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import esprima  # For JavaScript parsing
from registerable_mcp_tool import RegisterableMCPTool
from omega.utils.db import MongoDBClient
from omega.core.models.analysis_models import Component, Dependency, AnalysisResult

# Import our enhanced dependency tracking
from enhanced_dependency_tracking import resolve_dependencies

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Main analyzer class that orchestrates the repository analysis process."""
    
    def __init__(self, repo_path: str, analysis_id: str):
        """
        Initialize the CodeAnalyzer.
        
        Args:
            repo_path: Path to the local repository.
            analysis_id: Unique ID for this analysis.
        """
        self.repo_path = Path(repo_path)
        self.analysis_id = analysis_id
        self.components: List[Component] = []
        self.dependencies: List[Dependency] = []
        self.file_tree: Dict = {}
        
d dependencies
        self.extract_components_and_dependencies()
        logger.info(f"Extracted {len(self.components)} components and {len(self.dependencies)} dependencies")
        
        # Create and return the analysis result
        result = AnalysisResult(
            analysis_id=self.analysis_id,
            file_tree=self.file_tree,
            components=self.components,
            dependencies=self.dependencies
        )
        
        logger.info(f"Analysis complete for {self.analysis_id}")
        return result
    
    def _count_files(self, tree: Dict) -> int:
        """Helper method to count files in the file tree."""
        count = 0
        for key, value in tree.items():
            if isinstance(value, dict) and not value:  # Empty dict means it's a file
                count += 1
            elif isinstance(value, dict):
                count += self._count_files(value)
        return count
    
    def build_file_tree(self) -> Dict:
        """
        Build a nested dictionary representing the file structure.
        
        Returns:
            Dict: A nested dictionary representation of the file tree.
        """
        tree = {}
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden directories (like .git)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Get the relative path from the repo root
            rel_path = os.path.relpath(root, self.repo_path)
            
            # Create nested dict path
            current = tree
            if rel_path != '.':
                path_parts = rel_path.replace('\\', '/').split('/')
                for part in path_parts:
                    current = current.setdefault(part, {})
            
            # Add files as empty dicts
            for file in files:
                # Skip hidden files and certain common non-code files
                if file.startswith('.') or file in ('LICENSE', 'README.md'):
                    continue
                
                current[file] = {}
        
        return tree
    
    def extract_components_and_dependencies(self):
        """Walk the repo and extract components and dependencies."""
        for root, _, files in os.walk(self.repo_path):
            # Skip hidden directories
            if any(part.startswith('.') for part in Path(root).parts):
                continue
                
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                
                # Get the relative path from the repo root
                rel_path = file_path.relative_to(self.repo_path)
                rel_path_str = str(rel_path).replace('\\', '/')
                
                # Determine file type and parse accordingly
                if file.endswith('.py'):
                    self._parse_python_file(file_path, rel_path_str)
                elif file.endswith(('.js', '.jsx')):
                    self._parse_javascript_file(file_path, rel_path_str)
                # Could add more language parsers here in the future
    
    def _parse_python_file(self, file_path: Path, rel_path: str):
        """
        Parse Python files using ast module.
        
        Args:
            file_path: Absolute path to the file.
            rel_path: Relative path from the repo root.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Add file as a component
            self.components.append(Component(
                type="file",
                name=file_path.name,
                path=rel_path
            ))
            
            # Parse the file and extract components and dependencies
            tree = ast.parse(content)
            visitor = PythonComponentVisitor(rel_path, self.components, self.dependencies)
            visitor.visit(tree)
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {rel_path}: {e}")
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error in {rel_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {rel_path}: {e}")
    
    def _parse_javascript_file(self, file_path: Path, rel_path: str):
        """
        Parse JavaScript files using esprima.
        
        Args:
            file_path: Absolute path to the file.
            rel_path: Relative path from the repo root.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Add file as a component
            self.components.append(Component(
                type="file",
                name=file_path.name,
                path=rel_path
            ))
            
            # Parse the file and extract components and dependencies
            tree = esprima.parseModule(content, {'loc': True, 'range': True})
            visitor = JavaScriptComponentVisitor(rel_path, self.components, self.dependencies)
            visitor.visit(tree)
            
        except Exception as e:
            logger.error(f"Error parsing JavaScript file {rel_path}: {e}")


class PythonComponentVisitor(ast.NodeVisitor):
    """AST visitor for Python files to extract components and dependencies."""
    
    def __init__(self, file_path: str, components: List[Component], dependencies: List[Dependency]):
        """
        Initialize the visitor.
        
        Args:
            file_path: Relative path of the file being parsed.
            components: List of components to append to.
            dependencies: List of dependencies to append to.
        """
        self.file_path = file_path
        self.components = components
        self.dependencies = dependencies
        self.current_class = None
        self.current_function = None
        self.imported_names = {}  # Maps imported names to their modules
        self.local_names = set()  # Set of names defined in this file
        self.aliases = {}  # Maps import aliases to their real names
        
    def visit_ClassDef(self, node):
        """Extract class definitions."""
        # Store the previous context
        prev_class = self.current_class
        
        # Set current context
        self.current_class = node.name
        class_path = f"{self.file_path}:{node.name}"
        
        # Add the class as a component
        self.components.append(Component(
            type="class",
            name=node.name,
            path=class_path
        ))
        
        # Track this as a local name
        self.local_names.add(node.name)
        
        # Check for class inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                if base_name in self.aliases:
                    base_name = self.aliases[base_name]
                
                self.dependencies.append(Dependency(
                    source=class_path,
                    target=base_name
                ))
        
        # Visit all child nodes
        self.generic_visit(node)
        
        # Restore the previous context
        self.current_class = prev_class
        
    def visit_FunctionDef(self, node):
        """Extract function definitions."""
        # Store the previous context
        prev_function = self.current_function
        
        # Set current context
        self.current_function = node.name
        
        # Determine the full path based on context
        if self.current_class:
            func_path = f"{self.file_path}:{self.current_class}.{node.name}"
        else:
            func_path = f"{self.file_path}:{node.name}"
        
        # Add the function as a component
        self.components.append(Component(
            type="function",
            name=node.name,
            path=func_path
        ))
        
        # Track this as a local name
        self.local_names.add(node.name)
        
        # Visit all child nodes
        self.generic_visit(node)
        
        # Restore the previous context
        self.current_function = prev_function
        
    def visit_Assign(self, node):
        """Track assigned names for potential module aliases."""
        targets = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                targets.append(target.id)
        
        # Check if this might be module alias like `db = database`
        if isinstance(node.value, ast.Name) and node.value.id in self.local_names.union(self.imported_names.keys()):
            for target in targets:
                self.aliases[target] = node.value.id
        
        self.generic_visit(node)
        
    def visit_Import(self, node):
        """Extract import statements."""
        # Current context path
        source_path = f"{self.file_path}:{self.current_function}" if self.current_function else self.file_path
        
        for name in node.names:
            module_name = name.name
            alias = name.asname or module_name
            
            # Track the imported name
            self.imported_names[alias] = module_name
            
            # If using an alias, record it
            if name.asname:
                self.aliases[name.asname] = module_name
            
            # Add dependency
            self.dependencies.append(Dependency(
                source=source_path,
                target=module_name
            ))
            
    def visit_ImportFrom(self, node):
        """Extract from import statements."""
        # Current context path
        source_path = f"{self.file_path}:{self.current_function}" if self.current_function else self.file_path
        
        if node.module:
            module_name = node.module
            for name in node.names:
                imported_name = name.name
                alias = name.asname or imported_name
                full_name = f"{module_name}.{imported_name}"
                
                # Track the imported name
                self.imported_names[alias] = full_name
                
                # If using an alias, record it
                if name.asname:
                    self.aliases[name.asname] = full_name
                
                # Add dependency
                self.dependencies.append(Dependency(
                    source=source_path,
                    target=full_name
                ))
    
    def visit_Call(self, node):
        """Extract function calls."""
        # Current context path
        source_path = f"{self.file_path}:{self.current_function}" if self.current_function else self.file_path
        
        # Extract the function being called
        if isinstance(node.func, ast.Name):
            # Direct function call like func()
            func_name = node.func.id
            
            # Check if this is an imported name
            if func_name in self.imported_names:
                target = self.imported_names[func_name]
            elif func_name in self.aliases:
                target = self.aliases[func_name]
            else:
                target = func_name
                
            self.dependencies.append(Dependency(
                source=source_path,
                target=target
            ))
            
        elif isinstance(node.func, ast.Attribute):
            # Method call like obj.method() or module.func()
            if isinstance(node.func.value, ast.Name):
                # Get the object/module name
                obj_name = node.func.value.id
                method_name = node.func.attr
                
                # Handle different cases
                if obj_name in self.imported_names:
                    # It's an imported module
                    module_name = self.imported_names[obj_name]
                    self.dependencies.append(Dependency(
                        source=source_path,
                        target=f"{module_name}.{method_name}"
                    ))
                elif obj_name in self.aliases:
                    # It's an alias
                    real_name = self.aliases[obj_name]
                    self.dependencies.append(Dependency(
                        source=source_path,
                        target=f"{real_name}.{method_name}"
                    ))
                else:
                    # Standard object.method() call
                    self.dependencies.append(Dependency(
                        source=source_path,
                        target=f"{obj_name}.{method_name}"
                    ))
        
        # Visit arguments
        for arg in node.args:
            self.visit(arg)
        
        # Visit keywords
        for keyword in node.keywords:
            self.visit(keyword.value)


class JavaScriptComponentVisitor:
    """Visitor for JavaScript AST to extract components and dependencies."""
    
    def __init__(self, file_path: str, components: List[Component], dependencies: List[Dependency]):
        """
        Initialize the visitor.
        
        Args:
            file_path: Relative path of the file being parsed.
            components: List of components to append to.
            dependencies: List of dependencies to append to.
        """
        self.file_path = file_path
        self.components = components
        self.dependencies = dependencies
        self.current_class = None
        self.current_function = None
        self.imported_modules = {}  # Maps variable names to imported modules
        self.imported_components = {}  # Maps variable names to imported components
        self.local_names = set()  # Set of names defined in this file
        
    def visit(self, node):
        """Visit a node in the AST."""
        method_name = f'visit_{node.type}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
        
    def generic_visit(self, node):
        """Default visitor for node types without specific visitors."""
        # Process children for node types that have a 'body' attribute
        if hasattr(node, 'body'):
            if isinstance(node.body, list):
                for child in node.body:
                    self.visit(child)
            else:
                self.visit(node.body)
                
        # Process children for node types with 'declaration' attribute
        if hasattr(node, 'declaration') and node.declaration:
            self.visit(node.declaration)
            
        # Process children for node types with 'expression' attribute
        if hasattr(node, 'expression') and node.expression:
            self.visit(node.expression)
            
        # Process function expressions
        if hasattr(node, 'init') and node.init and hasattr(node.init, 'type'):
            if node.init.type in ('FunctionExpression', 'ArrowFunctionExpression'):
                # Store the previous context
                prev_function = self.current_function
                
                # For variable declarations that are functions
                if hasattr(node, 'id') and node.id and hasattr(node.id, 'name'):
                    func_name = node.id.name
                    self.current_function = func_name
                    func_path = f"{self.file_path}:{func_name}"
                    
                    # Add to local names
                    self.local_names.add(func_name)
                    
                    self.components.append(Component(
                        type="function",
                        name=func_name,
                        path=func_path
                    ))
                
                # Visit the function body
                if hasattr(node.init, 'body'):
                    self.visit(node.init.body)
                
                # Restore the previous context
                self.current_function = prev_function
            else:
                self.visit(node.init)
                
        # Process declarations array
        if hasattr(node, 'declarations') and node.declarations:
            for decl in node.declarations:
                self.visit(decl)
                
    def visit_VariableDeclaration(self, node):
        """Process variable declarations."""
        for declaration in node.declarations:
            # Handle the case where a variable is assigned an imported value
            if (hasattr(declaration, 'id') and 
                hasattr(declaration, 'init') and 
                declaration.init and 
                hasattr(declaration.id, 'name')):
                
                var_name = declaration.id.name
                
                # Add to local names
                self.local_names.add(var_name)
                
                # Track assignments from imports (e.g., const { func } = utils)
                if (hasattr(declaration.init, 'type') and 
                    declaration.init.type == 'Identifier' and 
                    declaration.init.name in self.imported_modules):
                    
                    self.imported_modules[var_name] = self.imported_modules[declaration.init.name]
            
            self.visit(declaration)
                
    def visit_ImportDeclaration(self, node):
        """Process import statements."""
        source_path = f"{self.file_path}:{self.current_function}" if self.current_function else self.file_path
        
        # Extract the source module
        if node.source and node.source.value:
            source_value = node.source.value
            
            # Add a dependency to the module itself
            self.dependencies.append(Dependency(
                source=source_path,
                target=source_value
            ))
            
            # Process default imports and named imports
            if hasattr(node, 'specifiers'):
                for specifier in node.specifiers:
                    if specifier.type == 'ImportDefaultSpecifier' and hasattr(specifier, 'local'):
                        local_name = specifier.local.name
                        
                        # Track this import
                        self.imported_modules[local_name] = source_value
                        self.imported_components[local_name] = f"{source_value}:default"
                        
                        # Add dependency
                        self.dependencies.append(Dependency(
                            source=source_path,
                            target=f"{source_value}:default"
                        ))
                        
                    elif specifier.type == 'ImportSpecifier' and hasattr(specifier, 'local') and hasattr(specifier, 'imported'):
                        local_name = specifier.local.name
                        imported_name = specifier.imported.name if hasattr(specifier.imported, 'name') else specifier.imported.value
                        
                        # Track this import
                        self.imported_components[local_name] = f"{source_value}:{imported_name}"
                        
                        # Add dependency
                        self.dependencies.append(Dependency(
                            source=source_path,
                            target=f"{source_value}:{imported_name}"
                        ))
                    
                    elif specifier.type == 'ImportNamespaceSpecifier' and hasattr(specifier, 'local'):
                        # e.g., import * as utils from './utils'
                        local_name = specifier.local.name
                        
                        # Track this namespace import
                        self.imported_modules[local_name] = source_value
                        
                        # Add dependency
                        self.dependencies.append(Dependency(
                            source=source_path,
                            target=f"{source_value}:*"
                        ))
                        
    def visit_ExportDefaultDeclaration(self, node):
        """Process default exports."""
        # Add component if it's a class or function
        if hasattr(node, 'declaration'):
            # Visit the declaration first
            self.visit(node.declaration)
            
            # If it's a named declaration, mark it as exported
            if (hasattr(node.declaration, 'id') and 
                node.declaration.id and 
                hasattr(node.declaration.id, 'name')):
                
                name = node.declaration.id.name
                self.components.append(Component(
                    type="export",
                    name=name,
                    path=f"{self.file_path}:default"
                ))
                
    def visit_ExportNamedDeclaration(self, node):
        """Process named exports."""
        # Visit the declaration if present
        if hasattr(node, 'declaration') and node.declaration:
            self.visit(node.declaration)
            
            # If it's a named declaration, mark it as exported
            if (hasattr(node.declaration, 'id') and 
                node.declaration.id and 
                hasattr(node.declaration.id, 'name')):
                
                name = node.declaration.id.name
                self.components.append(Component(
                    type="export",
                    name=name,
                    path=f"{self.file_path}:{name}"
                ))
        
        # Process export specifiers
        if hasattr(node, 'specifiers'):
            for specifier in node.specifiers:
                if (hasattr(specifier, 'exported') and 
                    hasattr(specifier.exported, 'name')):
                    
                    name = specifier.exported.name
                    self.components.append(Component(
                        type="export",
                        name=name,
                        path=f"{self.file_path}:{name}"
                    ))
                        
    def visit_FunctionDeclaration(self, node):
        """Process function declarations."""
        # Store the previous context
        prev_function = self.current_function
        
        # Set current context
        if hasattr(node, 'id') and node.id and hasattr(node.id, 'name'):
            func_name = node.id.name
            self.current_function = func_name
            
            # Add to local names
            self.local_names.add(func_name)
            
            # Determine the full path based on context
            if self.current_class:
                func_path = f"{self.file_path}:{self.current_class}.{func_name}"
            else:
                func_path = f"{self.file_path}:{func_name}"
            
            # Add the function as a component
            self.components.append(Component(
                type="function",
                name=func_name,
                path=func_path
            ))
            
            # Visit function body
            if hasattr(node, 'body'):
                self.visit(node.body)
        
        # Restore the previous context
        self.current_function = prev_function
        
    def visit_ClassDeclaration(self, node):
        """Process class declarations."""
        # Store the previous context


# Register the tool function
def analyze_repo(repo_path: str, analysis_id: str) -> dict:
    """
    Analyze a code repository and return its structure.
    
    Args:
        repo_path: Path to the local repository.
        analysis_id: Unique ID for this analysis.
        
    Returns:
        dict: Analysis result in dict format.
    """
    logger.info(f"Starting code analysis for repo: {repo_path}, analysis_id: {analysis_id}")
    
    analyzer = CodeAnalyzer(repo_path, analysis_id)
    result = analyzer.analyze()
    
    # Persist to MongoDB
    try:
        db = MongoDBClient("mongodb://localhost:27017", "omega")
        db.insert_one("analyses", result.dict())
        logger.info(f"Analysis result saved to MongoDB, analysis_id: {analysis_id}")
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}")
    
    return result.dict()

# Create and register the tool
tool = RegisterableMCPTool(
    tool_id="code_analyzer",
    name="Code Analyzer",
    description="Analyzes code repositories for structure and dependencies",
    version="1.0.0",
    tags=["analysis", "code"]
)

tool.add_tool(
    name="analyze",
    description="Analyze a repository",
    func=analyze_repo,
    parameters={
        "repo_path": {"type": "string", "description": "Path to local repo"},
        "analysis_id": {"type": "string", "description": "Unique ID for this analysis"}
    }
)

# Run the tool if executed directly
if __name__ == "__main__":
    tool.run()
