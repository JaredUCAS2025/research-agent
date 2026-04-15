from __future__ import annotations

from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = ROOT_DIR / "workspace"
INPUTS_DIR = WORKSPACE_DIR / "inputs"
OUTPUTS_DIR = WORKSPACE_DIR / "outputs"
RUNS_DIR = WORKSPACE_DIR / "runs"
SESSIONS_DIR = WORKSPACE_DIR / "sessions"
UPLOADS_DIR = WORKSPACE_DIR / "uploads"


class Settings(BaseModel):
    openai_api_key: str = ""
    openai_base_url: str | None = None
    openai_model: str = "gpt-5.4-mini"
    # Optional fast model for lightweight tasks (chat, translation, etc.)
    openai_fast_model: str | None = None



def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        openai_fast_model=os.getenv("OPENAI_FAST_MODEL") or None,
    )


for directory in (WORKSPACE_DIR, INPUTS_DIR, OUTPUTS_DIR, RUNS_DIR, SESSIONS_DIR, UPLOADS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
