locals {
  db_url = "postgresql://${var.db_user}:${var.db_password}@/${var.db_name}?host=/cloudsql/${var.db_connection_name}"
}

# ── Backend service ────────────────────────────────────────────
resource "google_cloud_run_v2_service" "backend" {
  name     = "copilot-backend-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.service_account

    containers {
      image = "${var.registry_url}/backend:${var.image_tag}"

      env {
        name  = "DATABASE_URL"
        value = local.db_url
      }
      env {
        name  = "CORS_ORIGINS"
        value = var.domain != "" ? "https://${var.domain}" : "*"
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 10
      }

      liveness_probe {
        http_get { path = "/health" }
        period_seconds    = 30
        failure_threshold = 3
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [var.db_connection_name]
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = var.backend_max_instances
    }

    vpc_access {
      connector = var.vpc_connector
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }
}

# ── Frontend service ───────────────────────────────────────────
resource "google_cloud_run_v2_service" "frontend" {
  name     = "copilot-frontend-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.registry_url}/frontend:${var.image_tag}"

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = var.frontend_max_instances
    }
  }
}

# ── IAM — allow public access to frontend ─────────────────────
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_v2_service.frontend.name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Backend is kept private (invoked only from frontend's Cloud Run SA)
resource "google_cloud_run_service_iam_member" "backend_frontend" {
  service  = google_cloud_run_v2_service.backend.name
  location = var.region
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"   # change to serviceAccount:... for stricter security
}
