################################################
# Terraform configuration
################################################
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
  
  # Backend configuration for GCS
  # NOTE: Uncomment this block AFTER the bucket is created
  # and run: terraform init -migrate-state
  
  backend "gcs" {
    bucket = "terraform-state-ai-diagnostic-navigator-475316-5786e4dc"
    prefix = "bootstrap"
  }
  
}

################################################
# Provider
################################################
provider "google" {
  region = "europe-west1"
  zone   = "europe-west1-b"
}

################################################
# Random ID for unique bucket name
################################################
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

################################################
# GCS Bucket for Terraform State
################################################
resource "google_storage_bucket" "terraform_state" {
  name     = "terraform-state-${var.project_id}-${random_id.bucket_suffix.hex}"
  project  = var.project_id
  location = "EU"

  # Enable versioning for state file history
  versioning {
    enabled = true
  }

  # Lifecycle rules for managing old state versions
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 10
      with_state         = "ARCHIVED"
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90
    }
  }

  # Security settings
  uniform_bucket_level_access = true
  
  # Prevent accidental deletion
  force_destroy = false

  labels = {
    environment = "bootstrap"
    purpose     = "terraform-state"
    managed_by  = "terraform"
  }
}

################################################
# Enable required APIs
################################################
resource "google_project_service" "gcp_services" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "aiplatform.googleapis.com",
    "ml.googleapis.com",
    "compute.googleapis.com",
    "storage.googleapis.com"
  ])

  project = var.project_id
  service = each.key
}

################################################
# Workload Identity Federation Pool
################################################
resource "google_iam_workload_identity_pool" "github_pool" {
  project                   = var.project_id
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Workload Identity Pool for GitHub Actions CI/CD"
  disabled                  = false
}

################################################
# Workload Identity Federation Provider
################################################
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  project                            = var.project_id
  workload_identity_pool_id         = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"
  description                        = "OIDC Provider for GitHub Actions"
  
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }

  # Attribute condition to restrict access to specific repository
  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

################################################
# Service Account for GitHub Actions
################################################
resource "google_service_account" "github_actions" {
  project      = var.project_id
  account_id   = "github-actions-sa"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions CI/CD pipeline"
}

################################################
# IAM Binding for Workload Identity
################################################
resource "google_service_account_iam_member" "github_actions_workload_identity" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}"
}

################################################
# Grant necessary permissions to GitHub Actions SA
################################################
resource "google_project_iam_member" "github_actions_permissions" {
  for_each = toset([
    "roles/viewer",
    "roles/storage.admin",           # For managing GCS buckets
    "roles/iam.serviceAccountUser",   # For impersonating service accounts
    "roles/resourcemanager.projectIamAdmin", # For managing IAM
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

################################################
# Outputs
################################################
output "terraform_state_bucket" {
  value       = google_storage_bucket.terraform_state.name
  description = "The name of the GCS bucket for Terraform state"
}

output "terraform_state_bucket_url" {
  value       = google_storage_bucket.terraform_state.url
  description = "The URL of the GCS bucket for Terraform state"
}

output "workload_identity_provider" {
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  description = "The Workload Identity Provider name for GitHub Actions"
}

output "github_actions_service_account_email" {
  value       = google_service_account.github_actions.email
  description = "The email of the GitHub Actions service account"
}

output "project_id" {
  value       = var.project_id
  description = "The GCP Project ID"
}