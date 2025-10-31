provider "google" {
  region = var.region
  user_project_override = true
}

# corpus data bucket
resource "google_storage_bucket" "bucket_regulation_corpus_cicd" {
  name                        = "${var.cicd_runner_project_id}-${var.project_name}-regulation-corpus-cicd"
  location                    = var.region
  project                     = var.cicd_runner_project_id
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [resource.google_project_service.cicd_services, resource.google_project_service.deploy_project_services]
}

resource "google_storage_bucket" "bucket_regulation_corpus_staging" {
  name                        = "${var.cicd_runner_project_id}-${var.project_name}-regulation-corpus-staging"
  location                    = var.region
  project                     = var.staging_project_id
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [resource.google_project_service.cicd_services, resource.google_project_service.deploy_project_services]
}

resource "google_storage_bucket" "bucket_regulation_corpus_prod" {
  name                        = "${var.cicd_runner_project_id}-${var.project_name}-regulation-corpus-prod"
  location                    = var.region
  project                     = var.prod_project_id
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [resource.google_project_service.cicd_services, resource.google_project_service.deploy_project_services]
}

resource "google_storage_bucket" "bucket_load_test_results" {
  name                        = "${var.cicd_runner_project_id}-${var.project_name}-load-test"
  location                    = var.region
  project                     = var.cicd_runner_project_id
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [resource.google_project_service.cicd_services, resource.google_project_service.deploy_project_services]
}

resource "google_storage_bucket" "logs_data_bucket" {
  for_each                    = toset(local.all_project_ids)
  name                        = "${each.value}-${var.project_name}-logs"
  location                    = var.region
  project                     = each.value
  uniform_bucket_level_access = true
  force_destroy               = true

  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.deploy_project_services]
}

#  

resource "google_artifact_registry_repository" "repo-artifacts-genai" {
  location      = var.region
  repository_id = "${var.project_name}-repo"
  description   = "Repo for Generative AI applications"
  format        = "DOCKER"
  project       = var.cicd_runner_project_id
  depends_on    = [resource.google_project_service.cicd_services, resource.google_project_service.deploy_project_services]
}


