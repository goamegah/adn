# a. Create PR checks trigger
resource "google_cloudbuild_trigger" "pr_checks" {
  name            = "pr-${var.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for PR checks"
  service_account = resource.google_service_account.cicd_runner_sa.id

  repository_event_config {
    repository = "projects/${var.cicd_runner_project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
    pull_request {
      branch = "main"
    }
  }

  filename = ".cloudbuild/pr_checks.yaml"
  included_files = [
    "app/**",
    "tests/**",
    "deployment/**",
    "uv.lock",
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  depends_on = [
    resource.google_project_service.cicd_services, 
    resource.google_project_service.deploy_project_services, 
    google_cloudbuildv2_connection.github_connection, 
    google_cloudbuildv2_repository.repo
  ]
}

# b. Create CD pipeline trigger
resource "google_cloudbuild_trigger" "cd_pipeline" {
  name            = "cd-${var.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  service_account = resource.google_service_account.cicd_runner_sa.id
  description     = "Trigger for CD pipeline"

  repository_event_config {
    repository = "projects/${var.cicd_runner_project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
    push {
      branch = "main"
    }
  }

  filename = ".cloudbuild/staging.yaml"
  included_files = [
    "app/**",
    "tests/**",
    "deployment/**",
    "uv.lock"
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  substitutions = {
    _STAGING_PROJECT_ID            = var.staging_project_id
    _BUCKET_NAME_LOAD_TEST_RESULTS = resource.google_storage_bucket.bucket_load_test_results.name
    _LOGS_BUCKET_NAME_STAGING      = resource.google_storage_bucket.logs_data_bucket[var.staging_project_id].url
    _REGION                        = var.region

    _CONTAINER_NAME                = var.project_name
    _ARTIFACT_REGISTRY_REPO_NAME   = resource.google_artifact_registry_repository.repo-artifacts-genai.repository_id


    # Your other CD Pipeline substitutions
  }
  depends_on = [
    resource.google_project_service.cicd_services, 
    resource.google_project_service.deploy_project_services, 
    google_cloudbuildv2_connection.github_connection, 
    google_cloudbuildv2_repository.repo
  ]

}

# c. Create Deploy to production trigger
resource "google_cloudbuild_trigger" "deploy_to_prod_pipeline" {
  name            = "deploy-${var.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for deployment to production"
  service_account = resource.google_service_account.cicd_runner_sa.id
  repository_event_config {
    repository = "projects/${var.cicd_runner_project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
  }
  filename = ".cloudbuild/deploy-to-prod.yaml"
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  approval_config {
    approval_required = true
  }
  substitutions = {
    _PROD_PROJECT_ID             = var.prod_project_id
    _LOGS_BUCKET_NAME_PROD       = resource.google_storage_bucket.logs_data_bucket[var.prod_project_id].url
    _REGION                      = var.region

    _CONTAINER_NAME              = var.project_name
    _ARTIFACT_REGISTRY_REPO_NAME = resource.google_artifact_registry_repository.repo-artifacts-genai.repository_id


    # Your other Deploy to Prod Pipeline substitutions
  }
  depends_on = [
    resource.google_project_service.cicd_services, 
    resource.google_project_service.deploy_project_services, 
    google_cloudbuildv2_connection.github_connection, 
    google_cloudbuildv2_repository.repo
  ]

}

# e. create Import MIMIC trigger
resource "google_cloudbuild_trigger" "import_mimic_staging_trigger" {
  name            = "import-mimic-staging-${var.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for importing MIMIC-III data to staging"
  service_account = resource.google_service_account.cicd_runner_sa.id

  repository_event_config {
    repository = "projects/${var.cicd_runner_project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
  }
  filename = ".cloudbuild/import-mimic.yaml"
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  substitutions = {
    _ENV                = "staging"
    _TARGET_PROJECT_ID  = var.staging_project_id
    _DATA_BUCKET        = google_storage_bucket.mimic_data_staging.name
    _SUBSET_FLAG        = ""  # Vide = import complet, ou "--subset 5" pour test

    _CONTAINER_NAME     = var.project_name
  }
  depends_on = [
    resource.google_project_service.cicd_services, 
    resource.google_project_service.deploy_project_services, 
    google_cloudbuildv2_connection.github_connection, 
    google_cloudbuildv2_repository.repo,
    google_storage_bucket.mimic_data_staging
  ]
}

# e. create Import MIMIC to prod trigger
resource "google_cloudbuild_trigger" "import_mimic_prod_trigger" {
  name            = "import-mimic-prod-${var.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for importing MIMIC-III data to prod"
  service_account = resource.google_service_account.cicd_runner_sa.id
  repository_event_config {
    repository = "projects/${var.cicd_runner_project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
  }
  filename = ".cloudbuild/import-mimic.yaml"
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  substitutions = {
    _ENV                = "prod"
    _TARGET_PROJECT_ID  = var.prod_project_id
    _DATA_BUCKET        = google_storage_bucket.mimic_data_prod.name
    _SUBSET_FLAG        = ""  # Vide = import complet, ou "--subset 5" pour test

    _CONTAINER_NAME     = var.project_name
  }
  depends_on = [
    resource.google_project_service.cicd_services, 
    resource.google_project_service.deploy_project_services, 
    google_cloudbuildv2_connection.github_connection, 
    google_cloudbuildv2_repository.repo,
    google_storage_bucket.mimic_data_prod
  ]
}