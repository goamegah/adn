variable "project_id" {
  type = string
  description = "Google Project ID"
}

variable "billing_account_id" {
  type = string
  description = "Google Billing Account ID"
}

variable "github_repo" {
  type = string
  description = "Github repo name"
}

variable "region" {
  description = "Région du déploiement (ex: europe-west1)"
  type        = string
}

variable "authorized_ip" {
  description = "Adresse IP autorisée à accéder à l’instance (ex: 123.45.67.89/32)"
  type        = string
}

variable "db_user" {
  description = "Nom d’utilisateur PostgreSQL"
  type        = string
}

variable "db_password" {
  description = "Mot de passe PostgreSQL"
  type        = string
  sensitive   = true
}
