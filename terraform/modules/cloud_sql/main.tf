resource "google_sql_database_instance" "main" {
  name             = "copilot-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true
    disk_size         = 10

    backup_configuration {
      enabled                        = var.environment == "prod"
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "prod"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = var.environment == "prod"
}

resource "google_sql_database" "copilot" {
  name     = "copilot_db"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

resource "google_sql_user" "copilot" {
  name     = "copilot"
  instance = google_sql_database_instance.main.name
  password = var.db_password
  project  = var.project_id
}
