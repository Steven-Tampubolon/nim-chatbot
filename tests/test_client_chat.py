import json

import httpx
import pytest

from nim_chatbot.client import NimClient
from nim_chatbot.config import load_settings
from nim_chatbot.errors import ApiError

SUCCESS_BODY = {"choices": [{"message": {"role": "assistant", "content": "Halo!"}}]}

EXPECTED_BODY = {
    "model": "z-ai/glm-5.3",
    "messages": [{"role": "user", "content": "hai"}],
    "temperature": 0.6,
    "max_tokens": 1024,
    "stream": False,
}


def make_settings():
    return load_settings({"NVIDIA_API_KEY": "test-key"})


def make_transport(handler):
    return httpx.MockTransport(handler)


def make_client(transport, **kwargs):
    return NimClient(make_settings(), transport=transport, **kwargs)


def test_chat_mengembalikan_konten():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=SUCCESS_BODY)

    client = make_client(make_transport(handler))
    try:
        assert client.chat([{"role": "user", "content": "hai"}]) == "Halo!"
    finally:
        client.close()


def test_permintaan_tertangkap():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=SUCCESS_BODY)

    client = make_client(make_transport(handler))
    try:
        client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert captured["method"] == "POST"
    assert captured["url"] == "https://integrate.api.nvidia.com/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["body"] == EXPECTED_BODY


def test_urutan_kunci_badan_permintaan():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=SUCCESS_BODY)

    client = make_client(make_transport(handler))
    try:
        client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert list(captured["body"].keys()) == list(EXPECTED_BODY.keys())


def test_status_401_melempar_api_error():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(401, json={"error": "unauthorized"})

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "API NVIDIA mengembalikan status 401"
    assert excinfo.value.status_code == 401
    assert len(calls) == 1


def test_badan_bukan_json_melempar_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="bukan json")

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "Respons API tidak valid"
    assert excinfo.value.status_code is None


def test_tanpa_choices_melempar_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "Respons API tidak valid"


def test_choices_kosong_melempar_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "Respons API tidak valid"


def test_content_bukan_str_melempar_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        body = {"choices": [{"message": {"role": "assistant", "content": 123}}]}
        return httpx.Response(200, json=body)

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "Respons API tidak valid"


def test_galat_tidak_membocorkan_kunci():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="bukan json")

    client = make_client(make_transport(handler))
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert "test-key" not in str(excinfo.value)
    assert "test-key" not in repr(excinfo.value)


def test_parameter_konstruktor_diterima():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=SUCCESS_BODY)

    def fake_sleep(seconds: float) -> None:
        raise AssertionError("sleep tidak boleh dipanggil di tugas ini")

    client = make_client(
        make_transport(handler),
        sleep=fake_sleep,
        max_retries=5,
        timeout=1.0,
    )
    try:
        assert client.chat([{"role": "user", "content": "hai"}]) == "Halo!"
    finally:
        client.close()


def test_close_menutup_klien():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=SUCCESS_BODY)

    client = make_client(make_transport(handler))
    client.close()

    with pytest.raises(RuntimeError):
        client.chat([{"role": "user", "content": "hai"}])
