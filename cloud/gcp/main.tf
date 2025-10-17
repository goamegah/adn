################################################
# Terraform Configuration
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
  
  backend "gcs" {
    bucket = "terraform-state-ai-diagnostic-navigator-475316-5786e4dc"
    prefix = "gcp/core"
  }
}

################################################
# Provider Configuration
################################################
provider "google" {
  region = "europe-west1"
  zone   = "europe-west1-b"
}

################################################
# Data Source for Project
################################################
data "google_project" "project" {
  project_id = var.project_id
}

################################################
# Service Account for Terraform Deployer
################################################
resource "google_service_account" "terraform_deployer" {
  account_id   = "terraform-deployer"
  display_name = "Terraform Deployer"
  description  = "Service account for GitHub Actions CI/CD pipeline"
  project      = var.project_id
}

################################################
# IAM Roles for Terraform Deployer
################################################
resource "google_project_iam_member" "terraform_deployer_roles" {
  for_each = toset([
    "roles/run.admin",              # Manage Cloud Run
    "roles/artifactregistry.admin", # Manage Artifact Registry
    "roles/secretmanager.admin",    # Manage Secret Manager
    "roles/iam.serviceAccountUser"  # Impersonate service accounts
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.terraform_deployer.email}"
}

################################################
# Workload Identity Federation Binding
################################################
# Connect GitHub repository to Terraform service account
resource "google_service_account_iam_member" "github_workload_identity" {
  service_account_id = google_service_account.terraform_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${data.google_project.project.number}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${var.github_repo}"
}

################################################
# Service Account for Cloud Run Application
################################################
resource "google_service_account" "cloud_run_app" {
  account_id   = "cloud-run-app"
  display_name = "Cloud Run Application"
  description  = "Service account for the Cloud Run AI Agent application"
  project      = var.project_id
}

################################################
# IAM Roles for Cloud Run Application
################################################
resource "google_project_iam_member" "cloud_run_app_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_app.email}"
}

################################################
# Artifact Registry Repository
################################################
resource "google_artifact_registry_repository" "docker_repo" {
  repository_id = "ai-agent-repo"
  description   = "Docker repository for AI Agent container images"
  format        = "DOCKER"
  location      = "europe-west1"
  project       = var.project_id
}

################################################
# Secret Manager - Dummy API Config
################################################
resource "google_secret_manager_secret" "api_config" {
  secret_id = "api-config"
  project   = var.project_id
  
  replication {
    auto {}
  }
}

# Secret version with dummy data
resource "google_secret_manager_secret_version" "api_config_version" {
  secret = google_secret_manager_secret.api_config.id
  
  secret_data = jsonencode({
    api_key     = "dummy-api-key-replace-in-production"
    environment = "production"
    config      = "dummy-config-value"
  })
}

################################################
# Grant Cloud Run App access to Secret Manager
################################################
resource "google_project_iam_member" "cloud_run_app_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_app.email}"
}

################################################
# Cloud Run v2 Service
################################################
resource "google_cloud_run_v2_service" "ai_agent" {
  name     = "ai-agent-service"
  location = "europe-west1"
  project  = var.project_id
  

  template {
    service_account = google_service_account.cloud_run_app.email
    
    containers {
      name  = "ai-agent"
      image = "europe-west1-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/ai-agent:latest"
      
      # Environment variables
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "GCP_REGION"
        value = "europe-west1"
      }
      
      # Secret from Secret Manager as environment variable
      env {
        name = "API_CONFIG"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.api_config.secret_id
            version = "latest"
          }
        }
      }
      
      # Resources
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      
      # Port configuration
      ports {
        container_port = 8080
      }
    }
    
    # Scaling configuration
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

################################################
# Make Cloud Run service publicly accessible
################################################
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_v2_service.ai_agent.name
  location = google_cloud_run_v2_service.ai_agent.location
  project  = var.project_id
  role     = "roles/run.invoker"
  member   = "allUsers"
}

################################################
# Outputs
################################################
output "cloud_run_url" {
  value       = google_cloud_run_v2_service.ai_agent.uri
  description = "The URL of the deployed Cloud Run service"
}

output "artifact_registry_repository" {
  value       = "europe-west1-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
  description = "The Artifact Registry repository path for docker push"
}