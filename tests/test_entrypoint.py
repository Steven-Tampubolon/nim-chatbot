"""Tes titik masuk modul dan dokumentasi (Tugas 4)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NAMA_VARIABEL = [
    "NVIDIA_API_KEY",
    "NVIDIA_MODEL",
    "NVIDIA_BASE_URL",
    "CHATBOT_SYSTEM_PROMPT",
    "CHATBOT_MAX_HISTORY_CHARS",
]


def test_python_m_nim_chatbot_help_keluar_0_dan_memuat_model():
    env = {"LC_ALL": "C.UTF-8", "PYTHONIOENCODING": "utf-8"}
    hasil = subprocess.run(
        [sys.executable, "-m", "nim_chatbot", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert hasil.returncode == 0
    assert "--model" in hasil.stdout


def test_readme_memuat_teks_wajib():
    isi = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "NVIDIA_API_KEY" in isi
    assert "python -m nim_chatbot" in isi
    assert "python -m pytest -q" in isi


def test_env_example_ada_dan_memuat_lima_variabel():
    isi = (ROOT / ".env.example").read_text(encoding="utf-8")
    for nama in NAMA_VARIABEL:
        assert f"{nama}=" in isi


def test_env_example_api_key_kosong_dan_tanpa_kunci_asli():
    isi = (ROOT / ".env.example").read_text(encoding="utf-8")
    baris_key = next(
        baris for baris in isi.splitlines() if baris.startswith("NVIDIA_API_KEY=")
    )
    assert baris_key == "NVIDIA_API_KEY="
    assert "nvapi-" not in isi
