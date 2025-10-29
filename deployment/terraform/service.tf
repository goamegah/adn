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

data "google_project" "project" {
  for_each   = local.deploy_project_ids
  project_id = local.deploy_project_ids[each.key]
}

# Cloud Run Service - Staging
resource "google_cloud_run_v2_service" "app_staging" {  
  name                = var.project_name
  location            = var.region
  project             = var.staging_project_id
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  labels = {
    "created-by" = "adk"
    "environment" = "staging"
  }

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
        cpu_idle = false
      }

      # Database configuration
      env {
        name  = "DB_NAME"
        value = var.database_name
      }

      env {
        name  = "DB_USER"
        value = var.database_user
      }

      env {
        name  = "INSTANCE_CONNECTION_NAME"
        value = google_sql_database_instance.postgres["staging"].connection_name
      }

      env {
        name  = "DB_HOST"
        value = google_sql_database_instance.postgres["staging"].public_ip_address
      }

      env {
        name  = "DB_PORT"
        value = "5432"
      }

      # Password from Secret Manager
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password["staging"].secret_id
            version = "latest"
          }
        }
      }

      # Mock mode for tests
      env {
        name  = "USE_MOCK_DB"
        value = "false"
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    service_account                  = google_service_account.app_sa["staging"].email
    max_instance_request_concurrency = 40

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    session_affinity = true

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres["staging"].connection_name]
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }

  depends_on = [
    google_project_service.deploy_project_services,
    google_sql_database_instance.postgres,
    google_secret_manager_secret.db_password
  ]
}

# Cloud Run Service - Production
resource "google_cloud_run_v2_service" "app_prod" {  
  name                = var.project_name
  location            = var.region
  project             = var.prod_project_id
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  labels = {
    "created-by" = "adk"
    "environment" = "production"
  }

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
        cpu_idle = false
      }

      # Database configuration
      env {
        name  = "DB_NAME"
        value = var.database_name
      }

      env {
        name  = "DB_USER"
        value = var.database_user
      }

      env {
        name  = "INSTANCE_CONNECTION_NAME"
        value = google_sql_database_instance.postgres["prod"].connection_name
      }

      env {
        name  = "DB_HOST"
        value = google_sql_database_instance.postgres["prod"].public_ip_address
      }

      env {
        name  = "DB_PORT"
        value = "5432"
      }

      # Password from Secret Manager
      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password["prod"].secret_id
            version = "latest"
          }
        }
      }

      # Mock mode disabled in prod
      env {
        name  = "USE_MOCK_DB"
        value = "false"
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    service_account                  = google_service_account.app_sa["prod"].email
    max_instance_request_concurrency = 40

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    session_affinity = true

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres["prod"].connection_name]
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }

  depends_on = [
    google_project_service.deploy_project_services,
    google_sql_database_instance.postgres,
    google_secret_manager_secret.db_password
  ]
}