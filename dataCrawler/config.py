import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

ROOT_ENV = Path(__file__).resolve().parents[1] / ".env"
if load_dotenv:
    load_dotenv(ROOT_ENV)
    load_dotenv(Path(__file__).resolve().parent / ".env", override=False)
else:
    for env_file in (ROOT_ENV, Path(__file__).resolve().parent / ".env"):
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


def database_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "databili"),
    }


def credential_values():
    enabled = os.getenv("BILI_USE_CREDENTIAL", "false").lower() == "true"
    return enabled, os.getenv("BILI_SESSDATA", ""), os.getenv("BILI_BILI_JCT", "")
