from config import SYSTEM_PROMPT
import os
import re
import html

# ==================== НАСТРОЙКИ ====================

DEFAULT_MODEL = "gemini-pro"
_model = None


# ==================== MODEL INIT ====================

def _get_model():
    """
    Лениво создаёт модель Gemini.
    """
    global _model

    if _model is not None:
        return _model

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY не найден в .env файле")

    import google.generativeai as genai

    genai.configure(api_key=api_key)

    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    _model = genai.GenerativeModel(
        model_name,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 1024,
        }
    )

    return _model


# ==================== MARKDOWN → HTML ====================

def md_to_html(md: str) -> str:
    md = html.escape(md)

    def block_code(match):
        return f"<pre><code>{match.group(2)}</code></pre>"

    md = re.sub(r"```([a-zA-Z0-9_-]+)?\n([\s\S]*?)```", block_code, md)
    md = re.sub(r"`([^`]+)`", r"<code>\1</code>", md)
    md = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", md)
    md = re.sub(r"\*(.*?)\*", r"<i>\1</i>", md)
    md = re.sub(r"^#+\s*(.*)$", r"<b>\1</b>", md, flags=re.MULTILINE)

    return md


# ==================== MAIN FUNCTION ====================

def get_ai_response(message: str):
    try:
        model = _get_model()  # 🔑 КЛЮЧЕВАЯ СТРОКА

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Пользователь:\n{message}"
        )

        response = model.generate_content(prompt)
        text = response.text or ""

        return md_to_html(text), 0, 0

    except Exception as e:
        print("❌ ОШИБКА AI:", e)
        return f"Ошибка при обращении к AI: {e}", 0, 0
