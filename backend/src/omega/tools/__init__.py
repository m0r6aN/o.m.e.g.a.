# tool registry utlization
from ..core.models.tool import tool_registry

# tools
from .translate_text_tool.translate import TranslateTool
from .summarize_text_tool.summarize_text import SummarizeTextTool
from .web_search_tool.web_search import WebSearchTool
from .nlp_to_sql_tool.nlp_to_sql import nlp_to_sql_tool
from .execute_sql_tool.execute_sql import execute_sql_tool

# Register tools with their capabilities
tool_registry.register(TranslateTool(), capabilities=["translation"])
tool_registry.register(SummarizeTextTool(), capabilities=["text_summarization"])
tool_registry.register(WebSearchTool(), capabilities=["web_search"])
tool_registry.register(nlp_to_sql_tool(), capabilities=["nlp_to_sql"])
tool_registry.register(execute_sql_tool(), capabilities=["execute_sql"])
