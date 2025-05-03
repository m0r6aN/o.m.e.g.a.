import os
import asyncio
import aiohttp
import gradio as gr
from typing import Dict, Any

class OmegaClient:
    """
    Client for interacting with the OMEGA framework.
    """
    
    def __init__(self, orchestrator_url=None):
        self.orchestrator_url = orchestrator_url or os.getenv("ORCHESTRATOR_URL", "http://localhost:9000")
        self.active_workflows = {}
    
    async def submit_request(self, request_text: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Submit a request to the OMEGA framework.
        
        Args:
            request_text: The natural language request to process
            options: Optional configuration for the workflow
            
        Returns:
            Dictionary containing the workflow ID and initial status
        """
        options = options or {
            "max_parallel_tasks": 5,
            "priority": "quality",
            "max_confidence_threshold": 0.7
        }
        
        payload = {
            "name": "execute_workflow",
            "parameters": {
                "workflow_request": {
                    "request": request_text,
                    "options": options
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.orchestrator_url}/tools/orchestrator",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    workflow_id = result.get("workflow_id")
                    self.active_workflows[workflow_id] = {
                        "status": "submitted",
                        "request": request_text
                    }
                    return result
                else:
                    error_text = await response.text()
                    return {"error": f"Request failed: {response.status}", "details": error_text}
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the current status of a workflow.
        
        Args:
            workflow_id: The ID of the workflow to check
            
        Returns:
            Dictionary containing the current workflow status
        """
        payload = {
            "name": "get_workflow_status",
            "parameters": {
                "workflow_id": workflow_id
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.orchestrator_url}/tools/orchestrator",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"Status check failed: {response.status}", "details": error_text}

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all registered tools from the registry.
        
        Returns:
            List of registered tools
        """
        registry_url = os.getenv("REGISTRY_URL", "http://registry:9401")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{registry_url}/registry/mcp/discover") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"Failed to get tools: {response.status}", "details": error_text}
    
    async def register_external_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register an external tool with the registry.
        
        Args:
            tool_data: Tool information including id, name, description, etc.
            
        Returns:
            Response from the registry
        """
        registry_url = os.getenv("REGISTRY_URL", "http://registry:9401")
    
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{registry_url}/registry/mcp/register/external",
                json=tool_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"Registration failed: {response.status}", "details": error_text}
    
    async def update_tool(self, tool_id: str, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing tool in the registry.
        
        Args:
            tool_id: ID of the tool to update
            tool_data: Updated tool information
            
        Returns:
            Response from the registry
        """
        registry_url = os.getenv("REGISTRY_URL", "http://registry:9401")

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{registry_url}/registry/mcp/update/{tool_id}",
                json=tool_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"Update failed: {response.status}", "details": error_text}
        

# Initialize the Gradio interface
def create_ui():
    client = OmegaClient()
    
    with gr.Blocks(title="OMEGA Framework") as app:
        gr.Markdown("""
        # 🧠 O.M.E.G.A. Framework
        ## Orchestrated Multi-Expert Gen Agents
        
        Submit your request and let our agent network handle it!
        """)
        
        with gr.Row():
            with gr.Column():
                request_input = gr.Textbox(
                    label="Your Request",
                    placeholder="Describe what you need...",
                    lines=4
                )
                options = gr.Json(
                    label="Options (Advanced)",
                    value={
                        "max_parallel_tasks": 5,
                        "priority": "quality",
                        "max_confidence_threshold": 0.7
                    }
                )
                submit_btn = gr.Button("Submit Request")
                
            with gr.Column():
                status_output = gr.Json(
                    label="Request Status",
                    value={}
                )
                refresh_btn = gr.Button("Refresh Status")
                workflow_id = gr.Textbox(
                    label="Workflow ID",
                    placeholder="Enter workflow ID to check status",
                    visible=True
                )
                
                with gr.Accordion("Workflow Results", open=False):
                    results_output = gr.Json(
                        label="Execution Results",
                        value={}
                    )

            with gr.Tab("Tool Management"):
                gr.Markdown("""
                # 🔧 Tool Management
                
                Register external MCP tools and manage existing tools.
                """)
    
            with gr.Row():
                with gr.Column():
                    # Form for registering new external tools
                    gr.Markdown("### Register External Tool")
                    
                    tool_id = gr.Textbox(label="Tool ID", placeholder="e.g., context7_docs")
                    tool_name = gr.Textbox(label="Tool Name", placeholder="e.g., Context7 Documentation Tool")
                    tool_description = gr.Textbox(
                        label="Description", 
                        placeholder="Describe what this tool does...",
                        lines=2
                    )
                    tool_host = gr.Textbox(label="Host", placeholder="e.g., context7-server")
                    tool_port = gr.Number(label="MCP Port", value=9000)
                    
                    # Tool capabilities
                    with gr.Accordion("Capabilities", open=False):
                        capabilities_json = gr.Json(
                            label="Tool Capabilities",
                            value=[
                                {
                                    "name": "get_documentation",
                                    "description": "Retrieves documentation for a specified library",
                                    "parameters": {
                                        "library_name": {"type": "string", "description": "Name of the library"}
                                    }
                                }
                            ]
                        )
                    
                    # Tool tags
                    tool_tags = gr.Textbox(
                        label="Tags (comma-separated)",
                        placeholder="e.g., documentation,dev,api"
                    )
                    
                    register_btn = gr.Button("Register Tool")
                
                with gr.Column():
                    # List of registered tools
                    gr.Markdown("### Registered Tools")
                    refresh_tools_btn = gr.Button("Refresh Tool List")
                    tools_list = gr.Json(label="Available Tools", value=[])
                    
                    # Tool details for updating
                    with gr.Accordion("Update Tool", open=False):
                        selected_tool_id = gr.Textbox(label="Selected Tool ID")
                        update_tool_json = gr.Json(label="Tool Configuration")
                        update_btn = gr.Button("Update Tool")
                return app

    # Event handlers
    async def register_tool_handler(id, name, description, host, port, capabilities, tags_str):
        try:
            # Parse tags
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
            
            # Create tool data
            tool_data = {
                "id": id,
                "name": name,
                "description": description,
                "host": host,
                "port": int(port),
                "capabilities": capabilities,
                "tags": tags,
                "version": "1.0.0"
            }
            
            # Register the tool
            result = await client.register_external_tool(tool_data)
            
            # Refresh tool list
            tools = await client.get_all_tools()
            
            return result, tools
        except Exception as e:
            return {"error": str(e)}, []
    
    async def refresh_tools_handler():
        try:
            tools = await client.get_all_tools()
            return tools
        except Exception as e:
            return {"error": str(e)}
    
    async def select_tool_handler(tools, evt: gr.SelectData):
        try:
            # Get the selected tool
            if isinstance(tools, list) and evt.index < len(tools):
                selected_tool = tools[evt.index]
                return selected_tool["id"], selected_tool
            return "", {}
        except Exception as e:
            return "", {"error": str(e)}
    
    async def update_tool_handler(tool_id, tool_data):
        try:
            result = await client.update_tool(tool_id, tool_data)
            
            # Refresh tool list
            tools = await client.get_all_tools()
            
            return result, tools
        except Exception as e:
            return {"error": str(e)}, []
    
    # Connect event handlers
    register_btn.click(
        lambda id, name, desc, host, port, caps, tags: asyncio.run(
            register_tool_handler(id, name, desc, host, port, caps, tags)
        ),
        inputs=[tool_id, tool_name, tool_description, tool_host, tool_port, capabilities_json, tool_tags],
        outputs=[gr.JSON(label="Registration Result"), tools_list]
    )
    
    refresh_tools_btn.click(
        lambda: asyncio.run(refresh_tools_handler()),
        inputs=[],
        outputs=[tools_list]
    )
    
    tools_list.select(
        lambda tools, evt: asyncio.run(select_tool_handler(tools, evt)),
        inputs=[tools_list],
        outputs=[selected_tool_id, update_tool_json]
    )
    
    update_btn.click(
        lambda id, data: asyncio.run(update_tool_handler(id, data)),
        inputs=[selected_tool_id, update_tool_json],
        outputs=[gr.JSON(label="Update Result"), tools_list]
    )
        
    # Event handlers
    async def submit_request_handler(request_text, options_json):
        try:
            result = await client.submit_request(request_text, options_json)
            workflow_id = result.get("workflow_id")
            return result, workflow_id
        except Exception as e:
            return {"error": str(e)}, ""
    
    async def refresh_status_handler(workflow_id):
        try:
            if not workflow_id:
                return {"error": "Please enter a workflow ID"}, {}
            
            result = await client.get_workflow_status(workflow_id)
            
            # Check if we have results to display
            if "results" in result:
                return result, result.get("results", {})
            else:
                return result, {}
        except Exception as e:
            return {"error": str(e)}, {}
    
    # Connect event handlers
    submit_btn.click(
        lambda x, y: asyncio.run(submit_request_handler(x, y)),
        inputs=[request_input, options],
        outputs=[status_output, workflow_id]
    )
    
    refresh_btn.click(
        lambda x: asyncio.run(refresh_status_handler(x)),
        inputs=[workflow_id],
        outputs=[status_output, results_output]
    )
if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7860)
