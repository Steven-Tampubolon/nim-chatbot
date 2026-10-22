import httpx
import pytest

from nim_chatbot.client import NimClient
from nim_chatbot.config import load_settings
from nim_chatbot.errors import ApiError

SUCCESS_BODY = {"choices": [{"message": {"role": "assistant", "content": "Halo!"}}]}

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


def make_settings():
    return load_settings({"NVIDIA_API_KEY": "test-key"})


def make_transport(handler):
    return httpx.MockTransport(handler)


def make_client(transport, **kwargs):
    return NimClient(make_settings(), transport=transport, **kwargs)


class Recorder:
    def __init__(self):
        self.sleeps = []

    def sleep(self, seconds):
        self.sleeps.append(seconds)


def status_sequence_handler(statuses, success_body=None):
    calls = []

    def handler(request):
        index = len(calls)
        calls.append(request)
        status = statuses[index]
        if status == 200:
            if success_body is None:
                return httpx.Response(200, json=SUCCESS_BODY)
            return httpx.Response(200, text=success_body)
        return httpx.Response(status, json={"error": "boom"})

    return handler, calls


def test_chat_retry_429_lalu_sukses():
    handler, calls = status_sequence_handler([429, 200])
    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        assert client.chat([{"role": "user", "content": "hai"}]) == "Halo!"
    finally:
        client.close()

    assert len(calls) == 2
    assert recorder.sleeps == [1.0]


def test_chat_retry_beberapa_status():
    handler, calls = status_sequence_handler([500, 502, 503, 200])
    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        assert client.chat([{"role": "user", "content": "hai"}]) == "Halo!"
    finally:
        client.close()

    assert len(calls) == 4
    assert recorder.sleeps == [1.0, 2.0, 4.0]


def test_chat_status_selalu_503():
    handler, calls = status_sequence_handler([503, 503, 503, 503])
    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "API NVIDIA mengembalikan status 503"
    assert excinfo.value.status_code == 503
    assert len(calls) == 4
    assert recorder.sleeps == [1.0, 2.0, 4.0]


def test_chat_status_401_tanpa_retry():
    handler, calls = status_sequence_handler([401])
    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "API NVIDIA mengembalikan status 401"
    assert excinfo.value.status_code == 401
    assert len(calls) == 1
    assert recorder.sleeps == []


def test_chat_transport_error_selalu():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectError("boom")

    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "Gagal terhubung ke API NVIDIA"
    assert excinfo.value.status_code is None
    assert len(calls) == 4
    assert recorder.sleeps == [1.0, 2.0, 4.0]


def test_chat_transport_error_sekali_lalu_sukses():
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            raise httpx.ConnectError("boom")
        return httpx.Response(200, json=SUCCESS_BODY)

    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        assert client.chat([{"role": "user", "content": "hai"}]) == "Halo!"
    finally:
        client.close()

    assert len(calls) == 2
    assert recorder.sleeps == [1.0]


def test_chat_max_retries_nol():
    handler, calls = status_sequence_handler([503])
    recorder = Recorder()
    client = make_client(
        make_transport(handler), sleep=recorder.sleep, max_retries=0
    )
    try:
        with pytest.raises(ApiError) as excinfo:
            client.chat([{"role": "user", "content": "hai"}])
    finally:
        client.close()

    assert str(excinfo.value) == "API NVIDIA mengembalikan status 503"
    assert excinfo.value.status_code == 503
    assert len(calls) == 1
    assert recorder.sleeps == []


def test_stream_retry_503_lalu_sukses():
    handler, calls = status_sequence_handler([503, 200], success_body=STREAM_BODY)
    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        assert list(client.stream([{"role": "user", "content": "hai"}])) == [
            "Halo",
            " dunia",
        ]
    finally:
        client.close()

    assert len(calls) == 2
    assert recorder.sleeps == [1.0]


def test_stream_status_selalu_503():
    handler, calls = status_sequence_handler([503, 503, 503, 503])
    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        with pytest.raises(ApiError) as excinfo:
            list(client.stream([{"role": "user", "content": "hai"}]))
    finally:
        client.close()

    assert str(excinfo.value) == "API NVIDIA mengembalikan status 503"
    assert excinfo.value.status_code == 503
    assert len(calls) == 4
    assert recorder.sleeps == [1.0, 2.0, 4.0]


def test_stream_transport_error_selalu():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectError("boom")

    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        with pytest.raises(ApiError) as excinfo:
            list(client.stream([{"role": "user", "content": "hai"}]))
    finally:
        client.close()

    assert str(excinfo.value) == "Gagal terhubung ke API NVIDIA"
    assert excinfo.value.status_code is None
    assert len(calls) == 4
    assert recorder.sleeps == [1.0, 2.0, 4.0]


def test_stream_galat_status_dilempar_saat_generator_dijalankan():
    handler, calls = status_sequence_handler([401])
    recorder = Recorder()
    client = make_client(make_transport(handler), sleep=recorder.sleep)
    try:
        generator = client.stream([{"role": "user", "content": "hai"}])
        assert calls == []
        with pytest.raises(ApiError):
            next(generator)
        assert len(calls) == 1
        assert recorder.sleeps == []
    finally:
        client.close()
