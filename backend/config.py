"""Application configuration loaded from the project-level YAML file."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "app.yaml"

# Only HTTP origins on the frontend development port and RFC1918 IPv4 ranges.
# Anchors prevent a private-looking substring in a public hostname from matching.
PRIVATE_LAN_ORIGIN_REGEX = (
    r"^http://(?:"
    r"10(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}|"
    r"172\.(?:1[6-9]|2\d|3[01])(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){2}|"
    r"192\.168(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){2}"
    r"):3000$"
)


class CorsSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_origins: list[str] = Field(default_factory=list)
    allow_local_network_origins: bool = False


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    environment: str = "production"
    cors: CorsSettings = Field(default_factory=CorsSettings)
    model_adapter: str = "mock"
    backend_port: int = 8000
    frontend_port: int = 3000

    @property
    def cors_origin_regex(self) -> str | None:
        return PRIVATE_LAN_ORIGIN_REGEX if self.environment == "development" and self.cors.allow_local_network_origins else None


def load_settings(path: Path | None = None) -> AppSettings:
    """Load settings, optionally using APP_CONFIG_PATH for deployments."""
    configured_path = path or Path(os.environ.get("APP_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    payload = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    return AppSettings.model_validate(payload)
