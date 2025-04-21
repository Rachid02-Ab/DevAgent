import os

class Settings:
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "onYcoSEMsQRVRfrt7WfjQrwrMcKJ8HzE")
    MAX_ATTEMPTS: int = 3

settings = Settings()