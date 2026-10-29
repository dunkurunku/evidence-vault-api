from anthropic import Anthropic

from app.config import get_settings

MODEL = "claude-sonnet-5-5"


def summarize(text: str, max_chars: int = 20000) -> str:
    key = get_settings().anthropic_api_key
    if not key:
        raise RuntimeError("Falta ANTHROPIC_API_KEY en el entorno")
    client = Anthropic(api_key=key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": (
                    "Resume en español, en un párrafo de cinco líneas como máximo, el siguiente "
                    "documento. No inventes nada que no esté en el texto.\n\n" + text[:max_chars]
                ),
            }
        ],
    )
    return "".join(block.text for block in message.content if block.type == "text")
