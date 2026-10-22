"""Simpan dan muat percakapan dalam berkas JSON UTF-8."""

import json
from pathlib import Path

from nim_chatbot.errors import ChatbotError
from nim_chatbot.history import validate_history

_INVALID_MESSAGE = "Berkas percakapan tidak valid"


def save_conversation(path: str | Path, history: list[dict]) -> None:
    """Simpan riwayat percakapan ke berkas JSON dengan format versi 1."""
    pesan = validate_history(history)
    lokasi = Path(path)
    lokasi.parent.mkdir(parents=True, exist_ok=True)
    data = {"version": 1, "messages": pesan}
    lokasi.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_conversation(path: str | Path) -> list[dict]:
    """Muat riwayat percakapan dari berkas JSON dan validasi isinya."""
    lokasi = Path(path)
    try:
        teks = lokasi.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ChatbotError(f"Berkas tidak ditemukan: {str(path)}") from None
    except UnicodeDecodeError:
        raise ChatbotError(_INVALID_MESSAGE) from None
    try:
        data = json.loads(teks)
    except json.JSONDecodeError:
        raise ChatbotError(_INVALID_MESSAGE) from None
    if (
        not isinstance(data, dict)
        or type(data.get("version")) is not int
        or data["version"] != 1
        or not isinstance(data.get("messages"), list)
    ):
        raise ChatbotError(_INVALID_MESSAGE)
    try:
        return validate_history(data["messages"])
    except ValueError:
        raise ChatbotError(_INVALID_MESSAGE) from None
