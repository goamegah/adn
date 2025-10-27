# main.tf - Agent 3 (Expert) Deployment on Cloud Run
# Project: AI Diagnostic Navigator
# SOLUTION: Automatic build with Cloud Build

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Provider configuration
provider "google" {
  project = "ai-diagnostic-navigator-475316"
  region  = "us-central1"
}

# Enable required APIs
resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "build_api" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "aiplatform_api" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Service Account for Agent 3
resource "google_service_account" "agent3_sa" {
  account_id   = "agent3-expert-sa"
  display_name = "Service Account for Agent 3 Expert"
}

# Vertex AI permissions
resource "google_project_iam_member" "agent3_aiplatform" {
  project = "ai-diagnostic-navigator-475316"
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent3_sa.email}"
}

# Permissions to read logs
resource "google_project_iam_member" "agent3_logging" {
  project = "ai-diagnostic-navigator-475316"
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent3_sa.email}"
}

# IMPORTANT: This file only creates the infrastructure
# To deploy the code, use gcloud run deploy after terraform apply

# Outputs
output "service_account_email" {
  description = "Email of the created service account"
  value       = google_service_account.agent3_sa.email
}

output "project_id" {
  description = "Project ID"
  value       = "ai-diagnostic-navigator-475316"
}
