import os


class Config:
    SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 1933))
    CONSOLE_HOST = os.getenv("CONSOLE_HOST", "127.0.0.1")
    CONSOLE_PORT = int(os.getenv("CONSOLE_PORT", 8020))

    SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
    CONSOLE_URL = f"http://{CONSOLE_HOST}:{CONSOLE_PORT}"

    ATOM_CTX_API_KEY = os.getenv("ATOM_CTX_API_KEY", "test-root-api-key")
    ATOM_CTX_ACCOUNT = os.getenv("ATOM_CTX_ACCOUNT", "default")
    ATOM_CTX_USER = os.getenv("ATOM_CTX_USER", "default")

    SERVER_STARTUP_TIMEOUT = 30
    CONSOLE_STARTUP_TIMEOUT = 30
    SERVICE_CHECK_INTERVAL = 1

    USE_PYENV = os.getenv("CTX_USE_PYENV", "true").lower() == "true"
