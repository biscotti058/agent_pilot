"""Motore di sanificazione documenti — rimuove PII e dati aziendali sensibili."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class PatternRule:
    category: str
    pattern: re.Pattern[str]
    placeholder_prefix: str
    priority: int = 50


@dataclass
class SanitizeOptions:
    redact_emails: bool = True
    redact_phones: bool = True
    redact_fiscal_codes: bool = True
    redact_vat_numbers: bool = True
    redact_iban: bool = True
    redact_credit_cards: bool = True
    redact_ip_addresses: bool = True
    redact_internal_ids: bool = True
    redact_person_names: bool = True
    redact_company_domains: bool = True
    company_domains: list[str] = field(default_factory=list)
    company_keywords: list[str] = field(default_factory=list)


@dataclass
class SanitizationReport:
    total_redactions: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    company_data_found: bool = False
    safe_to_export: bool = True
    warnings: list[str] = field(default_factory=list)


@dataclass
class SanitizationResult:
    original_length: int
    sanitized_text: str
    report: SanitizationReport


def _compile(pattern: str, flags: int = re.IGNORECASE) -> re.Pattern[str]:
    return re.compile(pattern, flags)


def _build_rules(options: SanitizeOptions) -> list[PatternRule]:
    rules: list[PatternRule] = []

    if options.redact_iban:
        rules.append(PatternRule(
            "iban",
            _compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
            "IBAN",
            priority=10,
        ))

    if options.redact_credit_cards:
        rules.append(PatternRule(
            "credit_card",
            _compile(r"\b(?:\d[ -]?){13,19}\b"),
            "CARTA",
            priority=15,
        ))

    if options.redact_fiscal_codes:
        rules.append(PatternRule(
            "codice_fiscale",
            _compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b"),
            "CF",
            priority=20,
        ))

    if options.redact_vat_numbers:
        rules.append(PatternRule(
            "partita_iva",
            _compile(r"\b(?:P\.?\s*IVA|Partita\s*IVA)\s*[:\s]?\s*(?:IT\s*)?\d{11}\b|\bIT\d{11}\b"),
            "PIVA",
            priority=25,
        ))

    if options.redact_emails:
        rules.append(PatternRule(
            "email",
            _compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            "EMAIL",
            priority=30,
        ))

    if options.redact_phones:
        rules.append(PatternRule(
            "telefono",
            _compile(
                r"(?:\+39|0039)?[\s.-]?"
                r"(?:\(?\d{2,4}\)?[\s.-]?)?"
                r"\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,4}(?:[\s.-]?\d{1,4})?"
            ),
            "TEL",
            priority=40,
        ))

    if options.redact_ip_addresses:
        rules.append(PatternRule(
            "ip_address",
            _compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
            "IP",
            priority=45,
        ))

    if options.redact_internal_ids:
        rules.extend([
            PatternRule(
                "id_interno",
                _compile(r"\b(?:EMP|MAT|ID|USR|PRJ|WO|TCK)[-_]?\d{3,10}\b"),
                "ID_INT",
                priority=35,
            ),
            PatternRule(
                "matricola",
                _compile(r"\b(?:matricola|employee\s*id|badge)\s*[:\s#-]*\d{3,10}\b", re.IGNORECASE),
                "MATRICOLA",
                priority=35,
            ),
        ])

    if options.redact_person_names:
        rules.append(PatternRule(
            "nome_persona",
            _compile(
                r"(?<!\w)(?:Sig\.|Sig\.ra|Sigg?\.|Dr\.|Dott\.|Dott\.ssa|Ing\.|Avv\.|Prof\.)\s+"
                r"[A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)+"
            ),
            "PERSONA",
            priority=55,
        ))

    for keyword in options.company_keywords:
        if keyword.strip():
            escaped = re.escape(keyword.strip())
            rules.append(PatternRule(
                "keyword_aziendale",
                _compile(rf"\b{escaped}\b", re.IGNORECASE),
                "AZIENDA",
                priority=5,
            ))

    return sorted(rules, key=lambda r: r.priority)


class DocumentSanitizer:
    """Rileva e sostituisce dati personali e aziendali con placeholder anonimi."""

    def __init__(self, options: SanitizeOptions | None = None) -> None:
        self.options = options or SanitizeOptions()
        self._rules = _build_rules(self.options)

    def sanitize(self, text: str) -> SanitizationResult:
        if not text or not text.strip():
            report = SanitizationReport(
                safe_to_export=False,
                warnings=["Documento vuoto — nulla da sanificare."],
            )
            return SanitizationResult(
                original_length=len(text),
                sanitized_text=text,
                report=report,
            )

        working = text
        counters: dict[str, int] = {}
        value_map: dict[str, str] = {}
        by_category: dict[str, int] = {}
        company_data_found = False
        warnings: list[str] = []

        def replace_match(category: str, prefix: str, match: re.Match[str]) -> str:
            nonlocal company_data_found
            value = match.group(0)

            if category == "telefono" and sum(c.isdigit() for c in value) < 8:
                return value

            if category == "credit_card" and sum(c.isdigit() for c in value) < 13:
                return value

            if category == "partita_iva":
                digits = re.sub(r"\D", "", value)
                if len(digits) != 11:
                    return value

            if category == "email" and self.options.redact_company_domains:
                domain = value.split("@")[-1].lower()
                if any(domain == d.lower() or domain.endswith(f".{d.lower()}") for d in self.options.company_domains):
                    company_data_found = True
                    prefix = "EMAIL_AZIENDALE"

            if category == "keyword_aziendale":
                company_data_found = True

            key = f"{category}:{value.lower()}"
            if key not in value_map:
                counters[prefix] = counters.get(prefix, 0) + 1
                value_map[key] = f"[{prefix}_{counters[prefix]}]"

            by_category[category] = by_category.get(category, 0) + 1
            return value_map[key]

        for rule in self._rules:
            working = rule.pattern.sub(
                lambda m, cat=rule.category, pre=rule.placeholder_prefix: replace_match(cat, pre, m),
                working,
            )

        if self.options.redact_company_domains:
            working, extra_company = self._redact_company_domain_emails(working, counters, value_map, by_category)
            company_data_found = company_data_found or extra_company

        total = sum(by_category.values())
        if total == 0:
            warnings.append(
                "Nessun dato sensibile rilevato con i pattern attuali. "
                "Rileggi manualmente prima di esportare."
            )

        report = SanitizationReport(
            total_redactions=total,
            by_category=by_category,
            company_data_found=company_data_found,
            safe_to_export=total > 0 or len(warnings) == 0,
            warnings=warnings,
        )

        return SanitizationResult(
            original_length=len(text),
            sanitized_text=working,
            report=report,
        )

    def _redact_company_domain_emails(
        self,
        text: str,
        counters: dict[str, int],
        value_map: dict[str, str],
        by_category: dict[str, int],
    ) -> tuple[str, bool]:
        if not self.options.company_domains:
            return text, False

        found_company = False
        domain_pattern = "|".join(re.escape(d.lower()) for d in self.options.company_domains)
        pattern = _compile(
            rf"\b[A-Za-z0-9._%+-]+@(?:{domain_pattern})\b",
            re.IGNORECASE,
        )

        def replacer(match: re.Match[str]) -> str:
            nonlocal found_company
            value = match.group(0)
            key = f"email_aziendale:{value.lower()}"
            if key not in value_map:
                counters["EMAIL_AZIENDALE"] = counters.get("EMAIL_AZIENDALE", 0) + 1
                value_map[key] = f"[EMAIL_AZIENDALE_{counters['EMAIL_AZIENDALE']}]"
            by_category["email_aziendale"] = by_category.get("email_aziendale", 0) + 1
            found_company = True
            return value_map[key]

        return pattern.sub(replacer, text), found_company


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    """Estrae testo da file supportati (.txt, .md, .csv, .json)."""
    name = filename.lower()

    if name.endswith((".txt", ".md", ".csv", ".json", ".log", ".xml", ".html", ".htm")):
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="replace")

    raise ValueError(
        f"Formato '{filename}' non supportato. "
        "Usa .txt, .md, .csv, .json (altri formati in arrivo)."
    )
