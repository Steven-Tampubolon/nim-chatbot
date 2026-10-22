"""Tes untuk fungsi main CLI (Tugas 3)."""

import pytest

from nim_chatbot.cli import main
from nim_chatbot.config import Settings


class KlienTiruan:
    """Klien tiruan dengan stream generator dan pencatat close()."""

    def __init__(self):
        self.ditutup = 0

    def stream(self, messages):
        yield from []

    def close(self):
        self.ditutup += 1


def buat_pabrik(klien):
    """Pabrik tiruan yang mencatat Settings yang diterima."""
    panggilan = []

    def factory(settings):
        panggilan.append(settings)
        return klien

    return factory, panggilan


def buat_input(baris_list):
    """input_fn tiruan: keluarkan baris berurutan, EOFError bila habis."""
    baris = iter(baris_list)

    def input_fn(prompt):
        try:
            return next(baris)
        except StopIteration:
            raise EOFError from None

    return input_fn


def test_config_galat_mengembalikan_2_dan_pabrik_tidak_dipanggil():
    input_fn = buat_input(["/exit"])
    keluaran = []
    klien = KlienTiruan()
    factory, panggilan = buat_pabrik(klien)

    kode = main(
        [],
        {},
        input_fn=input_fn,
        write_fn=keluaran.append,
        client_factory=factory,
    )

    assert kode == 2
    assert "".join(keluaran) == "Galat: NVIDIA_API_KEY belum diatur\n"
    assert panggilan == []
    assert klien.ditutup == 0


def test_sukses_dengan_model_dan_close_dipanggil():
    input_fn = buat_input(["/exit"])
    keluaran = []
    klien = KlienTiruan()
    factory, panggilan = buat_pabrik(klien)

    kode = main(
        ["--model", "m1"],
        {"NVIDIA_API_KEY": "k"},
        input_fn=input_fn,
        write_fn=keluaran.append,
        client_factory=factory,
    )

    assert kode == 0
    assert "".join(keluaran) == (
        "Chatbot NVIDIA NIM (model: m1). Ketik /help untuk bantuan.\n"
        "Sampai jumpa.\n"
    )
    assert len(panggilan) == 1
    assert isinstance(panggilan[0], Settings)
    assert panggilan[0].model == "m1"
    assert panggilan[0].api_key == "k"
    assert klien.ditutup == 1
