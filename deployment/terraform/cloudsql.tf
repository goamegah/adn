# Generate random passwords for database users
resource "random_password" "db_password" {
  for_each = local.deploy_project_ids
  length   = 32
  special  = true
}

# Store passwords in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  for_each  = local.deploy_project_ids
  project   = each.value
  secret_id = "${var.project_name}-db-password-${each.key}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.deploy_project_services]
}

resource "google_secret_manager_secret_version" "db_password" {
  for_each    = local.deploy_project_ids
  secret      = google_secret_manager_secret.db_password[each.key].id
  secret_data = random_password.db_password[each.key].result
}

# Cloud SQL PostgreSQL instances
resource "google_sql_database_instance" "postgres" {
  for_each = local.deploy_project_ids

  name             = "${var.project_name}-db-${each.key}"
  database_version = var.postgres_version
  project          = each.value
  region           = var.region

  settings {
    # ⚠️ IMPORTANT: Augmenter les ressources pour l'import MIMIC-III
    tier              = each.key == "prod" ? "db-custom-4-16384" : "db-custom-2-8192"
    availability_type = each.key == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = each.key == "prod" ? 100 : 50  # Plus d'espace pour MIMIC-III
    disk_type         = "PD_SSD"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = each.key == "prod" ? true : false
      start_time                     = "03:00"
      transaction_log_retention_days = each.key == "prod" ? 7 : 3
      backup_retention_settings {
        retained_backups = each.key == "prod" ? 30 : 7
      }
    }

    ip_configuration {
      # ✅ IP publique TEMPORAIRE pour l'import initial
      # À désactiver après l'import (voir guide)
      ipv4_enabled    = var.enable_public_ip
      private_network = null
      
      # Autoriser uniquement Cloud Build pour l'import
      dynamic "authorized_networks" {
        for_each = var.enable_public_ip ? [{
          name  = "allow-cloud-build"
          value = "0.0.0.0/0"  # ⚠️ À restreindre après l'import
        }] : []
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.value
        }
      }
    }

    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
    }
  }

  # deletion_protection = each.key == "prod" ? true : false

  depends_on = [google_project_service.deploy_project_services]
}

# Create database
resource "google_sql_database" "database" {
  for_each = local.deploy_project_ids

  name     = var.database_name
  instance = google_sql_database_instance.postgres[each.key].name
  project  = each.value
}

# Create database user
resource "google_sql_user" "db_user" {
  for_each = local.deploy_project_ids

  name     = var.database_user
  instance = google_sql_database_instance.postgres[each.key].name
  password = random_password.db_password[each.key].result
  project  = each.value
}

# Grant the application service account access to the database password
resource "google_secret_manager_secret_iam_member" "app_sa_db_password_access" {
  for_each = local.deploy_project_ids

  project   = each.value
  secret_id = google_secret_manager_secret.db_password[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_sa[each.key].email}"
}

# Grant CICD service account access to Cloud SQL
resource "google_project_iam_member" "cicd_cloudsql_client" {
  for_each = local.deploy_project_ids

  project = each.value
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cicd_runner_sa.email}"

  depends_on = [google_project_service.deploy_project_services]
}

# Grant application service account Cloud SQL client role
resource "google_project_iam_member" "app_sa_cloudsql_client" {
  for_each = local.deploy_project_ids

  project = each.value
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app_sa[each.key].email}"

  depends_on = [google_project_service.deploy_project_services]
}

# Grant CICD SA permission to access secrets (for migrations)
resource "google_secret_manager_secret_iam_member" "cicd_db_password_access" {
  for_each = local.deploy_project_ids

  project   = each.value
  secret_id = google_secret_manager_secret.db_password[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}