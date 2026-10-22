import pytest

from nim_chatbot.history import Conversation, validate_history


def test_validate_history_mengembalikan_salinan():
    pesan = [{"role": "user", "content": "Halo"}]
    hasil = validate_history(pesan)
    assert hasil == pesan
    assert hasil is not pesan
    hasil[0]["content"] = "diubah"
    hasil.append({"role": "assistant", "content": "x"})
    assert pesan == [{"role": "user", "content": "Halo"}]


def test_validate_history_menerima_user_dan_assistant():
    pesan = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    assert validate_history(pesan) == pesan


@pytest.mark.parametrize(
    "pesan",
    [
        [],
        "bukan dict",
        {"role": "user"},
        {"role": "user", "content": "Halo", "extra": 1},
        {"role": "system", "content": "x"},
        {"role": "tool", "content": "x"},
        {"role": 1, "content": "x"},
        {"role": "user", "content": 123},
        {"role": "user", "content": None},
        {"role": "user", "content": ""},
    ],
)
def test_validate_history_tidak_valid(pesan):
    with pytest.raises(ValueError) as excinfo:
        validate_history([pesan])
    assert str(excinfo.value) == "Riwayat tidak valid"


def test_add_user_dan_add_assistant_memangkas_spasi():
    convo = Conversation("S", 100)
    convo.add_user("  Halo  ")
    convo.add_assistant("\tHai\n")
    assert convo.history == [
        {"role": "user", "content": "Halo"},
        {"role": "assistant", "content": "Hai"},
    ]


@pytest.mark.parametrize("teks", ["", "   ", "\t\n"])
def test_add_pesan_kosong_melempar(teks):
    convo = Conversation("S", 100)
    with pytest.raises(ValueError) as excinfo:
        convo.add_user(teks)
    assert str(excinfo.value) == "Pesan kosong"
    assert convo.history == []
    with pytest.raises(ValueError) as excinfo:
        convo.add_assistant(teks)
    assert str(excinfo.value) == "Pesan kosong"
    assert convo.history == []


def test_drop_last_menghapus_pesan_terakhir():
    convo = Conversation("S", 100)
    convo.add_user("a")
    convo.add_assistant("b")
    convo.drop_last()
    assert convo.history == [{"role": "user", "content": "a"}]


def test_drop_last_pada_riwayat_kosong_tidak_apa_apa():
    convo = Conversation("S", 100)
    convo.drop_last()
    assert convo.history == []


def test_reset_mengosongkan_riwayat():
    convo = Conversation("S", 100)
    convo.add_user("a")
    convo.reset()
    assert convo.history == []


def test_history_adalah_salinan_tanpa_pesan_sistem():
    convo = Conversation("S", 100)
    convo.add_user("a")
    riwayat = convo.history
    riwayat.append({"role": "user", "content": "penyusup"})
    assert convo.history == [{"role": "user", "content": "a"}]


def test_replace_history_valid():
    convo = Conversation("S", 100)
    convo.replace_history(
        [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    )
    assert convo.history == [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]


def test_replace_history_tidak_valid_melempar_dan_riwayat_utuh():
    convo = Conversation("S", 100)
    convo.add_user("lama")
    with pytest.raises(ValueError) as excinfo:
        convo.replace_history([{"role": "system", "content": "x"}])
    assert str(excinfo.value) == "Riwayat tidak valid"
    assert convo.history == [{"role": "user", "content": "lama"}]


def test_to_messages_memangkas_lalu_buang_assistant_awal():
    convo = Conversation("S", 10)
    convo.add_user("aaaa")
    convo.add_assistant("bbbb")
    convo.add_user("cccc")
    assert convo.to_messages() == [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "cccc"},
    ]
    assert len(convo.history) == 3


def test_to_messages_tanpa_pemangkasan_urutan_terjaga():
    convo = Conversation("S", 100)
    convo.add_user("aaaa")
    convo.add_assistant("bbbb")
    convo.add_user("cccc")
    assert convo.to_messages() == [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "aaaa"},
        {"role": "assistant", "content": "bbbb"},
        {"role": "user", "content": "cccc"},
    ]


def test_to_messages_pesan_terakhir_tidak_pernah_dibuang():
    convo = Conversation("S", 3)
    convo.add_user("abcdef")
    assert convo.to_messages() == [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "abcdef"},
    ]


def test_to_messages_tepat_pada_batas_tidak_memangkas():
    convo = Conversation("S", 8)
    convo.add_user("aaaa")
    convo.add_assistant("bbbb")
    assert convo.to_messages() == [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "aaaa"},
        {"role": "assistant", "content": "bbbb"},
    ]


def test_to_messages_sisa_satu_assistant_tetap_ada():
    convo = Conversation("S", 6)
    convo.add_user("aaaa")
    convo.add_assistant("bbbb")
    assert convo.to_messages() == [
        {"role": "system", "content": "S"},
        {"role": "assistant", "content": "bbbb"},
    ]


def test_to_messages_panjang_prompt_sistem_tidak_dihitung():
    prompt = "S" * 500
    convo = Conversation(prompt, 10)
    convo.add_user("12345")
    assert convo.to_messages() == [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "12345"},
    ]


def test_to_messages_riwayat_kosong_hanya_pesan_sistem():
    convo = Conversation("S", 10)
    assert convo.to_messages() == [{"role": "system", "content": "S"}]


def test_to_messages_tidak_mengubah_riwayat_asli():
    convo = Conversation("S", 10)
    convo.add_user("aaaa")
    convo.add_assistant("bbbb")
    convo.add_user("cccc")
    convo.to_messages()
    assert convo.history == [
        {"role": "user", "content": "aaaa"},
        {"role": "assistant", "content": "bbbb"},
        {"role": "user", "content": "cccc"},
    ]


def test_hasil_to_messages_dan_history_adalah_salinan():
    convo = Conversation("S", 100)
    convo.add_user("a")
    pesan = convo.to_messages()
    pesan.append({"role": "user", "content": "penyusup"})
    pesan[1]["content"] = "diubah"
    assert convo.to_messages() == [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "a"},
    ]
    assert convo.history == [{"role": "user", "content": "a"}]
