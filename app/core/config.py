import os

APP_VERSION = os.getenv("APP_VERSION", "0.3.0")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://db_financeiro:fin_pass@localhost:5432/financeiro_encontro"
)

APP_PORT = int(os.getenv("APP_PORT", "8000"))

JWT_SECRET = os.getenv("JWT_SECRET", "changeme-insecure-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
