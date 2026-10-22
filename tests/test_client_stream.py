import json

import httpx
import pytest

from nim_chatbot.client import NimClient
from nim_chatbot.config import load_settings
from nim_chatbot.errors import ApiError

STREAM_BODY = (
    'data: {"choices":[{"delta":{"role":"assistant"}}]}\n'
    "\n"
    'data: {"choices":[{"delta":{"content":"Halo"}}]}\n'
    "\n"
    ": keep-alive\n"
    "\n"
    'data: {"choices":[{"delta":{"content":" dunia"}}]}\n'
    "\n"
    'data: {"choices":[{"delta":{"content":null}}]}\n'
    "\n"
    'data: {"choices":[]}\n'
    "\n"
    "data: [DONE]\n"
    "\n"
)

EXPECTED_BODY = {
    "model": "z-ai/glm-5.3",
    "messages": [{"role": "user", "content": "hai"}],
    "temperature": 0.6,
    "max_tokens": 1024,
    "stream": True,
}


def make_settings():
    return load_settings({"NVIDIA_API_KEY": "test-key"})


def make_transport(handler):
    return httpx.MockTransport(handler)


def make_client(transport, **kwargs):
    return NimClient(make_settings(), transport=transport, **kwargs)


def test_stream_mengembalikan_potongan():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=STREAM_BODY)

    client = make_client(make_transport(handler))
    try:
        assert list(client.stream([{"role": "user", "content": "hai"}])) == [
            "Halo",
            " dunia",
        ]
    finally:
        client.close()


def test_badan_permintaan_memuat_stream_true():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, text=STREAM_BODY)

    client = make_client(make_transport(handler))
    try:
        list(client.stream([{"role": "user", "content": "hai"}]))
    finally:
        client.close()

    assert captured["body"] == EXPECTED_BODY
    assert captured["body"]["stream"] is True
    assert list(captured["body"].keys()) == list(EXPECTED_BODY.keys())


def test_data_bukan_json_melempar_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="data: bukan-json\n\n")

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            list(client.stream([{"role": "user", "content": "hai"}]))
    finally:
        client.close()

    assert str(excinfo.value) == "Respons API tidak valid"
    assert excinfo.value.status_code is None


def test_status_401_melempar_api_error():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(401, json={"error": "unauthorized"})

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            list(client.stream([{"role": "user", "content": "hai"}]))
    finally:
        client.close()

    assert str(excinfo.value) == "API NVIDIA mengembalikan status 401"
    assert excinfo.value.status_code == 401
    assert len(calls) == 1


def test_galat_dilempar_saat_generator_dijalankan():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(401, json={"error": "unauthorized"})

    client = make_client(make_transport(handler))
    try:
        generator = client.stream([{"role": "user", "content": "hai"}])
        assert calls == []
        with pytest.raises(ApiError):
            next(generator)
        assert len(calls) == 1
    finally:
        client.close()


def test_payload_choices_bukan_daftar_melempar_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text='data: {"choices": "bukan"}\n\n')

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            list(client.stream([{"role": "user", "content": "hai"}]))
    finally:
        client.close()

    assert str(excinfo.value) == "Respons API tidak valid"


def test_stream_tanpa_retry():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(401, json={"error": "unauthorized"})

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError):
            list(client.stream([{"role": "user", "content": "hai"}]))
    finally:
        client.close()

    assert len(calls) == 1
