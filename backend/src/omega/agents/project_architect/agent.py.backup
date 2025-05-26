# agents/project_architect/agent.py
import os
from typing import Dict, Any, List, Optional
import aiohttp

from omega.core.registerable_dual_mode_agent import RegisterableDualModeAgent
from omega.core.models.task_models import TaskEnvelope

class ProjectArchitectAgent(RegisterableDualModeAgent):
    """
    Project Architect Agent that designs software architecture, project structures,
    and technical specifications based on requirements.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="project_architect",
            tool_name="project_architect",
            description="Designs software architecture and project structures based on requirements",
            version="1.0.0",
            skills=["design_architecture", "create_technical_spec", "plan_project_structure"],
            agent_type="agent",
            tags=["architecture", "design", "planning", "project"]
        )
        
        # Get OpenAI API key from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("⚠️ WARNING: OPENAI_API_KEY not set. Architecture design will fail!")
    
    def _register_a2a_capabilities(self):
        """Register A2A skills"""
        # This would be implemented with specific A2A capabilities
        pass
    
    async def discover_documentation_tools(self):
        """
        Discover documentation tools from the registry.
        Returns a list of documentation tools.
        """
        # Try to find tools with documentation tag
        doc_tools = await self.discover_mcp_tools_by_tag("documentation")
        
        # If that fails, try other related tags
        if not doc_tools:
            for tag in ["docs", "reference", "library", "api"]:
                doc_tools = await self.discover_mcp_tools_by_tag(tag)
                if doc_tools:
                    break
        
        return doc_tools
    
    async def get_technical_documentation(self, technology: str) -> str:
        """
        Try to fetch documentation for a specific technology.
        """
        try:
            # First find documentation tools
            doc_tools = await self.discover_documentation_tools()
            
            if not doc_tools:
                return f"No documentation tools found for {technology}"
            
            # Use the first tool we find
            doc_tool = doc_tools[0]
            print(f"🔍 Found documentation tool: {doc_tool['id']}")
            
            # First try to resolve the library ID if it's Context7
            if "context7" in doc_tool["id"].lower() or "documentation" in doc_tool["id"].lower():
                try:
                    # Try Context7-specific API
                    resolve_result = await self.call_mcp_tool(
                        doc_tool["mcp_endpoint"],
                        "resolve_library_id",
                        libraryName=technology
                    )
                    
                    library_id = resolve_result.get("library_id", "")
                    if library_id:
                        # Get the documentation
                        docs_result = await self.call_mcp_tool(
                            doc_tool["mcp_endpoint"],
                            "get_library_docs",
                            context7CompatibleLibraryID=library_id,
                            tokens=5000
                        )
                        
                        return docs_result.get("documentation", f"No documentation found for {technology}")
                except Exception as e:
                    print(f"Error using Context7 API: {str(e)}")
            
            # Generic approach - look for a 'get_docs' or similar capability
            for capability in doc_tool.get("capabilities", []):
                cap_name = capability.get("name", "").lower()
                if "doc" in cap_name or "reference" in cap_name or "info" in cap_name:
                    try:
                        result = await self.call_mcp_tool(
                            doc_tool["mcp_endpoint"],
                            capability["name"],
                            technology=technology
                        )
                        
                        # Extract docs from result
                        if isinstance(result, dict):
                            for key in ["documentation", "docs", "content", "text", "response"]:
                                if key in result:
                                    return result[key]
                        
                        return str(result)
                    except Exception as e:
                        print(f"Error calling {capability['name']}: {str(e)}")
            
            return f"Found documentation tool {doc_tool['id']} but couldn't retrieve docs for {technology}"
            
        except Exception as e:
            return f"Error accessing documentation: {str(e)}"
    
    async def call_openai_api(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Call the OpenAI Responses API with the given messages and optional tools.
        
        Args:
            messages: List of messages in the conversation
            tools: Optional list of tools to enable
            
        Returns:
            OpenAI API response
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        # OpenAI API endpoint
        url = "https://api.openai.com/v1/chat/completions"
        
        # Prepare request payload
        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                # Check if request was successful
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                
                # Parse response
                result = await response.json()
                return result
    
    async def design_architecture(self, requirements: str, tech_stack: List[str] = None, constraints: str = None) -> str:
        """
        Design a software architecture based on requirements and tech stack.
        
        Args:
            requirements: The project requirements
            tech_stack: Optional list of technologies to use
            constraints: Optional constraints to consider
            
        Returns:
            Architecture design with explanation
        """
        tech_stack = tech_stack or []
        constraints = constraints or "No specific constraints."
        
        # Fetch documentation for the tech stack
        tech_docs = {}
        for tech in tech_stack:
            doc = await self.get_technical_documentation(tech)
            if doc and len(doc) > 100:  # Ensure we got meaningful docs
                tech_docs[tech] = doc
        
        # Prepare documentation context
        docs_context = ""
        if tech_docs:
            docs_context = "## Available Technical Documentation\n\n"
            for tech, doc in tech_docs.items():
                # Limit doc size to avoid token limits
                trimmed_doc = doc[:2000] + "..." if len(doc) > 2000 else doc
                docs_context += f"### {tech}\n{trimmed_doc}\n\n"
        
        # Prepare system message with instructions
        system_message = {
            "role": "system",
            "content": (
                "You are an expert software architect specializing in designing robust, scalable "
                "software systems. Your task is to create a comprehensive architecture design "
                "based on the user's requirements and technology constraints.\n\n"
                "For each architecture design, provide:\n"
                "1. A high-level overview of the system\n"
                "2. Key components and their responsibilities\n"
                "3. Data flow and communication patterns\n"
                "4. API contracts between components\n"
                "5. Technology recommendations for each component\n"
                "6. Deployment considerations\n"
                "7. Scalability and performance considerations\n\n"
                "Use diagrams described in text format (e.g., ASCII or Mermaid) to illustrate the architecture.\n"
                f"{docs_context}"
            )
        }
        
        # Prepare user message with requirements
        user_message = {
            "role": "user",
            "content": (
                f"Please design a software architecture for a project with these requirements:\n\n"
                f"{requirements}\n\n"
                f"Tech stack: {', '.join(tech_stack) if tech_stack else 'Open to recommendations'}\n"
                f"Constraints: {constraints}"
            )
        }
        
        # Prepare messages for API call
        messages = [system_message, user_message]
        
        try:
            # Call OpenAI API
            response = await self.call_openai_api(messages)
            
            # Extract response content
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                return "Failed to design architecture. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error designing architecture: {str(e)}"
    
    async def create_technical_spec(self, project_name: str, description: str, architecture: str = None) -> str:
        """
        Create a detailed technical specification document.
        
        Args:
            project_name: The name of the project
            description: Description of the project
            architecture: Optional existing architecture design
            
        Returns:
            Technical specification document
        """
        # Prepare system message with instructions
        system_message = {
            "role": "system",
            "content": (
                "You are an expert software architect specializing in creating comprehensive "
                "technical specification documents. Your task is to create a detailed technical "
                "specification based on the project information provided.\n\n"
                "Include the following sections:\n"
                "1. Project Overview\n"
                "2. Objectives and Goals\n"
                "3. System Architecture\n"
                "4. Functional Requirements\n"
                "5. Non-Functional Requirements\n"
                "6. API Specifications\n"
                "7. Data Models\n"
                "8. Security Considerations\n"
                "9. Deployment Strategy\n"
                "10. Testing Strategy\n"
                "11. Timeline and Milestones\n\n"
                "Provide comprehensive details for each section."
            )
        }
        
        # Prepare user message with project information
        user_content = (
            f"Please create a technical specification document for the following project:\n\n"
            f"Project Name: {project_name}\n"
            f"Description: {description}\n"
        )
        
        if architecture:
            user_content += f"\nExisting Architecture Design:\n{architecture}"
        
        user_message = {
            "role": "user",
            "content": user_content
        }
        
        # Prepare messages for API call
        messages = [system_message, user_message]
        
        try:
            # Call OpenAI API
            response = await self.call_openai_api(messages)
            
            # Extract response content
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                return "Failed to create technical specification. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error creating technical specification: {str(e)}"
    
    async def plan_project_structure(self, project_type: str, tech_stack: List[str], features: List[str]) -> str:
        """
        Create a project directory structure and file organization.
        
        Args:
            project_type: Type of project (e.g., web app, mobile app, API)
            tech_stack: List of technologies used
            features: List of features to implement
            
        Returns:
            Project structure plan
        """
        # Fetch documentation for the tech stack
        tech_docs = {}
        for tech in tech_stack:
            doc = await self.get_technical_documentation(tech)
            if doc and len(doc) > 100:  # Ensure we got meaningful docs
                tech_docs[tech] = doc
        
        # Prepare documentation context
        docs_context = ""
        if tech_docs:
            docs_context = "## Available Technical Documentation\n\n"
            for tech, doc in tech_docs.items():
                # Limit doc size to avoid token limits
                trimmed_doc = doc[:1500] + "..." if len(doc) > 1500 else doc
                docs_context += f"### {tech}\n{trimmed_doc}\n\n"
        
        # Prepare system message with instructions
        system_message = {
            "role": "system",
            "content": (
                "You are an expert software architect specializing in project organization and structure. "
                "Your task is to create a comprehensive project structure based on best practices for "
                "the given technology stack and project type.\n\n"
                "For each project structure, provide:\n"
                "1. Directory structure with explanation of each directory's purpose\n"
                "2. Key files and their responsibilities\n"
                "3. Configuration files needed\n"
                "4. Module organization\n"
                "5. Best practices for the specific tech stack\n"
                "6. Recommended third-party libraries and tools\n\n"
                "Present the directory structure in a clear, hierarchical format.\n"
                f"{docs_context}"
            )
        }
        
        # Prepare user message with project requirements
        user_message = {
            "role": "user",
            "content": (
                f"Please create a project structure for a {project_type} with the following details:\n\n"
                f"Tech Stack: {', '.join(tech_stack)}\n"
                f"Features to Implement: {', '.join(features)}\n\n"
                f"I need a detailed directory structure, key files, and organization that follows "
                f"best practices for this tech stack and makes it easy to implement the specified features."
            )
        }
        
        # Prepare messages for API call
        messages = [system_message, user_message]
        
        try:
            # Call OpenAI API
            response = await self.call_openai_api(messages)
            
            # Extract response content
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                return "Failed to plan project structure. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error planning project structure: {str(e)}"
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """Process a task from any source (Redis stream or A2A)"""
        try:
            # Extract input from the task envelope
            input_data = env.input or {}
            input_text = input_data.get("text", "")
            
            # Check if this is an architecture design request
            if any(x in input_text.lower() for x in ["design architecture", "system architecture", "software architecture"]):
                # Extract tech stack if mentioned
                tech_stack = []
                common_techs = ["react", "node", "python", "django", "flask", "fastapi", "aws", "azure", 
                                "kubernetes", "docker", "mongodb", "postgresql", "typescript", "angular", 
                                "vue", "graphql", "rest", "microservices", "serverless"]
                
                for tech in common_techs:
                    if tech in input_text.lower():
                        tech_stack.append(tech)
                
                # Extract constraints
                constraints = None
                if "constraints:" in input_text.lower():
                    parts = input_text.lower().split("constraints:")
                    if len(parts) > 1:
                        constraints = parts[1].strip()
                
                # Design the architecture
                architecture = await self.design_architecture(
                    requirements=input_text,
                    tech_stack=tech_stack,
                    constraints=constraints
                )
                
                env.output = {"text": architecture}
                env.status = "COMPLETED"
                
            elif any(x in input_text.lower() for x in ["technical spec", "technical specification", "spec document"]):
                # Extract project name and description
                project_name = "Unnamed Project"
                description = input_text
                
                # Check for project name in format "Project Name: X"
                if "project name:" in input_text.lower():
                    parts = input_text.split("project name:", 1)
                    if len(parts) > 1:
                        project_name_part = parts[1].strip()
                        if "\n" in project_name_part:
                            project_name = project_name_part.split("\n", 1)[0].strip()
                        else:
                            project_name = project_name_part
                
                # Create the technical specification
                spec_doc = await self.create_technical_spec(
                    project_name=project_name,
                    description=description
                )
                
                env.output = {"text": spec_doc}
                env.status = "COMPLETED"
                
            elif any(x in input_text.lower() for x in ["project structure", "directory structure", "file organization"]):
                # Extract project type
                project_type = "web application"  # Default
                if "mobile" in input_text.lower():
                    project_type = "mobile application"
                elif "api" in input_text.lower() or "backend" in input_text.lower():
                    project_type = "API / backend service"
                elif "desktop" in input_text.lower():
                    project_type = "desktop application"
                
                # Extract tech stack
                tech_stack = []
                common_techs = ["react", "node", "python", "django", "flask", "fastapi", "javascript", 
                                "typescript", "angular", "vue", "express", "next.js", "nest.js"]
                
                for tech in common_techs:
                    if tech in input_text.lower():
                        tech_stack.append(tech)
                
                # Extract features (very simple approach)
                features = ["user authentication", "data management"]
                if "features:" in input_text.lower():
                    parts = input_text.lower().split("features:")
                    if len(parts) > 1:
                        features_text = parts[1].strip()
                        features = [f.strip() for f in features_text.split(",")]
                
                # Create the project structure plan
                structure_plan = await self.plan_project_structure(
                    project_type=project_type,
                    tech_stack=tech_stack,
                    features=features
                )
                
                env.output = {"text": structure_plan}
                env.status = "COMPLETED"
                
            else:
                # Default response for unknown queries
                env.output = {
                    "text": (
                        "I'm a Project Architect agent. I can help with:\n"
                        "- Designing system architecture based on requirements\n"
                        "- Creating technical specification documents\n"
                        "- Planning project directory structures\n\n"
                        "Please specify what type of architectural design or planning you need."
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
    # Create and run the project architect agent
    agent = ProjectArchitectAgent()
    agent.run()