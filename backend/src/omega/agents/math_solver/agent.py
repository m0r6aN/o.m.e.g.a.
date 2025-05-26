from omega.agents.registerable_dual_mode_agent import RegisterableDualModeAgent
from omega.core.models.task_models import TaskEnvelope

class MathSolverAgent(RegisterableDualModeAgent):
    """
    An example agent that discovers and uses MCP tools from the registry
    to solve math problems.
    
    This version uses the base class methods for tool discovery and calling.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="math_solver",
            tool_name="math_solver",
            description="An agent that solves math problems using available tools",
            version="1.0.0",
            skills=["solve_math_problem"],
            agent_type="agent",
            tags=["math", "solver"]
        )
    
    def _register_a2a_capabilities(self):
        """Register A2A skills"""
        # No need to implement custom capabilities for this example
        pass
    
    async def parse_and_solve_math(self, text: str):
        """
        Parse a math problem and solve it using available tools
        """
        # Discover available math tools using the base class method
        tools = await self.discover_mcp_tools_by_tag("math")
        
        if not tools:
            return "I couldn't find any math tools to help solve this problem."
        
        # Look for the calculator tool
        calculator = next((tool for tool in tools if tool["id"] == "calculator"), None)
        
        if not calculator:
            return "I couldn't find a calculator tool to solve this problem."
        
        # Simple parsing for demonstration purposes
        text = text.lower()
        
        try:
            if "add" in text or "plus" in text or "sum" in text or "+" in text:
                # Extract numbers - this is very basic for demonstration
                nums = [float(s) for s in text.replace(",", "").split() if s.replace(".", "").isdigit()]
                if len(nums) >= 2:
                    # Use the base class method to call the tool
                    result = await self.call_mcp_tool(
                        calculator["mcp_endpoint"],
                        "add",
                        a=nums[0],
                        b=nums[1]
                    )
                    return result.get("response", "Calculation failed")
            
            elif "subtract" in text or "minus" in text or "-" in text:
                nums = [float(s) for s in text.replace(",", "").split() if s.replace(".", "").isdigit()]
                if len(nums) >= 2:
                    # Use the base class method to call the tool
                    result = await self.call_mcp_tool(
                        calculator["mcp_endpoint"],
                        "subtract",
                        a=nums[0],
                        b=nums[1]
                    )
                    return result.get("response", "Calculation failed")
            
            elif "multiply" in text or "times" in text or "*" in text or "×" in text:
                nums = [float(s) for s in text.replace(",", "").split() if s.replace(".", "").isdigit()]
                if len(nums) >= 2:
                    # Use the base class method to call the tool
                    result = await self.call_mcp_tool(
                        calculator["mcp_endpoint"],
                        "multiply",
                        a=nums[0],
                        b=nums[1]
                    )
                    return result.get("response", "Calculation failed")
            
            elif "divide" in text or "/" in text or "÷" in text:
                nums = [float(s) for s in text.replace(",", "").split() if s.replace(".", "").isdigit()]
                if len(nums) >= 2:
                    # Use the base class method to call the tool
                    result = await self.call_mcp_tool(
                        calculator["mcp_endpoint"],
                        "divide",
                        a=nums[0],
                        b=nums[1]
                    )
                    return result.get("response", "Calculation failed")
            
            # Alternative method using the high-level helper method
            # This would automatically find and call a tool with the right capability
            elif "square root" in text:
                nums = [float(s) for s in text.replace(",", "").split() if s.replace(".", "").isdigit()]
                if len(nums) >= 1:
                    result = await self.find_tool_by_capability_and_call("sqrt", number=nums[0])
                    return result.get("response", "Calculation failed")
            
            return "I couldn't understand the math operation. Please specify add, subtract, multiply, or divide with two numbers."
            
        except Exception as e:
            print(f"❌ Error solving math problem: {str(e)}")
            return f"Error solving the math problem: {str(e)}"
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """Process a task from any source (Redis stream or A2A)"""
        try:
            # Extract input from the task envelope
            input_text = env.input.get("text", "") if env.input else ""
            
            if "solve" in input_text.lower() and any(op in input_text.lower() for op in ["add", "plus", "sum", "subtract", "minus", "multiply", "times", "divide", "+"]):
                # This looks like a math problem, try to solve it
                response = await self.parse_and_solve_math(input_text)
                env.output = {"text": response}
                env.status = "COMPLETED"
            else:
                # Default response for unknown queries
                env.output = {
                    "text": (
                        "I'm a math solver agent. I can help you solve math problems using available tools.\n"
                        "For example, you can ask me to solve addition, subtraction, multiplication, or division problems."
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
    # Create and run the math solver agent
    agent = MathSolverAgent()
    agent.run()