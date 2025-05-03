# tools/summarize_text/tool.py
import textwrap
from omega.core.registerable_mcp_tool import RegisterableMCPTool

def summarize_text(text: str, max_length: int = 300) -> str:
    """
    Summarize input text into a concise explanation.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary (default: 300)
        
    Returns:
        Summarized text
    """
    # In a real implementation, we would use an LLM or specialized summarization model
    # For demo purposes, just truncate the text
    summary = textwrap.shorten(text, width=max_length, placeholder="...")
    return f"Summary: {summary}"

# Create the tool
tool = RegisterableMCPTool(
    tool_id="summarize_text",
    name="Text Summarizer",
    description="Summarizes long text into concise explanations",
    version="1.0.0",
    tags=["text", "summarization", "nlp"]
)

# Add the summarization function
tool.add_tool(
    name="summarize",
    description="Summarize text to a shorter length",
    func=summarize_text,
    parameters={
        "text": {
            "type": "string", 
            "description": "Text to summarize"
        },
        "max_length": {
            "type": "integer", 
            "description": "Maximum length of summary",
            "required": False,
            "default": 300
        }
    }
)

# Run the tool server
if __name__ == "__main__":
    tool.run()