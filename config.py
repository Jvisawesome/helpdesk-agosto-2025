import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "helpdesk_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "helpdesk_password")
    DB_NAME = os.getenv("DB_NAME", "helpdesk_db")
    DB_PORT = int(os.getenv("DB_PORT", "3307"))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
