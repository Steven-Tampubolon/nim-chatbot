from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from nim_chatbot.errors import ConfigError

DEFAULT_SYSTEM_PROMPT = (
    "Kamu adalah asisten yang ramah dan ringkas. "
    "Jawab dalam bahasa yang dipakai pengguna."
)
DEFAULT_MODEL = "z-ai/glm-5.3"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"

_API_KEY_VAR = "NVIDIA_API_KEY"
_MAX_HISTORY_VAR = "CHATBOT_MAX_HISTORY_CHARS"
_MISSING_KEY_MESSAGE = "NVIDIA_API_KEY belum diatur"
_INVALID_MAX_HISTORY_MESSAGE = "CHATBOT_MAX_HISTORY_CHARS harus bilangan bulat positif"


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    model: str
    base_url: str
    system_prompt: str
    max_history_chars: int


def _read(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    value = value.strip()
    return value


def load_settings(env: Mapping[str, str]) -> Settings:
    api_key = _read(env, _API_KEY_VAR)
    if not api_key:
        raise ConfigError(_MISSING_KEY_MESSAGE)

    model = _read(env, "NVIDIA_MODEL") or DEFAULT_MODEL
    base_url = _read(env, "NVIDIA_BASE_URL") or DEFAULT_BASE_URL
    base_url = base_url.rstrip("/")
    system_prompt = _read(env, "CHATBOT_SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT

    raw_max_history = _read(env, _MAX_HISTORY_VAR)
    if raw_max_history:
        try:
            max_history_chars = int(raw_max_history)
        except ValueError:
            raise ConfigError(_INVALID_MAX_HISTORY_MESSAGE) from None
        if max_history_chars <= 0:
            raise ConfigError(_INVALID_MAX_HISTORY_MESSAGE)
    else:
        max_history_chars = 12000

    return Settings(
        api_key=api_key,
        model=model,
        base_url=base_url,
        system_prompt=system_prompt,
        max_history_chars=max_history_chars,
    )
