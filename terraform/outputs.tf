output "backend_url" {
  description = "Cloud Run backend service URL"
  value       = module.cloud_run.backend_url
}

output "frontend_url" {
  description = "Cloud Run frontend service URL"
  value       = module.cloud_run.frontend_url
}

output "registry_url" {
  description = "Artifact Registry URL for pushing images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "db_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = module.cloud_sql.connection_name
}
