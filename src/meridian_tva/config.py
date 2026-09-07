"""Configuration : variables d'environnement (fichier .env optionnel) avec des défauts."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else value.strip()


@dataclass(frozen=True)
class Settings:
    pg_host: str = _env("POSTGRES_HOST", "127.0.0.1")
    pg_port: int = int(_env("POSTGRES_PORT", "5435"))
    pg_db: str = _env("POSTGRES_DB", "tva")
    pg_user: str = _env("POSTGRES_USER", "meridian")
    pg_password: str = _env("POSTGRES_PASSWORD", "meridian")

    vies_url: str = _env("VIES_URL", "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number")
    vies_status_url: str = _env("VIES_STATUS_URL", "https://ec.europa.eu/taxation_customs/vies/rest-api/check-status")
    vies_timeout: float = float(_env("VIES_TIMEOUT", "30"))
    vies_delay: float = float(_env("VIES_DELAY", "1.5"))
    vies_requester_country: str = _env("VIES_REQUESTER_COUNTRY", "")
    vies_requester_number: str = _env("VIES_REQUESTER_NUMBER", "")
    verdict_ttl_hours: float = float(_env("VERDICT_TTL_HOURS", "24"))
    native_tls: bool = _env("NATIVE_TLS", "0") in {"1", "true", "yes"}

    data_file: Path = field(default_factory=lambda: Path(_env("DATA_FILE", "data/numeros_tva.csv")))
    report_file: Path = field(default_factory=lambda: Path(_env("REPORT_FILE", "docs/rapport-reconciliation.md")))
    log_dir: Path = field(default_factory=lambda: Path(_env("LOG_DIR", "logs")))

    @property
    def pg_conninfo(self) -> str:
        return (
            f"host={self.pg_host} port={self.pg_port} dbname={self.pg_db} "
            f"user={self.pg_user} password={self.pg_password}"
        )


def enable_native_tls_if_requested(settings: Settings) -> None:
    """Postes avec interception TLS : utiliser les certificats du système plutôt que désactiver la vérification."""
    if settings.native_tls:
        import truststore

        truststore.inject_into_ssl()
