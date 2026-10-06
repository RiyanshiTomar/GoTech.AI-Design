"""python -m archagent.server"""
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")   # API keys for litellm (OPENAI_API_KEY, HF_TOKEN, ...)

from .app import create_app
from .config import get_settings

if __name__ == "__main__":
    s = get_settings()
    print(f"Architecture Agent -> http://{s.host}:{s.port}   model={s.model}   workspace={s.workspace}")
    uvicorn.run(create_app(s), host=s.host, port=s.port, log_level="info")
