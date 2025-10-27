# main.tf - Agent 2 (Synthesizer) Deployment on Cloud Run
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

# Service Account for Agent 2
resource "google_service_account" "agent2_sa" {
  account_id   = "agent2-synthetiseur-sa"
  display_name = "Service Account for Agent 2 Synthesizer"
}

# Vertex AI permissions
resource "google_project_iam_member" "agent2_aiplatform" {
  project = "ai-diagnostic-navigator-475316"
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent2_sa.email}"
}

# Permissions to read logs
resource "google_project_iam_member" "agent2_logging" {
  project = "ai-diagnostic-navigator-475316"
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent2_sa.email}"
}

# IMPORTANT: This file only creates the infrastructure
# To deploy the code, use gcloud run deploy after terraform apply

# Outputs
output "service_account_email" {
  description = "Email of the created service account"
  value       = google_service_account.agent2_sa.email
}

output "project_id" {
  description = "Project ID"
  value       = "ai-diagnostic-navigator-475316"
}

output "next_steps" {
  description = "Next steps"
  value = <<-EOT
  
  ✅ Infrastructure created successfully!
  
  Now, deploy your code with this command:
  
  gcloud run deploy agent2-synthetiseur \
    --source . \
    --region us-central1 \
    --project ai-diagnostic-navigator-475316 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --service-account ${google_service_account.agent2_sa.email}
  
  EOT
}
