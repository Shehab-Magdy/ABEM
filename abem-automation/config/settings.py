"""
Framework-wide configuration loader.

Priority (highest → lowest):
  1. Environment variables (e.g. ABEM_ENVIRONMENT=staging)
  2. environments.yaml values
  3. Hard-coded defaults

Usage:
    from config.settings import get_config
    cfg = get_config()       # reads ABEM_ENVIRONMENT env-var (default: dev)
    cfg = get_config("staging")
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

_ENV_FILE = Path(__file__).parent / "environments.yaml"


# ── Sub-configs ───────────────────────────────────────────────────────────────

@dataclass
class MobileConfig:
    platform_name: str = "Android"
    device_name: str = "emulator-5554"
    platform_version: str = "13.0"
    app_package: str = "com.abem.mobile"
    app_activity: str = ".MainActivity"
    automation_name: str = "UiAutomator2"
    appium_url: str = "http://localhost:4723"
    no_reset: bool = True


@dataclass
class Config:
    environment: str = "dev"
    base_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000/api/v1"
    admin_email: str = "admin@abem.local"
    admin_password: str = "Admin@1234"
    owner_email: str = "owner@abem.local"
    owner_password: str = "Owner@1234"
    browser: str = "chrome"
    headless: bool = True
    implicit_wait: int = 10
    explicit_wait: int = 15
    mobile: MobileConfig = field(default_factory=MobileConfig)

    @property
    def health_url(self) -> str:
        return f"{self.api_url.rstrip('/api/v1')}/health/"

    @property
    def docs_url(self) -> str:
        return f"{self.api_url}/docs/"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _expand_env_vars(value: str) -> str:
    """Replace ${VAR_NAME} patterns with the matching OS environment variable."""
    if not isinstance(value, str):
        return value
    return re.sub(
        r"\$\{(\w+)\}",
        lambda m: os.environ.get(m.group(1), m.group(0)),
        value,
    )


def _expand_dict(d: dict) -> dict:
    """Recursively expand env-var placeholders in a dict."""
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _expand_dict(v)
        elif isinstance(v, str):
            result[k] = _expand_env_vars(v)
        else:
            result[k] = v
    return result


def _load_yaml(env_name: str) -> dict:
    with open(_ENV_FILE) as f:
        raw = yaml.safe_load(f)
    envs = raw.get("environments", {})
    if env_name not in envs:
        raise ValueError(
            f"Unknown environment '{env_name}'. "
            f"Valid options: {list(envs.keys())}"
        )
    return _expand_dict(envs[env_name])


# ── Public API ─────────────────────────────────────────────────────────────────

def get_config(environment: Optional[str] = None) -> Config:
    """Return a fully-resolved Config for the requested environment."""
    env_name = environment or os.environ.get("ABEM_ENVIRONMENT", "dev")
    data = _load_yaml(env_name)

    mobile_data = data.pop("mobile", {})
    mobile_cfg = MobileConfig(**{k: mobile_data[k] for k in mobile_data if hasattr(MobileConfig, k)})

    return Config(
        environment=env_name,
        mobile=mobile_cfg,
        **{k: data[k] for k in data if hasattr(Config, k)},
    )
