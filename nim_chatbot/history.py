"""Riwayat percakapan: validasi, penyimpanan, dan pemangkasan pesan."""

_ROLES = ("user", "assistant")


def validate_history(messages: list[dict]) -> list[dict]:
    """Validasi daftar pesan dan mengembalikan salinannya."""
    hasil: list[dict] = []
    for pesan in messages:
        if not isinstance(pesan, dict) or set(pesan) != {"role", "content"}:
            raise ValueError("Riwayat tidak valid")
        role = pesan["role"]
        content = pesan["content"]
        if role not in _ROLES or not isinstance(content, str) or content == "":
            raise ValueError("Riwayat tidak valid")
        hasil.append({"role": role, "content": content})
    return hasil


class Conversation:
    """Percakapan berjalan dengan prompt sistem dan batas panjang riwayat."""

    def __init__(self, system_prompt: str, max_chars: int) -> None:
        self.system_prompt = system_prompt
        self.max_chars = max_chars
        self._history: list[dict] = []

    def add_user(self, text: str) -> None:
        """Tambahkan pesan pengguna setelah memangkas spasi tepi."""
        self._add("user", text)

    def add_assistant(self, text: str) -> None:
        """Tambahkan pesan asisten setelah memangkas spasi tepi."""
        self._add("assistant", text)

    def _add(self, role: str, text: str) -> None:
        teks = text.strip()
        if not teks:
            raise ValueError("Pesan kosong")
        self._history.append({"role": role, "content": teks})

    def reset(self) -> None:
        """Kosongkan riwayat percakapan."""
        self._history.clear()

    def drop_last(self) -> None:
        """Hapus pesan terakhir; tidak melakukan apa pun bila kosong."""
        if self._history:
            self._history.pop()

    @property
    def history(self) -> list[dict]:
        """Salinan daftar pesan tanpa pesan sistem."""
        return [dict(pesan) for pesan in self._history]

    def replace_history(self, messages: list[dict]) -> None:
        """Ganti seluruh riwayat dengan pesan yang sudah divalidasi."""
        self._history = validate_history(messages)

    def to_messages(self) -> list[dict]:
        """Pesan system lebih dulu, lalu riwayat yang sudah dipangkas."""
        riwayat = [dict(pesan) for pesan in self._history]
        total = sum(len(pesan["content"]) for pesan in riwayat)
        while len(riwayat) > 1 and total > self.max_chars:
            total -= len(riwayat[0]["content"])
            riwayat.pop(0)
        if len(riwayat) > 1 and riwayat[0]["role"] == "assistant":
            riwayat.pop(0)
        return [{"role": "system", "content": self.system_prompt}, *riwayat]
