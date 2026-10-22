"""Antarmuka baris perintah: loop percakapan dan perintah keluar."""

import sys

from nim_chatbot.errors import ApiError


def _stdout_write(teks: str) -> None:
    """Tulis teks ke stdout tanpa newline tambahan lalu flush."""
    sys.stdout.write(teks)
    sys.stdout.flush()


def chat_loop(conversation, client, input_fn=input, write_fn=_stdout_write) -> None:
    """Jalankan loop percakapan sampai pengguna keluar."""
    while True:
        try:
            baris = input_fn("Anda: ")
        except EOFError:
            baris = "/exit"
        teks = baris.strip()
        if not teks:
            continue
        if teks.startswith("/"):
            if teks in ("/exit", "/quit"):
                write_fn("Sampai jumpa.\n")
                break
            write_fn("Perintah tidak dikenal. Ketik /help\n")
            continue
        conversation.add_user(teks)
        potongan: list[str] = []
        try:
            for i, potong in enumerate(client.stream(conversation.to_messages())):
                if i == 0:
                    write_fn("Bot: ")
                write_fn(potong)
                potongan.append(potong)
        except ApiError as galat:
            conversation.drop_last()
            write_fn(f"Galat: {galat}\n")
            continue
        if not potongan:
            conversation.drop_last()
            write_fn("Galat: Respons kosong\n")
            continue
        conversation.add_assistant("".join(potongan))
        write_fn("\n")
