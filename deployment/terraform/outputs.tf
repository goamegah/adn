# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

output "database_connection_names" {
  description = "Connection names for Cloud SQL instances (for Cloud Run)"
  value = {
    for k, v in google_sql_database_instance.postgres : k => v.connection_name
  }
}

output "database_ip_addresses" {
  description = "Public IP addresses for Cloud SQL instances"
  value = {
    for k, v in google_sql_database_instance.postgres : k => v.public_ip_address
  }
}

output "database_password_secrets" {
  description = "Secret Manager secret IDs containing database passwords"
  value = {
    for k, v in google_secret_manager_secret.db_password : k => v.secret_id
  }
}

output "database_connection_strings" {
  description = "Connection strings for local/external access"
  value = {
    for k, v in google_sql_database_instance.postgres : k => 
      "postgresql://${var.database_user}:<password>@${v.public_ip_address}:5432/${var.database_name}?sslmode=require"
  }
  sensitive = true
}

output "cloud_run_urls" {
  description = "Cloud Run service URLs"
  value = {
    staging = google_cloud_run_v2_service.app_staging.uri
    prod    = google_cloud_run_v2_service.app_prod.uri
  }
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = google_artifact_registry_repository.repo-artifacts-genai.registry_uri
}

output "database_info" {
  description = "Complete database information"
  value = {
    for k, v in google_sql_database_instance.postgres : k => {
      instance_name      = v.name
      connection_name    = v.connection_name
      public_ip          = v.public_ip_address
      database_version   = v.database_version
      region             = v.region
      database_name      = var.database_name
      database_user      = var.database_user
      secret_name        = google_secret_manager_secret.db_password[k].secret_id
    }
  }
}