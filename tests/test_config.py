import dataclasses

import pytest

from nim_chatbot.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    Settings,
    load_settings,
)
from nim_chatbot.errors import ConfigError


def test_bawaan_lengkap():
    settings = load_settings({"NVIDIA_API_KEY": "k"})
    assert settings == Settings(
        api_key="k",
        model="z-ai/glm-5.3",
        base_url="https://integrate.api.nvidia.com/v1",
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        max_history_chars=12000,
    )
    assert DEFAULT_MODEL == "z-ai/glm-5.3"
    assert DEFAULT_BASE_URL == "https://integrate.api.nvidia.com/v1"
    assert DEFAULT_SYSTEM_PROMPT == (
        "Kamu adalah asisten yang ramah dan ringkas. "
        "Jawab dalam bahasa yang dipakai pengguna."
    )


def test_base_url_tanpa_garis_miring_akhir():
    settings = load_settings(
        {"NVIDIA_API_KEY": "k", "NVIDIA_BASE_URL": "https://x.test/v1/"}
    )
    assert settings.base_url == "https://x.test/v1"


def test_base_url_spasi_dipangkas():
    settings = load_settings(
        {"NVIDIA_API_KEY": "k", "NVIDIA_BASE_URL": "  https://x.test/v1/  "}
    )
    assert settings.base_url == "https://x.test/v1"


@pytest.mark.parametrize("api_key", [None, "", "  "])
def test_kunci_hilang_melempar_config_error(api_key):
    env = {} if api_key is None else {"NVIDIA_API_KEY": api_key}
    with pytest.raises(ConfigError) as excinfo:
        load_settings(env)
    assert str(excinfo.value) == "NVIDIA_API_KEY belum diatur"


def test_max_history_chars_valid():
    settings = load_settings(
        {"NVIDIA_API_KEY": "k", "CHATBOT_MAX_HISTORY_CHARS": "500"}
    )
    assert settings.max_history_chars == 500


@pytest.mark.parametrize("raw", ["abc", "0", "-5"])
def test_max_history_chars_tidak_valid(raw):
    with pytest.raises(ConfigError) as excinfo:
        load_settings({"NVIDIA_API_KEY": "k", "CHATBOT_MAX_HISTORY_CHARS": raw})
    assert (
        str(excinfo.value) == "CHATBOT_MAX_HISTORY_CHARS harus bilangan bulat positif"
    )


def test_max_history_chars_kosong_dianggap_tidak_diatur():
    settings = load_settings(
        {"NVIDIA_API_KEY": "k", "CHATBOT_MAX_HISTORY_CHARS": "  "}
    )
    assert settings.max_history_chars == 12000


def test_model_dan_prompt_kustom():
    settings = load_settings(
        {
            "NVIDIA_API_KEY": "k",
            "NVIDIA_MODEL": "  model-kustom  ",
            "CHATBOT_SYSTEM_PROMPT": "  Prompt kustom  ",
        }
    )
    assert settings.model == "model-kustom"
    assert settings.system_prompt == "Prompt kustom"


def test_kunci_tidak_muncul_di_repr():
    settings = load_settings({"NVIDIA_API_KEY": "k-rahasia"})
    assert "k-rahasia" not in repr(settings)


def test_settings_beku():
    settings = load_settings({"NVIDIA_API_KEY": "k"})
    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.model = "model-lain"
