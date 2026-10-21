from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

import httpx

from nim_chatbot.config import Settings
from nim_chatbot.errors import ApiError

_INVALID_RESPONSE_MESSAGE = "Respons API tidak valid"
_CONNECTION_ERROR_MESSAGE = "Gagal terhubung ke API NVIDIA"
_TIMEOUT = 60.0

_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


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
        payload = self._build_payload(messages, stream=False)
        response = self._send(payload, stream=False)
        try:
            return self._extract_content(response)
        finally:
            response.close()

    def stream(self, messages: list[dict]) -> Iterator[str]:
        payload = self._build_payload(messages, stream=True)
        response = self._send(payload, stream=True)
        try:
            yield from self._iter_content(response)
        finally:
            response.close()

    def close(self) -> None:
        self._client.close()

    def _build_payload(self, messages: list[dict], stream: bool) -> dict:
        return {
            "model": self._settings.model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1024,
            "stream": stream,
        }

    def _send(self, payload: dict, stream: bool) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._settings.base_url}/chat/completions"
        total_attempts = self._max_retries + 1
        for attempt in range(total_attempts):
            last_attempt = attempt == total_attempts - 1
            try:
                request = self._client.build_request(
                    "POST", url, json=payload, headers=headers
                )
                response = self._client.send(request, stream=stream)
            except httpx.TransportError:
                if last_attempt:
                    raise ApiError(_CONNECTION_ERROR_MESSAGE) from None
                self._sleep(1.0 * 2**attempt)
                continue

            if response.status_code in _RETRY_STATUSES:
                status_code = response.status_code
                response.close()
                if last_attempt:
                    raise ApiError(
                        f"API NVIDIA mengembalikan status {status_code}",
                        status_code=status_code,
                    )
                self._sleep(1.0 * 2**attempt)
                continue

            if not response.is_success:
                status_code = response.status_code
                response.close()
                raise ApiError(
                    f"API NVIDIA mengembalikan status {status_code}",
                    status_code=status_code,
                )

            return response

        raise AssertionError("unreachable")

    def _iter_content(self, response: httpx.Response) -> Iterator[str]:
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
