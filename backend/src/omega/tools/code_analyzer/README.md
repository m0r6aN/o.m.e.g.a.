# CodeAnalyzerTool

[![OMEGA Framework](https://img.shields.io/badge/OMEGA%20Framework-Compatible-blue)]()
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Compatible-green)]()
[![MongoDB](https://img.shields.io/badge/MongoDB-Required-orange)]()

A RegisterableMCPTool for the OMEGA Framework that analyzes code repositories to extract structure and dependencies.

## Overview

The CodeAnalyzerTool scans repositories, identifies languages (Python/JavaScript), parses files, extracts components (files, classes, functions), and maps dependencies between them. It integrates with the OMEGA Framework's Model Context Protocol (MCP) to expose its capabilities as a tool that can be discovered and used by AI agents.

## Features

- 🔍 **Repository Analysis**: Scans and parses code repositories
- 🌐 **Multiple Language Support**: Python (ast) and JavaScript (esprima)
- 🧩 **Component Extraction**: Files, classes, functions/methods, exports
- 🔗 **Dependency Mapping**: Imports, function calls, class instantiations, inheritance
- 🔄 **Cross-File Resolution**: Maps dependencies across files
- 📊 **Visualization-Ready Output**: JSON format compatible with ReactFlow
- 💾 **MongoDB Integration**: Persists analysis results

## Installation

### Prerequisites

- Python 3.9+
- MongoDB
- OMEGA Framework

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/code-analyzer-tool.git
cd code-analyzer-tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure MongoDB is running:
```bash
# Example with Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## Usage

### As a Standalone Tool

```python
from code_analyzer_tool import analyze_repo
import uuid

# Generate a unique analysis ID
analysis_id = str(uuid.uuid4())

# Analyze a repository
result = analyze_repo(
    repo_path="/path/to/repository",
    analysis_id=analysis_id
)

# Process the results
file_tree = result["file_tree"]
components = result["components"]
dependencies = result["dependencies"]

# Print some stats
print(f"Found {len(components)} components and {len(dependencies)} dependencies")
```

### As an OMEGA MCP Tool

The tool automatically registers with the OMEGA Framework's MCP registry when run:

```bash
# Start the tool
python code_analyzer_tool.py
```

Then it can be used by other agents or services:

```python
# In an OMEGA agent
from omega.utils.mcp import call_tool
import uuid

analysis_id = str(uuid.uuid4())
result = call_tool(
    "code_analyzer",  # tool_id
    "analyze",        # function name
    {
        "repo_path": "/path/to/repository",
        "analysis_id": analysis_id
    }
)

# Access the results from MongoDB
from omega.utils.db import MongoDBClient

async def get_analysis_results(analysis_id):
    db = MongoDBClient("mongodb://localhost:27017", "omega")
    result = await db.find_one("analyses", {"analysis_id": analysis_id})
    return result
```

## Docker Deployment

A Dockerfile is included for easy containerization:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV MCP_PORT=9202
ENV MONGO_URI=mongodb://mongo:27017
ENV MONGO_DB=omega

CMD ["python", "code_analyzer_tool.py"]
```

Build and run:

```bash
docker build -t code-analyzer-tool .
docker run -p 9202:9202 --name code-analyzer-tool code-analyzer-tool
```

## Output Format

The tool returns an `AnalysisResult` object with the following structure:

```json
{
    "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
    "file_tree": {
        "src": {
            "api.py": {},
            "db.py": {},
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
            "target": "src/db.py:query"
        },
        {
            "source": "src/api.py",
            "target": "src/db.py"
        }
    ]
}
```

## Integration with ReactFlow

The analysis results can be easily converted to ReactFlow format for visualization:

```javascript
// In a React component
import React, { useEffect, useState } from 'react';
import ReactFlow from 'react-flow-renderer';

function DependencyGraph({ analysisId }) {
  const [elements, setElements] = useState([]);

  useEffect(() => {
    async function fetchData() {
      const response = await fetch(`/api/analysis/${analysisId}`);
      const data = await response.json();
      
      // Convert components to nodes
      const nodes = data.components.map(component => ({
        id: component.path,
        data: { label: component.name },
        position: { x: 0, y: 0 } // You'll need positioning logic
      }));
      
      // Convert dependencies to edges
      const edges = data.dependencies.map((dep, i) => ({
        id: `e${i}`,
        source: dep.source,
        target: dep.target
      }));
      
      setElements([...nodes, ...edges]);
    }
    
    fetchData();
  }, [analysisId]);

  return (
    <div style={{ height: 800 }}>
      <ReactFlow elements={elements} />
    </div>
  );
}
```

## Testing

Run the test suite:

```bash
pytest
```

The tests include:
- Unit tests for individual components
- Integration tests with sample repositories
- Dependency resolution tests

## Performance Considerations

- Optimized for repositories with up to 1,000 files
- Error handling for syntax errors and malformed files
- Logging of parsing/resolution processes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OMEGA Framework for the RegisterableMCPTool infrastructure
- Esprima for JavaScript parsing
- Python's ast module for Python parsing
