class ChatbotError(Exception):
    """Galat dasar untuk seluruh aplikasi chatbot."""


class ConfigError(ChatbotError):
    """Galat konfigurasi yang dapat diperbaiki pengguna."""


class ApiError(ChatbotError):
    """Galat saat berbicara dengan API NVIDIA."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
