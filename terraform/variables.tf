variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region (e.g. us-central1)"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod"
  }
}

variable "image_tag" {
  description = "Container image tag to deploy (e.g. git SHA or semver)"
  type        = string
  default     = "latest"
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"   # use db-n1-standard-2 for prod
}

variable "db_password" {
  description = "PostgreSQL app user password — store in Secret Manager, not tfvars"
  type        = string
  sensitive   = true
}

variable "backend_max_instances" {
  description = "Maximum Cloud Run instances for backend"
  type        = number
  default     = 5
}

variable "frontend_max_instances" {
  description = "Maximum Cloud Run instances for frontend"
  type        = number
  default     = 3
}

variable "domain" {
  description = "Custom domain (optional — leave empty to use *.run.app URLs)"
  type        = string
  default     = ""
}
