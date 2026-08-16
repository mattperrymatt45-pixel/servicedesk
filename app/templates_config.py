from fastapi.templating import Jinja2Templates
from app.config import settings


def get_current_ai_model() -> str:
    """Format configured AI model name dynamically for user-friendly display in UI."""
    model_raw = getattr(settings, 'AI_MODEL', None) or getattr(settings, 'GROQ_MODEL', None) or ""
    if not model_raw or not model_raw.strip():
        return "Model: Default"
    
    clean = model_raw.strip().lower()
    if "gpt-oss-120b" in clean:
        return "GPT OSS 120B"
    elif "qwen3.6-27b" in clean or "qwen" in clean:
        return "Qwen 3.6 27B"
    elif "llama-3.1" in clean:
        return "Llama 3.1 8B"
    elif "llama-3.3" in clean:
        return "Llama 3.3 70B"
    
    parts = model_raw.split("/")
    name = parts[-1] if len(parts) > 1 else model_raw
    return name.replace("-", " ").replace("_", " ").title()


# Shared Jinja2Templates instance with global helper functions
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["get_current_ai_model"] = get_current_ai_model
