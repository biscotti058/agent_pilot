from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.sanitizer import DocumentSanitizer, SanitizeOptions, extract_text_from_bytes

router = APIRouter()
EXPORT_DIR = Path(__file__).resolve().parents[4] / "data" / "sanitized"


class SanitizeTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Testo del documento da sanificare")
    options: dict[str, Any] = Field(default_factory=dict)
    save_export: bool = Field(False, description="Salva copia sanificata in data/sanitized/")


class SanitizeTextResponse(BaseModel):
    sanitized_text: str
    report: dict[str, Any]
    original_length: int
    sanitized_length: int
    export_path: str | None = None


def _build_options(raw: dict[str, Any]) -> SanitizeOptions:
    return SanitizeOptions(
        redact_emails=raw.get("redact_emails", True),
        redact_phones=raw.get("redact_phones", True),
        redact_fiscal_codes=raw.get("redact_fiscal_codes", True),
        redact_vat_numbers=raw.get("redact_vat_numbers", True),
        redact_iban=raw.get("redact_iban", True),
        redact_credit_cards=raw.get("redact_credit_cards", True),
        redact_ip_addresses=raw.get("redact_ip_addresses", True),
        redact_internal_ids=raw.get("redact_internal_ids", True),
        redact_person_names=raw.get("redact_person_names", True),
        redact_company_domains=raw.get("redact_company_domains", True),
        company_domains=raw.get("company_domains") or settings.sanitize_company_domains,
        company_keywords=raw.get("company_keywords") or settings.sanitize_company_keywords,
    )


def _maybe_save_export(content: str, filename: str) -> str:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    if not safe_name.endswith(".sanitized.txt"):
        stem = Path(safe_name).stem
        safe_name = f"{stem}.sanitized.txt"
    out_path = EXPORT_DIR / safe_name
    out_path.write_text(content, encoding="utf-8")
    return str(out_path)


@router.post("/sanitize/text", response_model=SanitizeTextResponse)
async def sanitize_text_endpoint(request: SanitizeTextRequest):
    sanitizer = DocumentSanitizer(_build_options(request.options))
    result = sanitizer.sanitize(request.text)

    export_path = None
    if request.save_export:
        export_path = _maybe_save_export(result.sanitized_text, "document.sanitized.txt")

    return SanitizeTextResponse(
        sanitized_text=result.sanitized_text,
        report={
            "total_redactions": result.report.total_redactions,
            "by_category": result.report.by_category,
            "company_data_found": result.report.company_data_found,
            "safe_to_export": result.report.safe_to_export,
            "warnings": result.report.warnings,
        },
        original_length=result.original_length,
        sanitized_length=len(result.sanitized_text),
        export_path=export_path,
    )


@router.post("/sanitize/file", response_model=SanitizeTextResponse)
async def sanitize_file_endpoint(
    file: UploadFile = File(...),
    save_export: bool = True,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome file mancante.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File vuoto.")

    try:
        text = extract_text_from_bytes(content, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    sanitizer = DocumentSanitizer(
        SanitizeOptions(
            company_domains=settings.sanitize_company_domains,
            company_keywords=settings.sanitize_company_keywords,
        )
    )
    result = sanitizer.sanitize(text)

    export_path = None
    if save_export:
        export_path = _maybe_save_export(result.sanitized_text, file.filename)

    return SanitizeTextResponse(
        sanitized_text=result.sanitized_text,
        report={
            "total_redactions": result.report.total_redactions,
            "by_category": result.report.by_category,
            "company_data_found": result.report.company_data_found,
            "safe_to_export": result.report.safe_to_export,
            "warnings": result.report.warnings,
        },
        original_length=result.original_length,
        sanitized_length=len(result.sanitized_text),
        export_path=export_path,
    )


@router.get("/sanitize/patterns")
async def list_patterns():
    """Elenco categorie di dati rilevati dal motore di sanificazione."""
    return {
        "categories": [
            {"id": "email", "label": "Indirizzi email"},
            {"id": "email_aziendale", "label": "Email con dominio aziendale configurato"},
            {"id": "telefono", "label": "Numeri di telefono (IT/internazionali)"},
            {"id": "codice_fiscale", "label": "Codice fiscale italiano"},
            {"id": "partita_iva", "label": "Partita IVA"},
            {"id": "iban", "label": "Coordinate bancarie IBAN"},
            {"id": "credit_card", "label": "Numeri carta di credito"},
            {"id": "ip_address", "label": "Indirizzi IP"},
            {"id": "id_interno", "label": "ID interni (EMP-, PRJ-, TCK-, ecc.)"},
            {"id": "matricola", "label": "Matricole dipendenti"},
            {"id": "nome_persona", "label": "Nomi con titolo (Sig., Dott., ecc.)"},
            {"id": "keyword_aziendale", "label": "Parole chiave aziendali configurate"},
        ],
        "company_domains": settings.sanitize_company_domains,
        "company_keywords": settings.sanitize_company_keywords,
    }
