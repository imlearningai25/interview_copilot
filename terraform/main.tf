terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Remote state — replace bucket with your GCS bucket name
  backend "gcs" {
    bucket = "REPLACE_WITH_YOUR_TF_STATE_BUCKET"
    prefix = "interview-copilot/terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ── Enable required APIs ───────────────────────────────────────
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# ── Artifact Registry ─────────────────────────────────────────
resource "google_artifact_registry_repository" "app" {
  repository_id = "interview-copilot"
  format        = "DOCKER"
  location      = var.region
  description   = "Interview Copilot container images"
  depends_on    = [google_project_service.apis]
}

# ── Secret Manager — DB password ──────────────────────────────
resource "google_secret_manager_secret" "db_password" {
  secret_id = "copilot-db-password"
  replication { auto {} }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

# ── Service account for Cloud Run ─────────────────────────────
resource "google_service_account" "cloud_run" {
  account_id   = "copilot-cloud-run"
  display_name = "Interview Copilot Cloud Run SA"
}

resource "google_project_iam_member" "cloud_run_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "cloud_run_secret" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ── Networking module ─────────────────────────────────────────
module "networking" {
  source     = "./modules/networking"
  project_id = var.project_id
  region     = var.region
  depends_on = [google_project_service.apis]
}

# ── Cloud SQL module ──────────────────────────────────────────
module "cloud_sql" {
  source      = "./modules/cloud_sql"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  db_tier     = var.db_tier
  db_password = var.db_password
  network_id  = module.networking.vpc_id
  depends_on  = [module.networking, google_project_service.apis]
}

# ── Cloud Run module ──────────────────────────────────────────
module "cloud_run" {
  source               = "./modules/cloud_run"
  project_id           = var.project_id
  region               = var.region
  environment          = var.environment
  image_tag            = var.image_tag
  registry_url         = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
  db_connection_name   = module.cloud_sql.connection_name
  db_url_secret        = google_secret_manager_secret.db_password.id
  db_name              = module.cloud_sql.db_name
  db_user              = module.cloud_sql.db_user
  db_password          = var.db_password
  vpc_connector        = module.networking.vpc_connector_id
  service_account      = google_service_account.cloud_run.email
  backend_max_instances  = var.backend_max_instances
  frontend_max_instances = var.frontend_max_instances
  domain               = var.domain
  depends_on           = [module.cloud_sql, google_project_service.apis]
}
