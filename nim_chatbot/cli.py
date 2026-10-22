"""Antarmuka baris perintah: loop percakapan dan perintah keluar."""

import argparse
import os
import sys
from dataclasses import replace

from nim_chatbot.client import NimClient
from nim_chatbot.config import load_settings
from nim_chatbot.errors import ApiError, ChatbotError, ConfigError
from nim_chatbot.history import Conversation
from nim_chatbot.storage import load_conversation, save_conversation


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
            kata = teks.split(None, 1)
            perintah = kata[0]
            sisa = kata[1].strip() if len(kata) > 1 else ""
            if perintah == "/help":
                write_fn(
                    "Perintah: /help, /reset, /save <berkas>, /load <berkas>, /exit\n"
                )
                continue
            if perintah == "/reset":
                conversation.reset()
                write_fn("Percakapan direset.\n")
                continue
            if perintah == "/save":
                if not sisa:
                    write_fn("Pemakaian: /save <berkas>\n")
                    continue
                try:
                    save_conversation(sisa, conversation.history)
                except ChatbotError as galat:
                    write_fn(f"Galat: {galat}\n")
                    continue
                write_fn(f"Tersimpan ke {sisa}\n")
                continue
            if perintah == "/load":
                if not sisa:
                    write_fn("Pemakaian: /load <berkas>\n")
                    continue
                try:
                    pesan = load_conversation(sisa)
                except ChatbotError as galat:
                    write_fn(f"Galat: {galat}\n")
                    continue
                conversation.replace_history(pesan)
                write_fn(f"Dimuat {len(pesan)} pesan dari {sisa}\n")
                continue
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


def main(
    argv=None,
    env=None,
    input_fn=input,
    write_fn=_stdout_write,
    client_factory=NimClient,
) -> int:
    """Rangkai konfigurasi, klien, dan loop percakapan."""
    if argv is None:
        argv = sys.argv[1:]
    if env is None:
        env = os.environ

    parser = argparse.ArgumentParser(prog="nim_chatbot")
    parser.add_argument("--model", default=None)
    args = parser.parse_args(argv)

    try:
        settings = load_settings(env)
    except ConfigError as galat:
        write_fn(f"Galat: {galat}\n")
        return 2

    if args.model is not None:
        settings = replace(settings, model=args.model)

    client = client_factory(settings)
    try:
        write_fn(
            f"Chatbot NVIDIA NIM (model: {settings.model}). "
            "Ketik /help untuk bantuan.\n"
        )
        chat_loop(
            Conversation(settings.system_prompt, settings.max_history_chars),
            client,
            input_fn,
            write_fn,
        )
    finally:
        client.close()
    return 0
