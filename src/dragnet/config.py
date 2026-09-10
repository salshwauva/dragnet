"""Config loader. Reads `config.yaml` + `.env`, returns a typed Config object."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


class LocationWeights(BaseModel):
    remote: float = 100
    hybrid: float = 80
    boston: float = 70
    dc: float = 50
    nyc: float = 40
    philly: float = 35
    chicago: float = 30
    other_us: float = 10
    international: float = 0


class ScoreConfig(BaseModel):
    location: LocationWeights = Field(default_factory=LocationWeights)
    recency_decay: float = 2.0
    category_match: float = 25
    citizenship_bonus: float = 20
    clearance_bonus: float = 30


class FilterConfig(BaseModel):
    intern_required: bool = True
    earliest_start: date | None = None
    drop_summer_2026: bool = True
    drop_spring_only: bool = False


class NotifyConfig(BaseModel):
    obsidian_brief_dir: str = "Tech/job-search/dragnet-briefs"
    email_enabled: bool = True
    email_to: str = ""
    email_from: str = ""
    email_min_score: float = 50
    email_max_postings: int = 25


class AdaptersConfig(BaseModel):
    concurrent_limit: int = 5
    per_adapter_timeout_sec: int = 30
    adzuna_pages: int = 2
    jsearch_pages: int = 1
    themuse_pages: int = 3
    usajobs_page_size: int = 250


class LifecycleConfig(BaseModel):
    # A posting missing from this many consecutive successful crawls of its
    # source is marked inactive. One miss is noise (rate limits, paging).
    inactive_after_misses: int = 3


class PathsConfig(BaseModel):
    db_path: str = "./dragnet.db"
    log_path: str = "./dragnet.log"


class Secrets(BaseModel):
    """Secrets loaded from .env. Empty strings mean "not configured"."""

    model_config = ConfigDict(frozen=True)

    usajobs_auth_key: str = ""
    usajobs_user_agent_email: str = ""
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    rapidapi_key: str = ""
    gmail_address: str = ""
    gmail_app_password: str = ""


class Config(BaseModel):
    sources: dict[str, bool] = Field(default_factory=dict)
    categories: dict[str, list[str]] = Field(default_factory=dict)
    category_weights: dict[str, float] = Field(default_factory=dict)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    score: ScoreConfig = Field(default_factory=ScoreConfig)
    notify: NotifyConfig = Field(default_factory=NotifyConfig)
    adapters: AdaptersConfig = Field(default_factory=AdaptersConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    lifecycle: LifecycleConfig = Field(default_factory=LifecycleConfig)

    # filled in post-load
    secrets: Secrets = Field(default_factory=Secrets)
    repo_root: Path = Field(default_factory=Path.cwd)
    vault_root: Path | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {path}. Copy config.yaml.example to config.yaml and edit."
        )
    with path.open() as f:
        return yaml.safe_load(f)


def _load_secrets() -> Secrets:
    return Secrets(
        usajobs_auth_key=os.getenv("USAJOBS_AUTH_KEY", ""),
        usajobs_user_agent_email=os.getenv("USAJOBS_USER_AGENT_EMAIL", ""),
        adzuna_app_id=os.getenv("ADZUNA_APP_ID", ""),
        adzuna_app_key=os.getenv("ADZUNA_APP_KEY", ""),
        rapidapi_key=os.getenv("RAPIDAPI_KEY", ""),
        gmail_address=os.getenv("GMAIL_ADDRESS", ""),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
    )


def _detect_vault_root() -> Path | None:
    """Best-effort detection of Sophia's Obsidian vault root. Returns None if not found."""
    candidates = [
        Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/my-vault",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def load_config(repo_root: Path | None = None) -> Config:
    """Load config.yaml and .env from `repo_root` (defaults to CWD). Validate and return."""
    root = repo_root or Path.cwd()
    load_dotenv(root / ".env")
    raw = _load_yaml(root / "config.yaml")
    cfg = Config(**raw)
    cfg.secrets = _load_secrets()
    cfg.repo_root = root
    cfg.vault_root = _detect_vault_root()
    return cfg
