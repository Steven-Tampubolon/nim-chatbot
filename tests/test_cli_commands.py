"""Tes untuk perintah /help, /reset, /save, dan /load (Tugas 2)."""

from nim_chatbot.cli import chat_loop
from nim_chatbot.history import Conversation
from nim_chatbot.storage import load_conversation

SYSTEM_PROMPT = "Anda asisten yang ramah."


def buat_percakapan():
    return Conversation(SYSTEM_PROMPT, max_chars=10000)


class KlienTiruan:
    """Klien dengan stream generator yang mencatat pesan yang diterima."""

    def __init__(self, potongan=None):
        self.panggilan = []
        self.potongan = potongan if potongan is not None else []

    def stream(self, messages):
        self.panggilan.append([dict(pesan) for pesan in messages])
        yield from self.potongan

    def close(self):
        pass


def buat_input(baris_list):
    """input_fn tiruan: keluarkan baris berurutan, EOFError bila habis."""
    baris = iter(baris_list)

    def input_fn(prompt):
        try:
            return next(baris)
        except StopIteration:
            raise EOFError from None

    return input_fn


def test_help():
    klien = KlienTiruan()
    input_fn = buat_input(["/help", "/exit"])
    keluaran = []

    chat_loop(buat_percakapan(), klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == (
        "Perintah: /help, /reset, /save <berkas>, /load <berkas>, /exit\n"
        "Sampai jumpa.\n"
    )
    assert klien.panggilan == []
