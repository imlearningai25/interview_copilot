variable "project_id"             { type = string }
variable "region"                 { type = string }
variable "environment"            { type = string }
variable "image_tag"              { type = string }
variable "registry_url"           { type = string }
variable "db_connection_name"     { type = string }
variable "db_url_secret"          { type = string }
variable "db_name"                { type = string }
variable "db_user"                { type = string }
variable "db_password"            { type = string; sensitive = true }
variable "vpc_connector"          { type = string }
variable "service_account"        { type = string }
variable "backend_max_instances"  { type = number; default = 5 }
variable "frontend_max_instances" { type = number; default = 3 }
variable "domain"                 { type = string; default = "" }
