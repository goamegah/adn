# Buckets pour stocker les CSV MIMIC-III
resource "google_storage_bucket" "mimic_data_staging" {
  name                        = "${var.staging_project_id}-mimic-data"
  location                    = var.region
  project                     = var.staging_project_id
  uniform_bucket_level_access = true
  force_destroy               = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.deploy_project_services]
}

resource "google_storage_bucket" "mimic_data_prod" {
  name                        = "${var.prod_project_id}-mimic-data"
  location                    = var.region
  project                     = var.prod_project_id
  uniform_bucket_level_access = true
  force_destroy               = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 180
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.deploy_project_services]
}

# Service Account pour l'import
resource "google_service_account" "data_import_sa" {
  account_id   = "${var.project_name}-import"
  display_name = "Data Import Service Account"
  project      = var.cicd_runner_project_id
  depends_on   = [google_project_service.cicd_services]
}

# Permissions pour accéder aux buckets
resource "google_storage_bucket_iam_member" "import_staging_reader" {
  bucket = google_storage_bucket.mimic_data_staging.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.data_import_sa.email}"
}

resource "google_storage_bucket_iam_member" "import_prod_reader" {
  bucket = google_storage_bucket.mimic_data_prod.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.data_import_sa.email}"
}

# Permissions Cloud SQL
resource "google_project_iam_member" "import_cloudsql_client" {
  for_each = local.deploy_project_ids

  project = each.value
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.data_import_sa.email}"
}

# Accès aux secrets DB
resource "google_secret_manager_secret_iam_member" "import_db_password" {
  for_each = local.deploy_project_ids

  project   = each.value
  secret_id = google_secret_manager_secret.db_password[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.data_import_sa.email}"
}

# Permissions pour le CICD SA
resource "google_storage_bucket_iam_member" "cicd_staging_reader" {
  bucket = google_storage_bucket.mimic_data_staging.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}

resource "google_storage_bucket_iam_member" "cicd_prod_reader" {
  bucket = google_storage_bucket.mimic_data_prod.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}