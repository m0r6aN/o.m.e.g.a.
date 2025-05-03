```python
# Create a calculator tool with the builder pattern
calc_tool = (MCPToolBuilder("calculator", "Calculator Tool")
    .with_description("A tool for performing calculations")
    .with_tags("math", "calculator")
    .add_function("add", add_func, "Add two numbers", params)
    .add_function("subtract", subtract_func, "Subtract numbers", params)
    .build())

# Run the tool
calc_tool.run()
```