"""Tes untuk loop percakapan CLI (Tugas 1)."""

from nim_chatbot.cli import chat_loop
from nim_chatbot.errors import ApiError
from nim_chatbot.history import Conversation

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


class KlienGalat:
    """Klien yang stream-nya melempar ApiError saat dipanggil."""

    def __init__(self, pesan):
        self.pesan = pesan
        self.panggilan = 0

    def stream(self, messages):
        self.panggilan += 1
        raise ApiError(self.pesan)

    def close(self):
        pass


class KlienGalatIterasi:
    """Klien yang stream-nya melempar ApiError saat diiterasi."""

    def __init__(self, pesan):
        self.pesan = pesan

    def stream(self, messages):
        raise ApiError(self.pesan)
        yield

    def close(self):
        pass


def buat_input(baris_list):
    """input_fn tiruan: catat prompt, keluarkan baris berurutan, EOFError bila habis."""
    prompt_diterima = []
    baris = iter(baris_list)

    def input_fn(prompt):
        prompt_diterima.append(prompt)
        try:
            return next(baris)
        except StopIteration:
            raise EOFError from None

    return input_fn, prompt_diterima


def test_obrolan_biasa_dan_keluar():
    klien = KlienTiruan(["Hai", " juga"])
    input_fn, prompt_diterima = buat_input(["Halo", "/exit"])
    keluaran = []
    percakapan = buat_percakapan()

    chat_loop(percakapan, klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == "Bot: Hai juga\nSampai jumpa.\n"
    assert klien.panggilan == [
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Halo"},
        ]
    ]
    assert percakapan.history == [
        {"role": "user", "content": "Halo"},
        {"role": "assistant", "content": "Hai juga"},
    ]
    assert prompt_diterima == ["Anda: ", "Anda: "]


def test_input_fn_selalu_dipanggil_dengan_prompt_anda():
    klien = KlienTiruan(["Hai"])
    input_fn, prompt_diterima = buat_input(["Halo", "Kabar?", "/quit"])

    chat_loop(buat_percakapan(), klien, input_fn=input_fn, write_fn=lambda teks: None)

    assert prompt_diterima == ["Anda: "] * 3


def test_galat_api_saat_stream_dipanggil():
    klien = KlienGalat("API NVIDIA mengembalikan status 401")
    input_fn, _ = buat_input(["Halo", "/exit"])
    keluaran = []
    percakapan = buat_percakapan()

    chat_loop(percakapan, klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == "Galat: API NVIDIA mengembalikan status 401\nSampai jumpa.\n"
    assert percakapan.history == []


def test_galat_api_saat_stream_diiterasi():
    klien = KlienGalatIterasi("API NVIDIA mengembalikan status 500")
    input_fn, _ = buat_input(["Halo", "/exit"])
    keluaran = []
    percakapan = buat_percakapan()

    chat_loop(percakapan, klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == "Galat: API NVIDIA mengembalikan status 500\nSampai jumpa.\n"
    assert percakapan.history == []


def test_respons_kosong():
    klien = KlienTiruan([])
    input_fn, _ = buat_input(["Halo", "/exit"])
    keluaran = []
    percakapan = buat_percakapan()

    chat_loop(percakapan, klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == "Galat: Respons kosong\nSampai jumpa.\n"
    assert percakapan.history == []


def test_loop_lanjut_setelah_galat():
    klien = KlienTiruan([])
    input_fn, _ = buat_input(["Halo", "Lagi", "/exit"])
    keluaran = []
    percakapan = buat_percakapan()
    pemanggilan = []

    def stream_galat_lalu_sukses(messages):
        pemanggilan.append(messages)
        if len(pemanggilan) == 1:
            raise ApiError("API NVIDIA mengembalikan status 503")
        yield from ["Hai", " juga"]

    klien.stream = stream_galat_lalu_sukses

    chat_loop(percakapan, klien, input_fn=input_fn, write_fn=keluaran.append)

    assert (
        "".join(keluaran)
        == "Galat: API NVIDIA mengembalikan status 503\nBot: Hai juga\nSampai jumpa.\n"
    )
    assert percakapan.history == [
        {"role": "user", "content": "Lagi"},
        {"role": "assistant", "content": "Hai juga"},
    ]


def test_baris_kosong_diabaikan():
    klien = KlienTiruan(["Hai"])
    input_fn, _ = buat_input(["", "   ", "/exit"])
    keluaran = []

    chat_loop(buat_percakapan(), klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == "Sampai jumpa.\n"
    assert klien.panggilan == []


def test_quit_sama_dengan_exit():
    klien = KlienTiruan(["Hai"])
    input_fn, _ = buat_input(["/quit"])
    keluaran = []

    chat_loop(buat_percakapan(), klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == "Sampai jumpa.\n"


def test_eof_error_diperlakukan_seperti_exit():
    klien = KlienTiruan(["Hai"])

    def input_eof(prompt):
        raise EOFError

    keluaran = []

    chat_loop(buat_percakapan(), klien, input_fn=input_eof, write_fn=keluaran.append)

    assert "".join(keluaran) == "Sampai jumpa.\n"


def test_perintah_tidak_dikenal():
    klien = KlienTiruan(["Hai"])
    input_fn, _ = buat_input(["/foo", "/exit"])
    keluaran = []

    chat_loop(buat_percakapan(), klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == "Perintah tidak dikenal. Ketik /help\nSampai jumpa.\n"
    assert klien.panggilan == []


def test_perintah_peka_huruf_besar_kecil():
    klien = KlienTiruan(["Hai"])
    input_fn, _ = buat_input(["/EXIT", "/exit"])
    keluaran = []

    chat_loop(buat_percakapan(), klien, input_fn=input_fn, write_fn=keluaran.append)

    assert "".join(keluaran) == "Perintah tidak dikenal. Ketik /help\nSampai jumpa.\n"
