from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

import httpx

from nim_chatbot.config import Settings
from nim_chatbot.errors import ApiError

_INVALID_RESPONSE_MESSAGE = "Respons API tidak valid"
_TIMEOUT = 60.0


class NimClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.BaseTransport | None = None,
        sleep: Any = time.sleep,
        max_retries: int = 3,
        timeout: float = _TIMEOUT,
    ) -> None:
        self._settings = settings
        self._sleep = sleep
        self._max_retries = max_retries
        self._client = httpx.Client(transport=transport, timeout=timeout)

    def chat(self, messages: list[dict]) -> str:
        payload = {
            "model": self._settings.model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1024,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }
        response = self._client.post(
            f"{self._settings.base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        if not response.is_success:
            raise ApiError(
                f"API NVIDIA mengembalikan status {response.status_code}",
                status_code=response.status_code,
            )
        return self._extract_content(response)

    def stream(self, messages: list[dict]) -> Iterator[str]:
        payload = {
            "model": self._settings.model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1024,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }
        with self._client.stream(
            "POST",
            f"{self._settings.base_url}/chat/completions",
            json=payload,
            headers=headers,
        ) as response:
            if not response.is_success:
                raise ApiError(
                    f"API NVIDIA mengembalikan status {response.status_code}",
                    status_code=response.status_code,
                )
            for line in response.iter_lines():
                data = line.strip()
                if not data.startswith("data:"):
                    continue
                data = data[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    body = json.loads(data)
                except ValueError:
                    raise ApiError(_INVALID_RESPONSE_MESSAGE) from None
                if not isinstance(body, dict):
                    raise ApiError(_INVALID_RESPONSE_MESSAGE)
                choices = body.get("choices")
                if not isinstance(choices, list):
                    raise ApiError(_INVALID_RESPONSE_MESSAGE)
                if not choices:
                    continue
                first = choices[0]
                delta = first.get("delta") if isinstance(first, dict) else None
                content = delta.get("content") if isinstance(delta, dict) else None
                if not isinstance(content, str) or not content:
                    continue
                yield content

    def close(self) -> None:
        self._client.close()

    def _extract_content(self, response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            raise ApiError(_INVALID_RESPONSE_MESSAGE) from None
        if not isinstance(body, dict):
            raise ApiError(_INVALID_RESPONSE_MESSAGE)
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ApiError(_INVALID_RESPONSE_MESSAGE)
        first = choices[0]
        if not isinstance(first, dict):
            raise ApiError(_INVALID_RESPONSE_MESSAGE)
        message = first.get("message")
        if not isinstance(message, dict):
            raise ApiError(_INVALID_RESPONSE_MESSAGE)
        content = message.get("content")
        if not isinstance(content, str):
            raise ApiError(_INVALID_RESPONSE_MESSAGE)
        return content
