# agents/code_generator/agent.py
import os
from typing import Dict, Any, List, Optional
import aiohttp
from openai import OpenAI

from omega.core.registerable_dual_mode_agent import RegisterableDualModeAgent
from omega.core.models.task_models import TaskEnvelope

class CodeGeneratorAgent(RegisterableDualModeAgent):
    """
    A specialized agent that generates code based on natural language requests,
    leveraging Context7 for up-to-date library documentation and OpenAI for code generation.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="code_generator",
            tool_name="code_generator",
            description="Generates high-quality code based on requirements, consulting latest documentation",
            version="1.0.0",
            skills=["generate_code", "explain_code", "refactor_code"],
            agent_type="agent",
            tags=["code", "programming", "development"]
        )
        
        # Get OpenAI API key from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("⚠️ WARNING: OPENAI_API_KEY not set. Code generation will fail!")

        self.client = OpenAI()
    
    def _register_a2a_capabilities(self):
        """Register A2A skills"""
        # This would be implemented with specific A2A capabilities
        pass
    
    async def fetch_library_docs(self, library_name: str, topic: Optional[str] = None) -> str:
        """
        Fetch documentation for a specific library using Context7 tool.
        
        Args:
            library_name: Name of the library to fetch docs for
            topic: Optional specific topic to focus on
            
        Returns:
            Documentation text
        """
        try:
            # First, resolve the library ID using Context7
            context7_tools = await self.discover_mcp_tools_by_tag("documentation")
            if not context7_tools:
                return f"No documentation tools found for {library_name}"
            
            context7_tool = context7_tools[0]
            
            # First call: Resolve the library ID
            resolve_result = await self.call_mcp_tool(
                context7_tool["mcp_endpoint"],
                "resolve_library_id",
                libraryName=library_name
            )
            
            library_id = resolve_result.get("library_id", "")
            if not library_id:
                return f"Could not resolve library ID for {library_name}"
            
            # Second call: Get the actual documentation
            docs_params = {
                "context7CompatibleLibraryID": library_id,
                "tokens": 5000
            }
            
            if topic:
                docs_params["topic"] = topic
                
            docs_result = await self.call_mcp_tool(
                context7_tool["mcp_endpoint"],
                "get_library_docs",
                **docs_params
            )
            
            return docs_result.get("documentation", f"No documentation found for {library_name}")
            
        except Exception as e:
            return f"Error fetching documentation: {str(e)}"
    
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
                     
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        response = self.client.responses.create(
            model="gpt-4.1",
            input="Write a one-sentence bedtime story about a unicorn."
        )
        
        return response.output_text

    async def generate_code(self, language: str, requirements: str, library_docs: Dict[str, str] = None) -> str:
        """
        Generate code based on requirements, using OpenAI Responses API.
        
        Args:
            language: Programming language to generate code in
            requirements: Natural language description of what the code should do
            library_docs: Optional dictionary of library documentation
            
        Returns:
            Generated code with explanations
        """
        library_docs = library_docs or {}
        
        # Prepare system message with instructions
        system_message = {
            "role": "system",
            "content": (
                "You are an expert software developer specializing in generating high-quality code. "
                "Your task is to generate well-structured, efficient, and documented code based on the user's requirements. "
                "Follow these guidelines:\n"
                "1. Write code that is idiomatic for the specified language\n"
                "2. Include appropriate error handling\n"
                "3. Add comments explaining key sections\n"
                "4. Use modern best practices\n"
                "5. Format your response with proper markdown code blocks\n"
                "6. After the code, include a brief explanation of how it works\n"
                "7. When using libraries, follow the documentation provided"
            )
        }
        
        # Add library documentation to system message if available
        if library_docs:
            docs_content = "Here is the latest documentation for the requested libraries:\n\n"
            for lib_name, doc in library_docs.items():
                # Limit doc size to avoid token limits
                trimmed_doc = doc[:3000] + "..." if len(doc) > 3000 else doc
                docs_content += f"## {lib_name} Documentation\n{trimmed_doc}\n\n"
            
            system_message["content"] += f"\n\n{docs_content}"
        
        # Prepare user message with requirements
        user_message = {
            "role": "user",
            "content": (
                f"Please generate {language} code that satisfies these requirements:\n\n"
                f"{requirements}\n\n"
                f"If libraries are mentioned, use the documentation provided. "
                f"If no specific libraries are mentioned, use standard libraries or suggest appropriate ones."
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
                return "Failed to generate code. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error generating code: {str(e)}"
    
    async def explain_code(self, code: str, detailed: bool = False) -> str:
        """
        Explain existing code using OpenAI Responses API.
        
        Args:
            code: The code to explain
            detailed: Whether to provide a detailed explanation
            
        Returns:
            Explanation of the code
        """
        # Prepare messages for API call
        system_message = {
            "role": "system",
            "content": (
                "You are an expert software developer specializing in explaining code. "
                "Your task is to provide clear, concise explanations of code. "
                f"{'Provide a detailed explanation covering all aspects of the code.' if detailed else 'Focus on the high-level functionality and key components.'}"
            )
        }
        
        user_message = {
            "role": "user",
            "content": f"Please explain this code:\n\n```\n{code}\n```"
        }
        
        messages = [system_message, user_message]
        
        try:
            # Call OpenAI API
            response = await self.call_openai_api(messages)
            
            # Extract response content
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                return "Failed to explain code. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error explaining code: {str(e)}"
    
    async def refactor_code(self, code: str, instructions: str) -> str:
        """
        Refactor existing code using OpenAI Responses API.
        
        Args:
            code: The code to refactor
            instructions: Instructions for refactoring
            
        Returns:
            Refactored code with explanation
        """
        # Prepare messages for API call
        system_message = {
            "role": "system",
            "content": (
                "You are an expert software developer specializing in code refactoring. "
                "Your task is to improve existing code based on the user's instructions. "
                "Focus on improving readability, efficiency, and best practices. "
                "Provide the refactored code and explain the changes made."
            )
        }
        
        user_message = {
            "role": "user",
            "content": (
                f"Please refactor this code according to these instructions: {instructions}\n\n"
                f"```\n{code}\n```"
            )
        }
        
        messages = [system_message, user_message]
        
        try:
            # Call OpenAI API
            response = await self.call_openai_api(messages)
            
            # Extract response content
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                return "Failed to refactor code. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error refactoring code: {str(e)}"
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """Process a task from any source (Redis stream or A2A)"""
        try:
            # Extract input from the task envelope
            input_data = env.input or {}
            input_text = input_data.get("text", "")
            
            # Get any structured parameters if available
            params = input_data.get("params", {})
            language = params.get("language", "python")  # Default to Python
            libraries = params.get("libraries", [])
            
            # Extract parameters from input text if not provided structurally
            if not params:
                # Default to Python unless specified
                if "javascript" in input_text.lower() or "js" in input_text.lower():
                    language = "javascript"
                elif "typescript" in input_text.lower() or "ts" in input_text.lower():
                    language = "typescript"
                elif "python" in input_text.lower():
                    language = "python"
                
                # Extract libraries if mentioned
                common_libs = ["fastapi", "react", "tensorflow", "pandas", "numpy", "express", "nextjs", "vue"]
                for lib in common_libs:
                    if lib in input_text.lower() and lib not in libraries:
                        libraries.append(lib)
            
            # Check if this is a code generation request
            if "generate" in input_text.lower() and "code" in input_text.lower():
                # Fetch documentation for each requested library
                library_docs = {}
                for library in libraries:
                    docs = await self.fetch_library_docs(library)
                    library_docs[library] = docs
                
                # Generate the code
                code_result = await self.generate_code(
                    language=language,
                    requirements=input_text,
                    library_docs=library_docs
                )
                
                env.output = {"text": code_result}
                env.status = "COMPLETED"
                
            elif "explain" in input_text.lower() and "code" in input_text.lower():
                # Extract code from input text
                # This is very basic and would need improvement for real use
                code_parts = input_text.split("```")
                if len(code_parts) >= 3:
                    # Get code from between ``` markers
                    code = code_parts[1]
                    # Remove language identifier if present
                    if code.strip().startswith(language):
                        code = code.strip()[len(language):].strip()
                    
                    # Check if detailed explanation requested
                    detailed = "detail" in input_text.lower() or "thorough" in input_text.lower()
                    
                    # Explain the code
                    explanation = await self.explain_code(code, detailed)
                    env.output = {"text": explanation}
                else:
                    env.output = {"text": "Please provide the code to explain between ``` markers."}
                
                env.status = "COMPLETED"
                
            elif "refactor" in input_text.lower() and "code" in input_text.lower():
                # Extract code and instructions
                code_parts = input_text.split("```")
                if len(code_parts) >= 3:
                    # Get code from between ``` markers
                    code = code_parts[1]
                    # Get instructions from before the code block
                    instructions = code_parts[0].replace("refactor", "").strip()
                    
                    # Refactor the code
                    refactored = await self.refactor_code(code, instructions)
                    env.output = {"text": refactored}
                else:
                    env.output = {"text": "Please provide the code to refactor between ``` markers."}
                
                env.status = "COMPLETED"
                
            else:
                # Default response for unknown queries
                env.output = {
                    "text": (
                        "I'm a code generator agent. I can help with:\n"
                        "- Generating code based on requirements\n"
                        "- Explaining code logic\n"
                        "- Refactoring existing code\n\n"
                        "Please specify what type of code you need, the programming language, "
                        "and any libraries or frameworks to use."
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
    # Create and run the code generator agent
    agent = CodeGeneratorAgent()
    agent.run()