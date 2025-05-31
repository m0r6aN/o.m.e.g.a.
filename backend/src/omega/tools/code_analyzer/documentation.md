# CodeAnalyzerTool Documentation

## Overview

The CodeAnalyzerTool is a RegisterableMCPTool for the OMEGA Framework that analyzes code repositories to extract structure and dependencies. This tool scans repositories, identifies language types, parses files, extracts components (files, classes, functions), and maps dependencies between them.

## Features

- **Repository Structure Extraction**: Builds a file tree representing the repository structure
- **Multiple Language Support**: 
  - Python parsing using the `ast` module
  - JavaScript parsing using `esprima`
- **Component Extraction**:
  - Files
  - Classes
  - Functions/Methods
  - Exports (JavaScript)
- **Dependency Mapping**:
  - Import statements
  - Function calls
  - Class instantiations
  - Inheritance
- **Resolution of Cross-File Dependencies**: Maps imported modules to their actual file paths
- **MongoDB Integration**: Persists analysis results to a MongoDB database
- **Error Handling**: Gracefully handles parsing errors without crashing
- **Path Normalization**: Uses consistent relative paths with forward slashes

## Architecture

The tool consists of several key components:

1. **CodeAnalyzer**: Main class that orchestrates the analysis process
   - Builds file tree
   - Coordinates file parsing
   - Manages component and dependency tracking

2. **PythonComponentVisitor**: AST visitor for Python files
   - Extends `ast.NodeVisitor`
   - Extracts components and dependencies from Python code
   - Tracks imported names and aliases

3. **JavaScriptComponentVisitor**: Custom visitor for JavaScript AST
   - Traverses Esprima's AST
   - Extracts components and dependencies from JavaScript code
   - Handles ES6 module imports/exports

4. **DependencyResolver**: Resolves cross-file dependencies
   - Maps import statements to actual file paths
   - Resolves function and class references
   - Creates a full dependency graph

## Output Format

The tool outputs an `AnalysisResult` with the following structure:

```json
{
    "analysis_id": "unique-id-for-this-analysis",
    "file_tree": {
        "src": {
            "api.py": {},
            "utils": {
                "helpers.py": {}
            }
        }
    },
    "components": [
        {
            "type": "file",
            "name": "api.py",
            "path": "src/api.py"
        },
        {
            "type": "function",
            "name": "get_user",
            "path": "src/api.py:get_user"
        },
        {
            "type": "class",
            "name": "User",
            "path": "src/models.py:User"
        }
    ],
    "dependencies": [
        {
            "source": "src/api.py:get_user",
            "target": "src/models.py:User"
        },
        {
            "source": "src/api.py",
            "target": "src/utils/helpers.py"
        }
    ]
}
```

## Usage

### As a RegisterableMCPTool

```python
# Import the tool
from code_analyzer_tool import analyze_repo

# Call the analyze function
result = analyze_repo(
    repo_path="/path/to/repository", 
    analysis_id="unique-analysis-id"
)

# Process the results
file_tree = result["file_tree"]
components = result["components"]
dependencies = result["dependencies"]
```

### Integration with OMEGA Framework

The tool automatically registers with the OMEGA Framework MCP registry, making it available to other agents:

```python
# In an OMEGA agent or service
def use_analyzer(repo_path):
    from omega.utils.mcp import call_tool
    
    analysis_id = str(uuid.uuid4())
    result = call_tool(
        "code_analyzer", 
        "analyze", 
        {"repo_path": repo_path, "analysis_id": analysis_id}
    )
    
    return result
```

### Retrieving Analysis Results from MongoDB

```python
from omega.core.utils.db import MongoDBClient

async def get_analysis(analysis_id):
    db = MongoDBClient("mongodb://localhost:27017", "omega")
    result = await db.find_one("analyses", {"analysis_id": analysis_id})
    return result
```

## Performance Considerations

- **Repository Size**: Optimized for repositories with up to 1,000 files
- **Memory Usage**: Builds in-memory representation of components and dependencies
- **Parsing Errors**: Gracefully handles and logs parsing errors, continuing with valid files

## Testing

The tool includes both unit tests and integration tests:

- **Unit Tests**: Test individual components:
  - File tree building
  - Python parsing
  - JavaScript parsing
  - Dependency resolution

- **Integration Tests**: Test end-to-end functionality with sample repositories:
  - Flask applications
  - React applications

## Extension Points

The CodeAnalyzerTool is designed to be extensible:

1. **Additional Language Support**: Add more language parsers by implementing new visitor classes
2. **Enhanced Dependency Resolution**: Improve the dependency resolution algorithms
3. **More Component Types**: Extract additional types of components beyond files, classes, and functions
4. **Visualization**: Add visualization capabilities for the dependency graph
5. **Analysis Reports**: Generate analysis reports or metrics about the codebase

## Error Handling

The tool handles several types of errors:

- **Syntax Errors**: Logs errors but continues processing other files
- **Unicode Errors**: Handles files with encoding issues
- **MongoDB Connection Issues**: Reports errors but returns analysis results regardless

## MongoDB Schema

The tool stores its results in a MongoDB collection called `analyses`, with each document following the `AnalysisResult` Pydantic model schema.

## Dependencies

- **esprima**: JavaScript parser
- **pymongo/motor**: MongoDB client libraries
- **registerable_mcp_tool**: OMEGA Framework MCP tool base class
