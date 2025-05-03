# agents/devops_discovery/agent.py
import os
from typing import Dict, Any, List, Optional
import aiohttp

from omega.core.registerable_dual_mode_agent import RegisterableDualModeAgent
from omega.core.models.task_models import TaskEnvelope

class DevOpsDiscoveryAgent(RegisterableDualModeAgent):
    """
    DevOps Discovery Agent that finds and leverages cloud provider tools
    to orchestrate infrastructure, deployment, and operations tasks.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="devops_discovery",
            tool_name="devops_discovery",
            description="Orchestrates cloud infrastructure and DevOps workflows by discovering provider tools",
            version="1.0.0",
            skills=["provision_infrastructure", "create_deployment_pipeline", "configure_monitoring"],
            agent_type="agent",
            tags=["devops", "cloud", "infrastructure", "deployment", "cicd"]
        )
        
        # Get OpenAI API key from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("⚠️ WARNING: OPENAI_API_KEY not set. DevOps planning will fail!")
        
        # Cloud provider mapping
        self.provider_tags = {
            "aws": ["aws", "amazon", "s3", "ec2", "lambda", "cloudformation", "ecs", "eks"],
            "azure": ["azure", "microsoft", "azurevm", "azurefunctions", "arm", "aks"],
            "gcp": ["gcp", "google", "googlecloud", "gke", "gcf", "googlestorage"],
            "kubernetes": ["kubernetes", "k8s", "helm", "kustomize", "argo"],
            "terraform": ["terraform", "hcl", "tfstate"],
            "ansible": ["ansible", "playbook"],
            "docker": ["docker", "dockerfile", "docker-compose"],
            "github": ["github", "githubactions", "gitops"]
        }
    
    def _register_a2a_capabilities(self):
        """Register A2A skills"""
        # This would be implemented with specific A2A capabilities
        pass
    
    async def identify_providers(self, request_text: str) -> List[str]:
        """
        Identify relevant cloud providers from request text.
        
        Args:
            request_text: User request text
            
        Returns:
            List of identified provider names
        """
        providers = []
        request_lower = request_text.lower()
        
        # Check for explicit provider mentions
        for provider, tags in self.provider_tags.items():
            for tag in tags:
                if tag in request_lower:
                    providers.append(provider)
                    break
        
        # If no providers identified, use OpenAI to infer
        if not providers and self.openai_api_key:
            try:
                inferred_providers = await self._infer_providers(request_text)
                providers.extend(inferred_providers)
            except Exception as e:
                print(f"Error inferring providers: {str(e)}")
        
        # Deduplicate
        return list(set(providers))
    
    async def _infer_providers(self, request_text: str) -> List[str]:
        """
        Use OpenAI to infer relevant cloud providers from request text.
        
        Args:
            request_text: User request text
            
        Returns:
            List of inferred provider names
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI specialized in cloud infrastructure and DevOps. "
                    "Your task is to identify which cloud providers or DevOps tools would be most relevant "
                    "for a given request. Only respond with a comma-separated list of providers from this list: "
                    "aws, azure, gcp, kubernetes, terraform, ansible, docker, github. "
                    "If none are clearly implied, respond with the most likely provider."
                )
            },
            {
                "role": "user",
                "content": request_text
            }
        ]
        
        response = await self.call_openai_api(messages)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse comma-separated list
        if content:
            providers = [p.strip().lower() for p in content.split(",")]
            return [p for p in providers if p in self.provider_tags.keys()]
        
        return []
    
    async def discover_provider_tools(self, providers: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover tools for the specified providers.
        
        Args:
            providers: List of provider names
            
        Returns:
            Dictionary mapping providers to lists of tools
        """
        provider_tools = {}
        
        for provider in providers:
            # Get relevant tags for this provider
            tags = self.provider_tags.get(provider, [provider])
            
            # Discover tools for each tag
            tools = []
            for tag in tags:
                tag_tools = await self.discover_mcp_tools_by_tag(tag)
                tools.extend(tag_tools)
            
            # Deduplicate tools by ID
            unique_tools = {}
            for tool in tools:
                unique_tools[tool["id"]] = tool
            
            provider_tools[provider] = list(unique_tools.values())
        
        return provider_tools
    
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
    
    async def provision_infrastructure(self, request: str, providers: List[str], provider_tools: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Create a plan for provisioning infrastructure using available provider tools.
        
        Args:
            request: Original infrastructure request
            providers: List of identified providers
            provider_tools: Dictionary of available tools for each provider
            
        Returns:
            Infrastructure plan with tool recommendations
        """
        # Build summary of available tools
        tools_summary = ""
        for provider, tools in provider_tools.items():
            if tools:
                tools_summary += f"\n## {provider.upper()} Tools\n"
                for tool in tools:
                    # Format tool capabilities
                    capabilities = ", ".join([cap["name"] for cap in tool.get("capabilities", [])])
                    tools_summary += f"- **{tool['id']}**: {tool.get('description', 'No description')}. Capabilities: {capabilities}\n"
            else:
                tools_summary += f"\n## {provider.upper()} Tools\n- No {provider} tools found in the registry\n"
        
        # Prepare system message with instructions
        system_message = {
            "role": "system",
            "content": (
                "You are an expert DevOps architect specializing in cloud infrastructure. "
                "Your task is to create a comprehensive infrastructure provisioning plan "
                "based on the user's requirements and the available tools in the registry.\n\n"
                "For each plan, provide:\n"
                "1. Overview of the proposed infrastructure\n"
                "2. Step-by-step provisioning plan\n"
                "3. Specific tools to use at each step (from the available tools)\n"
                "4. Sample configurations or commands\n"
                "5. Potential issues and mitigations\n\n"
                "If critical tools are missing from the registry, suggest alternatives or "
                "recommend tools that should be installed.\n\n"
                "Here are the available tools in the registry:\n"
                f"{tools_summary}"
            )
        }
        
        # Prepare user message with request
        user_message = {
            "role": "user",
            "content": f"Please create an infrastructure provisioning plan for this request: {request}"
        }
        
        # Prepare messages for API call
        messages = [system_message, user_message]
        
        try:
            # Call OpenAI API
            response = await self.call_openai_api(messages)
            
            # Extract response content
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                return "Failed to create infrastructure plan. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error creating infrastructure plan: {str(e)}"
    
    async def create_deployment_pipeline(self, request: str, providers: List[str], provider_tools: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Create a deployment pipeline plan using available provider tools.
        
        Args:
            request: Original deployment request
            providers: List of identified providers
            provider_tools: Dictionary of available tools for each provider
            
        Returns:
            Deployment pipeline plan with tool recommendations
        """
        # Build summary of available tools
        tools_summary = ""
        for provider, tools in provider_tools.items():
            if tools:
                tools_summary += f"\n## {provider.upper()} Tools\n"
                for tool in tools:
                    # Format tool capabilities
                    capabilities = ", ".join([cap["name"] for cap in tool.get("capabilities", [])])
                    tools_summary += f"- **{tool['id']}**: {tool.get('description', 'No description')}. Capabilities: {capabilities}\n"
            else:
                tools_summary += f"\n## {provider.upper()} Tools\n- No {provider} tools found in the registry\n"
        
        # Prepare system message with instructions
        system_message = {
            "role": "system",
            "content": (
                "You are an expert DevOps engineer specializing in CI/CD pipelines. "
                "Your task is to create a comprehensive deployment pipeline "
                "based on the user's requirements and the available tools in the registry.\n\n"
                "For each pipeline, provide:\n"
                "1. Overview of the pipeline stages\n"
                "2. Detailed configuration for each stage\n"
                "3. Specific tools to use at each stage (from the available tools)\n"
                "4. Sample pipeline code or configuration\n"
                "5. Testing and validation strategies\n\n"
                "If critical tools are missing from the registry, suggest alternatives or "
                "recommend tools that should be installed.\n\n"
                "Here are the available tools in the registry:\n"
                f"{tools_summary}"
            )
        }
        
        # Prepare user message with request
        user_message = {
            "role": "user",
            "content": f"Please create a deployment pipeline for this request: {request}"
        }
        
        # Prepare messages for API call
        messages = [system_message, user_message]
        
        try:
            # Call OpenAI API
            response = await self.call_openai_api(messages)
            
            # Extract response content
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                return "Failed to create deployment pipeline. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error creating deployment pipeline: {str(e)}"
    
    async def configure_monitoring(self, request: str, providers: List[str], provider_tools: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Create a monitoring and observability setup using available provider tools.
        
        Args:
            request: Original monitoring request
            providers: List of identified providers
            provider_tools: Dictionary of available tools for each provider
            
        Returns:
            Monitoring configuration plan with tool recommendations
        """
        # Build summary of available tools
        tools_summary = ""
        for provider, tools in provider_tools.items():
            if tools:
                tools_summary += f"\n## {provider.upper()} Tools\n"
                for tool in tools:
                    # Format tool capabilities
                    capabilities = ", ".join([cap["name"] for cap in tool.get("capabilities", [])])
                    tools_summary += f"- **{tool['id']}**: {tool.get('description', 'No description')}. Capabilities: {capabilities}\n"
            else:
                tools_summary += f"\n## {provider.upper()} Tools\n- No {provider} tools found in the registry\n"
        
        # Prepare system message with instructions
        system_message = {
            "role": "system",
            "content": (
                "You are an expert DevOps engineer specializing in monitoring and observability. "
                "Your task is to create a comprehensive monitoring setup "
                "based on the user's requirements and the available tools in the registry.\n\n"
                "For each monitoring setup, provide:\n"
                "1. Overview of the monitoring strategy\n"
                "2. Key metrics and logs to collect\n"
                "3. Alerting and notification configuration\n"
                "4. Visualization and dashboard recommendations\n"
                "5. Specific tools to use for each aspect (from the available tools)\n"
                "6. Sample configurations or commands\n\n"
                "If critical tools are missing from the registry, suggest alternatives or "
                "recommend tools that should be installed.\n\n"
                "Here are the available tools in the registry:\n"
                f"{tools_summary}"
            )
        }
        
        # Prepare user message with request
        user_message = {
            "role": "user",
            "content": f"Please create a monitoring and observability setup for this request: {request}"
        }
        
        # Prepare messages for API call
        messages = [system_message, user_message]
        
        try:
            # Call OpenAI API
            response = await self.call_openai_api(messages)
            
            # Extract response content
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not response_content:
                return "Failed to create monitoring setup. Empty response from API."
            
            return response_content
            
        except Exception as e:
            return f"Error creating monitoring setup: {str(e)}"
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """Process a task from any source (Redis stream or A2A)"""
        try:
            # Extract input from the task envelope
            input_data = env.input or {}
            input_text = input_data.get("text", "")
            
            # Identify cloud providers from the request
            providers = await self.identify_providers(input_text)
            
            # Discover tools for each provider
            provider_tools = await self.discover_provider_tools(providers)
            
            # Add provider information to response
            providers_summary = "I've identified these cloud providers/tools from your request: " + ", ".join(providers) if providers else "I couldn't identify specific cloud providers in your request."
            
            # Check if this is an infrastructure provisioning request
            if any(x in input_text.lower() for x in ["provision", "infrastructure", "set up", "deploy infrastructure", "create resources"]):
                # Create infrastructure plan
                plan = await self.provision_infrastructure(
                    request=input_text,
                    providers=providers,
                    provider_tools=provider_tools
                )
                
                env.output = {"text": f"{providers_summary}\n\n{plan}"}
                env.status = "COMPLETED"
                
            # Check if this is a deployment pipeline request
            elif any(x in input_text.lower() for x in ["ci/cd", "pipeline", "continuous integration", "continuous deployment", "automated deployment"]):
                # Create deployment pipeline plan
                plan = await self.create_deployment_pipeline(
                    request=input_text,
                    providers=providers,
                    provider_tools=provider_tools
                )
                
                env.output = {"text": f"{providers_summary}\n\n{plan}"}
                env.status = "COMPLETED"
                
            # Check if this is a monitoring request
            elif any(x in input_text.lower() for x in ["monitor", "observability", "logging", "tracing", "alerts", "metrics"]):
                # Create monitoring setup
                plan = await self.configure_monitoring(
                    request=input_text,
                    providers=providers,
                    provider_tools=provider_tools
                )
                
                env.output = {"text": f"{providers_summary}\n\n{plan}"}
                env.status = "COMPLETED"
                
            else:
                # Default response for unknown queries
                tools_summary = ""
                for provider, tools in provider_tools.items():
                    if tools:
                        tools_summary += f"\n## {provider.upper()} Tools Found\n"
                        for tool in tools:
                            tools_summary += f"- {tool['id']}: {tool.get('description', 'No description')}\n"
                    else:
                        tools_summary += f"\n## {provider.upper()}\n- No {provider} tools found in the registry\n"
                
                env.output = {
                    "text": (
                        f"{providers_summary}\n\n"
                        "I'm a DevOps Discovery agent. I can help with:\n"
                        "- Provisioning cloud infrastructure\n"
                        "- Creating deployment pipelines\n"
                        "- Setting up monitoring and observability\n\n"
                        "Please specify what type of DevOps assistance you need.\n"
                        f"{tools_summary if tools_summary else ''}"
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
    # Create and run the DevOps discovery agent
    agent = DevOpsDiscoveryAgent()
    agent.run()