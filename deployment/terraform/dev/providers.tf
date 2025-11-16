terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "> 7.0.0"
    }
  }
}

provider "google" {
  alias                 = "dev_billing_override"
  billing_project       = var.dev_project_id
  region = var.region
  user_project_override = true
}
