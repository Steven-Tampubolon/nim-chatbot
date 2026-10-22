import nim_chatbot


def test_paket_dapat_diimpor():
    assert nim_chatbot is not None


def test_versi_paket():
    assert nim_chatbot.__version__ == "0.1.0"
