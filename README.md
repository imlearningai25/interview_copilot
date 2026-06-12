# Interview Copilot

AI-powered interview assistant. Listens to interview questions, answers from your resume using Claude AI. Manages target job context via a web app.

---

## Architecture

| Component | What it does | Port |
|---|---|---|
| `copilot.py` | Desktop overlay — listens & answers | — |
| Frontend (React) | Web UI to manage job configs | 4002 |
| Backend (FastAPI) | REST API + job storage | 4001 |
| PostgreSQL | Job config database | 4000 |
| `job_setup.py` | Legacy simple job form (optional) | 4003 |

---

## Local Development

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Python 3.10+ (for the desktop copilot)
- An [Anthropic API key](https://console.anthropic.com/)

### Step 1 — Copy and fill in the environment file

```bash
cp .env.example .env
```

Open `.env` and set your API key:

```
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

Everything else has working defaults.

### Step 2 — Start the web stack

```bash
docker compose up --build
```

First run takes ~2 minutes to pull images and build containers.

When you see both of these lines, the stack is ready:

```
backend-1   | INFO:     Application startup complete.
frontend-1  |   ➜  Local:   http://localhost:4002/
```

### Step 3 — Open the web app and set your target job

Open **http://localhost:4002** in your browser.

1. Click **+ New Job**
2. Fill in the role, company, location, and paste the full job description
3. Click **Save**
4. On the job card, click **Set Active**
5. The green banner will show the active job
6. Click **Ready** — it will show you instructions to launch the copilot

### Step 4 — Install desktop copilot dependencies

Run once in **PowerShell**:

```powershell
pip install -r requirements.txt
```

If PyAudio fails on Windows:

```powershell
pip install pipwin; pipwin install pyaudio
```

### Step 5 — Start the launcher (keep this running)

Open **PowerShell** in the project folder and run:

```powershell
python launcher.py
```

Leave this terminal open. The launcher listens on port 4004 and will start `copilot.py` whenever you click **Ready** in the browser.

> **Important — use PowerShell, not Git Bash** for the launcher. Git Bash has quirks with Windows GUI process management that prevent Tkinter windows from appearing.

---

## Stopping

```bash
docker compose down
```

To also wipe the database (start fresh):

```bash
docker compose down -v
```

---

## Restarting after changes

| What changed | Command |
|---|---|
| Backend Python code | Auto-reloads (uvicorn `--reload`) |
| Frontend React code | Auto-reloads (Vite HMR) |
| `docker-compose.yml` or `Dockerfile` | `docker compose up --build` |
| `.env` values | `docker compose down && docker compose up` |

---

## Production Deployment (GCP)

### Prerequisites

- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (`gcloud`)
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- A GCP project with billing enabled
- Docker Desktop (for building images)

### Step 1 — Authenticate with GCP

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Step 2 — Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  vpcaccess.googleapis.com \
  servicenetworking.googleapis.com
```

### Step 3 — Initialize Terraform

```bash
cd terraform
terraform init
```

### Step 4 — Create a `terraform.tfvars` file

```bash
cp terraform.tfvars.example terraform.tfvars   # if it exists, else create it
```

Fill in `terraform/terraform.tfvars`:

```hcl
project_id  = "your-gcp-project-id"
region      = "us-east1"
environment = "production"
db_password = "a-strong-random-password"
domain      = "your-domain.com"   # or leave blank for auto-assigned URL
```

### Step 5 — Plan and apply infrastructure

```bash
terraform plan
terraform apply
```

Type `yes` when prompted. This creates:
- VPC + private subnet
- Cloud SQL (PostgreSQL 15)
- Artifact Registry
- Cloud Run services (backend + frontend)
- Secret Manager entry for the API key

Takes ~10 minutes on first run.

### Step 6 — Push your API key to Secret Manager

```bash
echo -n "sk-ant-...your-key..." | \
  gcloud secrets versions add interview-copilot-api-key --data-file=-
```

### Step 7 — Build and push container images

```bash
# Set your Artifact Registry URL (output from terraform apply)
export REGISTRY=us-central1-docker.pkg.dev/this-terraform/interview-copilot

# Build and push backend
docker build -t $REGISTRY/backend:latest ./backend
docker push $REGISTRY/backend:latest

# Build and push frontend (pass production API URL)
docker build \
  --target production \
  --build-arg VITE_API_URL=https://backend-url-from-cloud-run.run.app \
  -t $REGISTRY/frontend:latest \
  ./frontend
docker push $REGISTRY/frontend:latest
```

### Step 8 — Deploy the new images

```bash
terraform apply -var="image_tag=latest"
```

### Step 9 — Verify

Cloud Run URLs are shown in the Terraform output. Open the frontend URL in your browser and confirm the job manager loads.

For the desktop copilot in production mode, update your local `.env`:

```
COPILOT_API_URL=https://backend-url-from-cloud-run.run.app
```

Then run `python copilot.py` as usual.

---

## Environment Variables Reference

| Variable | Used by | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | copilot.py, backend | Your Claude API key |
| `COPILOT_MODEL` | copilot.py | Claude model (default: haiku) |
| `COPILOT_API_URL` | copilot.py | Backend URL for fetching active job |
| `COPILOT_ANSWER_COOLDOWN` | copilot.py | Seconds mic is muted after an answer |
| `POSTGRES_USER` | docker-compose | DB username |
| `POSTGRES_PASSWORD` | docker-compose | DB password |
| `POSTGRES_DB` | docker-compose | Database name |
| `DATABASE_URL` | backend | Full PostgreSQL connection string |
| `CORS_ORIGINS` | backend | Allowed frontend origins |
| `VITE_API_URL` | frontend | Backend URL for API calls |
| `BACKEND_PORT` | docker-compose | Host port for backend (default 4001) |
| `FRONTEND_PORT` | docker-compose | Host port for frontend (default 4002) |

See `.env.example` for all options with descriptions.

---

## Troubleshooting

**`database "copilot" does not exist`**
Old Docker volume has wrong DB name. Run:
```bash
docker compose down -v && docker compose up --build
```

**Frontend blank at localhost:4002**
Ensure `frontend/index.html` exists at the project root (not inside `public/`).

**`Cannot find module` errors in frontend**
Node modules missing. Rebuild:
```bash
docker compose build frontend && docker compose up frontend
```

**PyAudio install fails on Windows**
```bash
pip install pipwin && pipwin install pyaudio
```

**Copilot doesn't pick up the active job**
- Confirm backend is running: http://localhost:4001/health
- Confirm `COPILOT_API_URL=http://localhost:4001` in `.env`
- Restart `copilot.py` after changing the active job
