output "connection_name" { value = google_sql_database_instance.main.connection_name }
output "private_ip"     { value = google_sql_database_instance.main.private_ip_address }
output "db_name"        { value = google_sql_database.copilot.name }
output "db_user"        { value = google_sql_user.copilot.name }
