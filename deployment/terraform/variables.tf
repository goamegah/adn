variable "project_name" {
  type        = string
  description = "Project name used as a base for resource naming"
  default     = "adn-agent"
}

variable "prod_project_id" {
  type        = string
  description = "**Production** Google Cloud Project ID for resource deployment."
}

variable "staging_project_id" {
  type        = string
  description = "**Staging** Google Cloud Project ID for resource deployment."
}

variable "cicd_runner_project_id" {
  type        = string
  description = "Google Cloud Project ID where CI/CD pipelines will execute."
}

variable "region" {
  type        = string
  description = "Google Cloud region for resource deployment."
  default     = "europe-west1"
}

variable "host_connection_name" {
  description = "Name of the host connection to create in Cloud Build"
  type        = string
  default     = "Application GitHub Cloud Build"
}

variable "repository_name" {
  description = "Name of the repository you'd like to connect to Cloud Build"
  type        = string
}

variable "telemetry_logs_filter" {
  type        = string
  description = "Log Sink filter for capturing telemetry data. Captures logs with the `traceloop.association.properties.log_type` attribute set to `tracing`."
  default     = "labels.service_name=\"adn-agent\" labels.type=\"agent_telemetry\""
}

variable "feedback_logs_filter" {
  type        = string
  description = "Log Sink filter for capturing feedback data. Captures logs where the `log_type` field is `feedback`."
  default     = "jsonPayload.log_type=\"feedback\""
}

variable "app_sa_roles" {
  description = "List of roles to assign to the application service account"
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/storage.admin",
    "roles/serviceusage.serviceUsageConsumer",
  ]
}

variable "cicd_roles" {
  description = "List of roles to assign to the CICD runner service account in the CICD project"
  type        = list(string)
  default = [
    "roles/run.invoker",
    "roles/storage.admin",
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/artifactregistry.writer",
    "roles/cloudbuild.builds.builder",
    "roles/serviceusage.serviceUsageAdmin",
    "roles/cloudbuild.connectionAdmin"
  ]
}

variable "cicd_sa_deployment_required_roles" {
  description = "List of roles to assign to the CICD runner service account for the Staging and Prod projects."
  type        = list(string)
  default = [
    "roles/run.developer",    
    "roles/iam.serviceAccountUser",
    "roles/aiplatform.user",
    "roles/storage.admin"
  ]
}


variable "repository_owner" {
  description = "Owner of the Git repository - username or organization"
  type        = string
}

variable "github_app_installation_id" {
  description = "GitHub App Installation ID for Cloud Build"
  type        = string
  default     = null
}


variable "github_pat_secret_id" {
  description = "GitHub PAT Secret ID created by gcloud CLI"
  type        = string
  default     = null
}

variable "create_cb_connection" {
  description = "Flag indicating if a Cloud Build connection already exists"
  type        = bool
  default     = true
}

variable "create_repository" {
  description = "Flag indicating whether to create a new Git repository"
  type        = bool
  default     = false
}


# cloud sql variables
variable "database_name" {
  type        = string
  description = "Name of the Cloud SQL database"
  default     = "adn_database"
}
variable "database_user" {
  type        = string
  description = "Cloud SQL database user name"
  default     = "adn_user"
}
variable "database_tier" {
  type        = string
  description = "Cloud SQL instance machine type"
  default     = "db-f1-micro"
}
variable "database_disk_size" {
  type        = number
  description = "Cloud SQL instance disk size in GB"
  default     = 10
}
variable "database_region" {
  type        = string
  description = "Cloud SQL instance region"
  default     = "europe-west1"
}
variable "database_availability_type" {
  type        = string
  description = "Cloud SQL instance availability type"
  default     = "ZONAL"
}
variable "postgres_version" {
  type        = string
  description = "PostgreSQL version for Cloud SQL instance"
  default     = "POSTGRES_14"
}
variable "enable_public_ip" {
  type        = bool
  description = "Flag to enable public IP for Cloud SQL instance"
  default     = true
}
variable "dev_project_id" {
  type        = string
  description = "**Development** Google Cloud Project ID for resource deployment."
  default     = ""
}
