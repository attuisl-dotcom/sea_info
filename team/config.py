"""Deployment profile loader. Non-secret values live in config/*.toml;
credentials are read only from environment variables or the deployment secret store.
"""
from __future__ import annotations

import os
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
except ImportError:
    pass


def _merge(target: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge(target[key], value)
        else:
            target[key] = value
    return target


def load_settings() -> dict[str, Any]:
    profile = os.getenv("SEA_INFO_ENV", "development").lower()
    if profile not in {"development", "production"}:
        raise ValueError("SEA_INFO_ENV must be development or production")
    with (ROOT / "config" / "settings.toml").open("rb") as f:
        settings = tomllib.load(f)
    with (ROOT / "config" / f"{profile}.toml").open("rb") as f:
        _merge(settings, tomllib.load(f))
    settings = deepcopy(settings)
    settings["app"]["environment"] = profile
    settings["ai"]["api_key"] = os.getenv("GEMINI_API_KEY", "")
    settings["ai"]["model"] = os.getenv("GEMINI_MODEL", settings["ai"]["model"])
    settings["ai"]["daily_limit_member"] = int(os.getenv("AI_DAILY_LIMIT_PER_MEMBER", settings["ai"]["daily_limit_member"]))
    settings["ai"]["daily_limit_guest"] = int(os.getenv("AI_DAILY_LIMIT_PER_GUEST", settings["ai"]["daily_limit_guest"]))
    settings["storage"]["sqlite_path"] = os.getenv("SQLITE_PATH", settings["storage"]["sqlite_path"])
    settings["integrations"]["jira_url"] = os.getenv("JIRA_BASE_URL", "")
    settings["integrations"]["jira_project_key"] = os.getenv("JIRA_PROJECT_KEY", "")
    settings["integrations"]["jira_user"] = os.getenv("JIRA_USER", "")
    settings["integrations"]["jira_api_token"] = os.getenv("JIRA_API_TOKEN", "")
    settings["integrations"]["redis_url"] = os.getenv("REDIS_URL", "")
    settings["integrations"]["supabase_url"] = os.getenv("SUPABASE_URL", "")
    settings["integrations"]["supabase_anon_key"] = os.getenv("SUPABASE_ANON_KEY", "")
    settings["integrations"]["marine_api_key"] = os.getenv("KHOA_API_KEY", "")
    return settings
