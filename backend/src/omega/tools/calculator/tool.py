import os
from omega.core.registerable_mcp_tool import RegisterableMCPTool
from fastmcp import text_response

def main():
    # Create a calculator tool that will register with the central registry
    calc_tool = RegisterableMCPTool(
        tool_id="calculator",
        name="Calculator Tool",
        description="A simple calculator tool that can perform basic arithmetic operations",
        version="1.0.0",
        tags=["math", "calculator", "arithmetic"]
    )
    
    # Add calculator functions    
    @text_response
    def add(a: float, b: float) -> str:
        """Add two numbers together"""
        result = a + b
        return f"The sum of {a} and {b} is {result}"
    
    calc_tool.add_tool(
        name="add",
        description="Add two numbers together",
        func=add,
        parameters={
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        }
    )
    
    @text_response
    def subtract(a: float, b: float) -> str:
        """Subtract b from a"""
        result = a - b
        return f"The result of {a} minus {b} is {result}"
    
    calc_tool.add_tool(
        name="subtract",
        description="Subtract the second number from the first",
        func=subtract,
        parameters={
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Number to subtract"}
        }
    )
    
    @text_response
    def multiply(a: float, b: float) -> str:
        """Multiply two numbers"""
        result = a * b
        return f"The product of {a} and {b} is {result}"
    
    calc_tool.add_tool(
        name="multiply",
        description="Multiply two numbers together",
        func=multiply,
        parameters={
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        }
    )
    
    @text_response
    def divide(a: float, b: float) -> str:
        """Divide a by b"""
        if b == 0:
            return "Error: Cannot divide by zero"
        result = a / b
        return f"The result of {a} divided by {b} is {result}"
    
    calc_tool.add_tool(
        name="divide",
        description="Divide the first number by the second",
        func=divide,
        parameters={
            "a": {"type": "number", "description": "Numerator"},
            "b": {"type": "number", "description": "Denominator"}
        }
    )
    
    # Run the tool server
    print(f"🧮 Starting Calculator Tool on port {os.getenv('PORT', '8000')}")
    calc_tool.run()


if __name__ == "__main__":
    main()