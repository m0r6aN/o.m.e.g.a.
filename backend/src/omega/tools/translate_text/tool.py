# tools/translate_text/tool.py
from googletrans import Translator
from omega.core.registerable_mcp_tool import RegisterableMCPTool

# Initialize the translator
translator = Translator()

async def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """
    Translate text from one language to another.
    
    Args:
        text: The text to translate
        target_lang: Target language code (e.g., 'fr', 'es', 'de')
        source_lang: Source language code (default: auto-detect)
        
    Returns:
        Translated text
    """
    try:
        # googletrans v4.x is actually *async*—so we just await it directly
        trans = await translator.translate(text, dest=target_lang, src=source_lang)
        return trans.text
    except Exception as e:
        return f"Translation error: {str(e)}"

# Create the tool
tool = RegisterableMCPTool(
    tool_id="translate_text",
    name="Text Translator",
    description="Translates text between languages",
    version="1.0.0",
    tags=["translation", "language", "nlp"]
)

# Add the translation function
tool.add_tool(
    name="translate",
    description="Translate text between languages",
    func=translate_text,
    parameters={
        "text": {
            "type": "string", 
            "description": "Text to translate"
        },
        "target_lang": {
            "type": "string", 
            "description": "Target language code (e.g., 'fr', 'es', 'de')"
        },
        "source_lang": {
            "type": "string", 
            "description": "Source language code (default: auto-detect)",
            "required": False,
            "default": "auto"
        }
    }
)

# Run the tool server
if __name__ == "__main__":
    tool.run()