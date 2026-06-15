"""Modulo I - Sanificazione documenti (rimozione PII e dati aziendali)."""

from typing import Any

from app.core.config import settings
from app.core.sanitizer import DocumentSanitizer, SanitizeOptions, extract_text_from_bytes
from app.modules.base import BaseModule

SANITIZE_KEYWORDS = [
    "sanifica",
    "sanificare",
    "anonimizza",
    "anonimizzare",
    "rimuovi dati personali",
    "rimuovere dati personali",
    "pii",
    "gdpr",
    "dati sensibili",
    "redact",
    "oscura",
    "maschera dati",
    "esporta senza",
    "pulisci documento",
]


class SanitizationModule(BaseModule):
    name = "sanitization"
    description = "Sanificazione documenti: rimuove dati personali e aziendali per export sicuro"
    phase = 1

    async def can_handle(self, intent: str, context: dict[str, Any]) -> float:
        text = intent.lower().strip()
        if text.startswith("/sanitize") or text.startswith("/sanifica"):
            return 1.0
        if context.get("text") or context.get("document"):
            return 0.85
        matches = sum(1 for kw in SANITIZE_KEYWORDS if kw in text)
        return min(matches * 0.4, 0.95)

    async def execute(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        text = payload.get("text") or payload.get("document") or self._extract_text_from_message(intent)

        if not text:
            return {
                "status": "error",
                "message": (
                    "Fornisci il testo da sanificare nel campo 'text' del context, "
                    "oppure incollalo dopo i due punti. Esempio: "
                    "'Sanifica: Mario Rossi mario.rossi@azienda.it CF RSSMRA80A01H501Z'"
                ),
                "commands": self.get_commands(),
            }

        options = self._build_options(payload)
        sanitizer = DocumentSanitizer(options)
        result = sanitizer.sanitize(text)

        return {
            "status": "ok",
            "sanitized_text": result.sanitized_text,
            "report": {
                "total_redactions": result.report.total_redactions,
                "by_category": result.report.by_category,
                "company_data_found": result.report.company_data_found,
                "safe_to_export": result.report.safe_to_export,
                "warnings": result.report.warnings,
            },
            "original_length": result.original_length,
            "sanitized_length": len(result.sanitized_text),
        }

    def get_commands(self) -> list[str]:
        return ["/sanitize", "/sanifica", "/sanitize file"]

    def _extract_text_from_message(self, message: str) -> str | None:
        for sep in (":", "—", "-"):
            if sep in message:
                head, _, tail = message.partition(sep)
                if any(kw in head.lower() for kw in SANITIZE_KEYWORDS) or head.strip().startswith("/"):
                    candidate = tail.strip()
                    if candidate:
                        return candidate
        return None

    def _build_options(self, payload: dict[str, Any]) -> SanitizeOptions:
        opts = payload.get("options", {})
        domains = opts.get("company_domains") or settings.sanitize_company_domains
        keywords = opts.get("company_keywords") or settings.sanitize_company_keywords

        return SanitizeOptions(
            redact_emails=opts.get("redact_emails", True),
            redact_phones=opts.get("redact_phones", True),
            redact_fiscal_codes=opts.get("redact_fiscal_codes", True),
            redact_vat_numbers=opts.get("redact_vat_numbers", True),
            redact_iban=opts.get("redact_iban", True),
            redact_credit_cards=opts.get("redact_credit_cards", True),
            redact_ip_addresses=opts.get("redact_ip_addresses", True),
            redact_internal_ids=opts.get("redact_internal_ids", True),
            redact_person_names=opts.get("redact_person_names", True),
            redact_company_domains=opts.get("redact_company_domains", True),
            company_domains=domains,
            company_keywords=keywords,
        )


def sanitize_text(text: str, options: SanitizeOptions | None = None) -> dict[str, Any]:
    """Helper sincrono per le route API."""
    sanitizer = DocumentSanitizer(options or SanitizeOptions())
    result = sanitizer.sanitize(text)
    return {
        "sanitized_text": result.sanitized_text,
        "report": {
            "total_redactions": result.report.total_redactions,
            "by_category": result.report.by_category,
            "company_data_found": result.report.company_data_found,
            "safe_to_export": result.report.safe_to_export,
            "warnings": result.report.warnings,
        },
        "original_length": result.original_length,
        "sanitized_length": len(result.sanitized_text),
    }
