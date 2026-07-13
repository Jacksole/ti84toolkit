"""
Config file support -- reads ~/.config/ti84toolkit/config.toml.

Deliberately hand-rolled instead of pulling in a toml library: the toolkit
only needs a handful of flat key = value settings, so a minimal parser avoids
an extra dependency (relevant since this runs across Ubuntu/ParrotOS/AlmaLinux
WSL distros with varying default Python versions).

Supported file (all keys optional, shown with their defaults):

    [physics]
    gravity = 9.81

    [display]
    precision = 6
"""
from __future__ import annotations

import os
from pathlib import Path

_DEFAULTS = {
    "physics": {"gravity": 9.81},
    "display": {"precision": 6},
}


def _config_path() -> Path:
    override = os.environ.get("TI84TOOLKIT_CONFIG_PATH")
    if override:
        return Path(override)
    return Path.home() / ".config" / "ti84toolkit" / "config.toml"


def _coerce(raw: str):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def load_config() -> dict:
    """Load config, merged over defaults. Missing file or parse errors fall back to defaults silently."""
    config = {section: dict(values) for section, values in _DEFAULTS.items()}

    path = _config_path()
    if not path.exists():
        return config

    section = None
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip()
                config.setdefault(section, {})
                continue
            if "=" in line and section is not None:
                key, _, value = line.partition("=")
                config[section][key.strip()] = _coerce(value)
    except OSError:
        return {section: dict(values) for section, values in _DEFAULTS.items()}

    return config


def get_gravity() -> float:
    return float(load_config().get("physics", {}).get("gravity", 9.81))


def get_precision() -> int:
    return int(load_config().get("display", {}).get("precision", 6))
