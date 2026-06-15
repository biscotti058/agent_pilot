# WorkFlow Assistant

Agente AI per gestione operativa — costruito **un passo alla volta**.

## Piano per gradi

| Passo | Cosa facciamo | Stato |
|-------|---------------|-------|
| **1** | API base + **sanificazione documenti** | **Adesso** |
| **2** | Modulo Tasks con lista in memoria | Prossimo |
| **3** | Docker con solo l'API | Dopo |
| **4** | Postgres — task salvati sul disco | |
| **5** | Modulo Writing con AI | |
| **6** | Moduli Correction + Excel | |
| **7** | Worker + Scheduler (stack Docker completo) | |
| **8** | Integrazioni (Outlook, Teams, Notion) | |

Ogni passo produce qualcosa di **funzionante e testabile** prima di passare al successivo.

---

## Passo 1 — API base (senza Docker)

Requisiti: **Python 3.11+** installato.

```powershell
cd auto_copilot
.\scripts\start-step1.ps1
```

Oppure manualmente:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-step1.txt
uvicorn app.main:app --reload --port 8000
```

### Verifica

- Browser: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: `GET /health` → `{"status": "ok"}`
- Chat: `POST /api/v1/chat` con body `{"message": "aggiungi task mail a Marco"}`

A questo passo i moduli rispondono con stub — **sanificazione documenti è già funzionante**.

---

## Sanificazione documenti

Rimuove dati personali (PII) e dati aziendali prima dell'export.

**Categorie rilevate:** email, telefoni, codice fiscale, P.IVA, IBAN, carte, IP, ID interni, matricole, nomi con titolo, domini/keyword aziendali.

### Via chat

```json
POST /api/v1/chat
{
  "message": "Sanifica questo testo",
  "context": {
    "text": "Sig. Mario Rossi — mario.rossi@deloitte.it — CF RSSMRA80A01H501Z — tel +39 333 1234567"
  }
}
```

### Via API dedicata

```json
POST /api/v1/sanitize/text
{
  "text": "...",
  "save_export": true,
  "options": {
    "company_domains": ["deloitte.com", "deloitte.it"]
  }
}
```

Upload file: `POST /api/v1/sanitize/file` (multipart, `.txt` `.md` `.csv` `.json`)

Configura domini aziendali in `.env`:

```
SANITIZE_COMPANY_DOMAINS=deloitte.com,deloitte.it
SANITIZE_COMPANY_KEYWORDS=progetto alpha,cliente riservato
```

I file sanificati vengono salvati in `data/sanitized/`.

> **Nota:** la sanificazione automatica non sostituisce una revisione umana prima di condividere documenti sensibili.

---

## Passi futuri (non ancora attivi)

### Passo 3 — Docker solo API

```powershell
docker compose up --build
```

### Passo 7 — Stack completo

```powershell
docker compose --profile full up --build
```

Include Postgres, Redis, Worker e Scheduler.

---

## Struttura progetto

```
auto_copilot/
├── scripts/start-step1.ps1   # Avvio locale passo 1
├── docker-compose.yml        # API di default; stack full con --profile full
├── .env.example
└── backend/
    ├── requirements-step1.txt  # Dipendenze minime
    ├── requirements.txt        # Tutte le dipendenze (passi successivi)
    └── app/
        ├── main.py
        ├── agent/orchestrator.py
        ├── api/routes/
        └── modules/            # Un modulo per ogni funzione
```

## API

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/chat` | POST | Messaggio all'agente |
| `/api/v1/modules` | GET | Moduli registrati |
| `/api/v1/sanitize/text` | POST | Sanifica testo |
| `/api/v1/sanitize/file` | POST | Sanifica file upload |
| `/api/v1/sanitize/patterns` | GET | Categorie rilevate |
| `/docs` | GET | Swagger UI |
