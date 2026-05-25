# DeckLens

DeckLens is an AI-powered contextual presentation evaluation platform. It ingests PPT, PPTX, and PDF decks, extracts slide content, applies OCR when needed, classifies slides and frameworks, runs reasoning-aware analysis, and generates a downloadable PDF report. The product is designed for case decks, startup pitches, consulting-style presentations, and evaluation workflows where the prompt matters more than generic slide quality.

## Features

- Authenticated presentation review workflow with JWT bearer tokens.
- Upload support for `.ppt`, `.pptx`, and `.pdf` files.
- Server-side file validation, size checks, and local storage of uploaded decks.
- Slide extraction from PowerPoint and PDF sources.
- OCR fallback for image-heavy or text-poor slides.
- Slide classification into business presentation categories.
- Hybrid framework detection using semantic embeddings, FAISS, and keyword signals.
- Context-aware evaluation of prompt alignment and evidence grounding.
- Ollama-backed executive summary and consultant-style feedback generation.
- PDF report generation with scoring, audit, and narrative sections.
- Per-user presentation history, slide views, analysis status, and report downloads.
- Celery-backed background processing for extraction, analysis, and report generation.

## Architecture

DeckLens is split into a Next.js frontend, a FastAPI backend, a PostgreSQL database, a Redis-backed Celery queue, and a local AI/runtime layer for OCR, embeddings, framework matching, and report generation.

```mermaid
flowchart LR
	U[User] --> FE[Next.js Frontend]
	FE --> API[FastAPI Backend]
	API --> DB[(PostgreSQL)]
	API --> REDIS[(Redis)]
	REDIS --> CEL[Celery Worker]
	CEL --> PARSE[Parse deck and OCR]
	CEL --> ANALYSIS[Reasoning and LLM analysis]
	CEL --> REPORT[PDF report generation]
	PARSE --> SLIDES[(Slides + metadata)]
	ANALYSIS --> ANALYSISDB[(Analysis record)]
	REPORT --> PDF[(Report PDF)]
```

The backend is responsible for the core workflow:

- Upload validation and persistence.
- Authentication and authorization.
- Slide extraction from decks.
- OCR and text normalization.
- Classification and framework matching.
- Reasoning audit and score generation.
- PDF report rendering and storage.

The frontend is responsible for:

- Registration and login.
- Dashboard and upload flows.
- Presentation status tracking.
- Slide-level presentation review.
- Report generation and download actions.

### Authentication

- Users register through `/api/v1/auth/register` and log in through `/api/v1/auth/login`.
- Login returns a JWT bearer token.
- The frontend stores the token in `localStorage` and attaches it to API requests with an Axios interceptor.
- Protected backend routes use `app.core.auth.get_current_user` to validate the bearer token.
- Logout is client-side only and clears the stored token.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4, Zustand, Axios |
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic, Uvicorn |
| AI / ML | SentenceTransformers, FAISS, Torch, Ollama, pytesseract, PyMuPDF, python-pptx |
| Database | PostgreSQL 16, JSONB, psycopg2-binary |
| Queue System | Redis, Celery |
| Reporting | ReportLab |
| File Handling | python-multipart, Pillow, LibreOffice/soffice for legacy `.ppt` conversion |

## Project Structure

| Path | Purpose |
| --- | --- |
| `backend/app/api/v1/endpoints/` | REST endpoints for auth, uploads, analysis, reports, and health checks |
| `backend/app/models/` | SQLAlchemy models for users, presentations, slides, analyses, and reports |
| `backend/app/schemas/` | Pydantic response/request schemas |
| `backend/app/services/parsing/` | PDF/PPTX parsing, OCR, and legacy PPT conversion |
| `backend/app/services/processing/` | Slide classification, framework matching, embeddings, and queue helpers |
| `backend/app/services/analysis/` | Prompt parsing, reasoning audit, scorecard computation, and Ollama feedback |
| `backend/app/services/reporting/` | PDF report payload assembly and ReportLab rendering |
| `backend/app/workers/` | Celery app and asynchronous task definitions |
| `backend/alembic/` | Database migrations |
| `backend/uploads/` | Stored uploaded files and extracted slide assets |
| `backend/reports/` | Generated PDF reports |
| `frontend/src/app/` | Next.js routes for home, login, register, dashboard, upload, and presentation detail pages |
| `frontend/src/components/` | Shared UI components such as the themed popup and navigation shell |
| `frontend/src/lib/` | Axios API client |
| `frontend/src/store/` | Client auth state |

## System Flow

```mermaid
flowchart LR
	A[Upload PPT / PPTX / PDF] --> B[Validate file and store locally]
	B --> C[Queue Celery extraction task]
	C --> D[Parse slides from PDF or PPTX]
	D --> E[OCR slide images when needed]
	E --> F[Normalize text and extract slide metadata]
	F --> G[Classify slide category]
	G --> H[Detect business framework matches]
	H --> I[Build reasoning context from prompt]
	I --> J[Compute reasoning audit and scores]
	J --> K[Call Ollama for narrative feedback]
	K --> L[Persist Analysis record]
	L --> M[Generate PDF report]
	M --> N[Download final report]
```

In practice, upload triggers extraction first. Analysis and PDF report generation are separate background jobs that run after extraction is complete and the previous step is ready.

## Backend Setup

### 1. Create and activate a virtual environment

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

The project ships a full runtime dependency list in `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL and Redis

You can run them locally or use Docker:

```bash
docker compose up -d db redis
```

### 4. Create the backend environment file

Create `backend/.env` with the required runtime settings.

```env
PROJECT_NAME=PresentIQ
ENVIRONMENT=development

DATABASE_URL=postgresql+psycopg2://presentiq:presentiq@localhost:5432/presentiq
REDIS_URL=redis://localhost:6379/0

SECRET_KEY=change-me-to-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080

API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

UPLOADS_DIR=uploads
REPORTS_DIR=reports
MAX_UPLOAD_SIZE_MB=50
```

The required variables are `DATABASE_URL`, `REDIS_URL`, and `SECRET_KEY`. The remaining values can stay at their defaults unless you need different ports, model names, or storage locations.

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the FastAPI server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start the Celery worker

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

### 8. Backend runtime notes

- The backend uses PostgreSQL for persistence.
- Redis is required as the Celery broker and result backend.
- Ollama must be reachable at the configured base URL for narrative analysis.
- Legacy `.ppt` files require LibreOffice or `soffice` on the machine running the parser.
- OCR requires Tesseract to be installed and available on the system PATH.

## Frontend Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Run the Next.js app

```bash
npm run dev
```

### 3. Frontend environment notes

The current frontend reads the API URL directly from `frontend/src/lib/api.ts` and points to `http://localhost:8000/api/v1`.

There is no required frontend `.env` file today. If you later externalize the API base URL, an example would look like this:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## Environment Variables

### Backend

```env
PROJECT_NAME=PresentIQ
ENVIRONMENT=development
DATABASE_URL=postgresql+psycopg2://presentiq:presentiq@localhost:5432/presentiq
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-to-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b
UPLOADS_DIR=uploads
REPORTS_DIR=reports
MAX_UPLOAD_SIZE_MB=50
```

### Frontend

```env
# Not currently required by the frontend codebase.
# The API client is hardcoded to http://localhost:8000/api/v1 in src/lib/api.ts.
# If you externalize that later, use the variable below.
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## API Overview

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic service status |
| `GET` | `/api/v1/health` | Database health check |
| `POST` | `/api/v1/auth/register` | Create a user account |
| `POST` | `/api/v1/auth/login` | Return a JWT bearer token |
| `GET` | `/api/v1/auth/me` | Return the authenticated user |
| `POST` | `/api/v1/presentations/upload` | Upload and queue a presentation for extraction |
| `GET` | `/api/v1/presentations` | List the current user’s presentations |
| `GET` | `/api/v1/presentations/{presentation_id}` | Fetch one presentation |
| `DELETE` | `/api/v1/presentations/{presentation_id}` | Delete a presentation, its slides, analysis, and report |
| `POST` | `/api/v1/presentations/{presentation_id}/extract` | Re-queue slide extraction |
| `GET` | `/api/v1/presentations/{presentation_id}/slides` | List extracted slides |
| `POST` | `/api/v1/presentations/{presentation_id}/analysis/generate` | Queue contextual analysis |
| `GET` | `/api/v1/presentations/{presentation_id}/analysis` | Fetch the computed analysis |
| `POST` | `/api/v1/presentations/{presentation_id}/report/generate` | Queue PDF report generation |
| `GET` | `/api/v1/presentations/{presentation_id}/report` | Fetch report metadata |
| `GET` | `/api/v1/presentations/{presentation_id}/report/download` | Download the generated PDF |

## AI / ML Pipeline

### Prompt Parsing and Context

The backend parses the uploaded case prompt into structured sections using `build_evaluation_context` and `parse_prompt_sections`. This creates:

- A cleaned problem statement.
- Expected focus areas.
- Evaluation criteria.
- A domain type inferred from the prompt and rubric.
- Domain-specific expected categories and frameworks.

### Slide Extraction

- PDF files are parsed with PyMuPDF.
- PPTX files are parsed with `python-pptx`.
- Legacy `.ppt` files are first converted to `.pptx` through LibreOffice/soffice in headless mode.
- Slide text is normalized before downstream scoring.
- Image assets are extracted into `uploads/extracted/<presentation_id>/slide_<n>/`.
- OCR is applied with `pytesseract` when text extraction is insufficient or the slide contains image content.

### Slide Classification

Slide category classification is rule-based and prompt-aware rather than LLM-based.

- `classifier.py` scores slide text against category keyword rules.
- Domain priors boost the categories that are expected for that domain.
- Slide titles and slide position provide additional heuristics.
- The output is a `slide_category`, a confidence value, and a reason string.

### Framework Detection

Framework detection is hybrid semantic matching, not just keyword lookup.

- `framework_catalog.py` defines the built-in framework corpus.
- `embeddings.py` uses `SentenceTransformer("all-MiniLM-L6-v2")` to generate normalized embeddings.
- `framework_detector.py` builds a FAISS `IndexFlatIP` index over framework reference texts.
- Semantic similarity, keyword hits, title hits, and domain priors are combined into a final framework score.
- The current implementation uses FAISS for framework similarity, not as a general user-facing search feature.

### Reasoning Audit and Scores

- `reasoner.py` derives prompt alignment, evidence grounding, unsupported claims, reasoning gaps, and slide insights.
- `scorer.py` combines business logic, strategy, analytical depth, financial soundness, clarity, framework utilization, prompt alignment, and evidence grounding into the final scorecard.
- The reasoning audit is fed into both scoring and narrative generation.

### LLM Feedback

- `llm_feedback.py` sends structured context to Ollama.
- The default model is `llama3:8b`.
- Ollama is used to generate `executive_summary` and `consultant_feedback`, plus the narrative bullets that complement the rule-based scorecard.
- If the LLM call fails or returns invalid JSON, the backend falls back to deterministic rule-based feedback.

## Database Design

| Model | Responsibility | Important Fields |
| --- | --- | --- |
| `User` | Authentication identity | `email`, `full_name`, `hashed_password`, `is_active` |
| `Presentation` | Uploaded deck and workflow state | `case_prompt`, `domain_type`, `evaluation_rubric`, `file_path`, `stored_filename`, `processing_status`, `user_id` |
| `Slide` | Extracted slide artifact | `slide_number`, `slide_title`, `extracted_text`, `ocr_text`, `image_paths`, `slide_category`, `primary_framework`, `framework_matches` |
| `Analysis` | Contextual evaluation output | Scores, `score_breakdown`, `slide_insights`, `unsupported_claims`, `reasoning_gaps`, `strengths`, `weaknesses`, `missing_elements`, `recommendations`, `investor_questions`, `executive_summary`, `consultant_feedback` |
| `Report` | Generated PDF metadata | `report_status`, `report_filename`, `report_file_path`, `report_summary`, `error_message`, `generated_at` |

The database is migrated with Alembic. Migrations live under `backend/alembic/versions/`.

## Current Capabilities

- Upload and validate presentation files.
- Extract text and images from slides.
- Run OCR on image-based content.
- Classify slides into presentation categories.
- Detect frameworks with semantic and keyword matching.
- Generate prompt-aligned scorecards.
- Produce reasoning audit output with unsupported claims and reasoning gaps.
- Generate consultant-style summaries with Ollama.
- Render downloadable PDF reports.
- Track presentations and reports per authenticated user.

## Limitations

- The frontend API URL is currently hardcoded to `http://localhost:8000/api/v1`.
- Celery, Redis, PostgreSQL, and Ollama are required at runtime; the app is not self-contained.
- Legacy `.ppt` conversion depends on LibreOffice/soffice.
- OCR depends on Tesseract being installed on the machine or container.
- FAISS-based matching currently covers the built-in framework corpus only.
- Report generation is local filesystem based; there is no object storage integration yet.
- The app uses bearer tokens stored in browser localStorage, so there is no refresh-token flow.

## Future Improvements

- Externalize the frontend API URL into environment configuration.
- Add a Celery worker service to the Docker Compose stack.
- Package Tesseract and LibreOffice into the deployment image.
- Persist or version the vector reference corpus separately from code.
- Add task progress telemetry to the UI.
- Add object storage support for uploaded decks and generated reports.
- Add a production LLM abstraction layer for Ollama or hosted model providers.
- Add richer slide-level drill-downs and export formats.

## Deployment

DeckLens is straightforward to run locally, but production deployment needs more than a single web container.

| Requirement | Why it matters |
| --- | --- |
| PostgreSQL | Stores users, presentations, slides, analyses, and reports |
| Redis | Celery broker and result backend |
| Celery worker | Executes extraction, analysis, and report jobs asynchronously |
| Ollama | Provides local LLM-backed narrative feedback |
| Torch / SentenceTransformers | Required for embedding generation |
| FAISS | Supports framework similarity matching |
| Tesseract | Required for OCR |
| LibreOffice / soffice | Required for legacy `.ppt` conversion |

Operational notes:

- The current `docker-compose.yml` starts PostgreSQL, Redis, and the FastAPI backend, but not the Celery worker.
- The backend Docker image is minimal and does not install system OCR or office-conversion binaries by default.
- Large ML dependencies can make container builds heavier than a typical CRUD application.
- If you deploy to a server or container platform, make sure the worker process, Redis, Ollama, and the system packages needed for OCR/PPT conversion are reachable from the backend runtime.

## Screenshots

![Home](docs/screenshots/home.png)
