import json

import pytest

from nim_chatbot.errors import ChatbotError
from nim_chatbot.storage import load_conversation, save_conversation


def test_simpan_lalu_muat_mengembalikan_daftar_sama(tmp_path):
    berkas = tmp_path / "conv.json"
    riwayat = [
        {"role": "user", "content": "kopi di café"},
        {"role": "assistant", "content": "oke"},
    ]
    save_conversation(berkas, riwayat)
    assert load_conversation(berkas) == riwayat


def test_berkas_berisi_unicode_tanpa_escape(tmp_path):
    berkas = tmp_path / "conv.json"
    save_conversation(
        berkas,
        [{"role": "user", "content": "kopi di café"}],
    )
    teks = berkas.read_text(encoding="utf-8")
    assert "café" in teks
    assert "\\u00e9" not in teks


def test_format_berkas_versi_dan_indentasi(tmp_path):
    berkas = tmp_path / "conv.json"
    save_conversation(berkas, [{"role": "user", "content": "hai"}])
    teks = berkas.read_text(encoding="utf-8")
    assert teks.startswith('{\n  "version": 1,\n  "messages": [')
    assert teks.endswith("]\n}")


def test_simpan_membuat_folder_induk(tmp_path):
    berkas = tmp_path / "sub" / "x.json"
    save_conversation(berkas, [{"role": "user", "content": "hai"}])
    assert berkas.is_file()
    assert load_conversation(berkas) == [{"role": "user", "content": "hai"}]


def test_path_string_diterima(tmp_path):
    berkas = tmp_path / "conv.json"
    save_conversation(str(berkas), [{"role": "assistant", "content": "oke"}])
    assert load_conversation(str(berkas)) == [{"role": "assistant", "content": "oke"}]


def test_riwayat_kosong(tmp_path):
    berkas = tmp_path / "empty.json"
    save_conversation(berkas, [])
    assert load_conversation(berkas) == []


def test_muat_berkas_tidak_ada(tmp_path):
    berkas = tmp_path / "hilang.json"
    with pytest.raises(ChatbotError) as excinfo:
        load_conversation(berkas)
    assert str(excinfo.value) == f"Berkas tidak ditemukan: {berkas}"


def test_muat_berkas_tidak_ada_path_string(tmp_path):
    berkas = tmp_path / "hilang.json"
    with pytest.raises(ChatbotError) as excinfo:
        load_conversation(str(berkas))
    assert str(excinfo.value) == f"Berkas tidak ditemukan: {berkas}"


def test_muat_json_rusak(tmp_path):
    berkas = tmp_path / "rusak.json"
    berkas.write_text("bukan json", encoding="utf-8")
    with pytest.raises(ChatbotError) as excinfo:
        load_conversation(berkas)
    assert str(excinfo.value) == "Berkas percakapan tidak valid"


@pytest.mark.parametrize(
    "data",
    [
        {"version": 2, "messages": []},
        {"version": 1, "messages": {"role": "user", "content": "hai"}},
        {"version": 1, "messages": [{"role": "system", "content": "hai"}]},
        {"version": 1, "messages": [{"role": "user", "content": ""}]},
        {"version": 1, "messages": [{"role": "user"}]},
        {"version": 1, "messages": ["bukan dict"]},
        {"version": 1},
        {"messages": []},
        {"version": True, "messages": []},
        [],
        None,
    ],
)
def test_muat_struktur_tidak_valid(tmp_path, data):
    berkas = tmp_path / "invalid.json"
    berkas.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ChatbotError) as excinfo:
        load_conversation(berkas)
    assert str(excinfo.value) == "Berkas percakapan tidak valid"
