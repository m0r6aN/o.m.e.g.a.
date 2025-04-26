from backend_v2.core.tools.tool_base import Tool
import textwrap

class SummarizeTextTool(Tool):
    name = "summarize_text"
    description = "Summarizes input text into a concise explanation."

    def run(self, input_data: str) -> str:
        # In reality, you'd use a real model/tool here.
        # For now, return the first few lines with a fake 'summary'
        summary = textwrap.shorten(input_data, width=300, placeholder="...")
        return f"Summary: {summary}"
