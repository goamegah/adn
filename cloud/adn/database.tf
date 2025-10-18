##########################################################
# 🚀 ADN - Google Cloud SQL PostgreSQL Setup
##########################################################

resource "google_project_service" "sqlapi" {
    project = var.project_id
    service = "sqladmin.googleapis.com"
}

##########################################################
# 📘 Instance Cloud SQL PostgreSQL
##########################################################
resource "google_sql_database_instance" "adn_postgres_instance" {
  name             = "adn-postgres-instance"
  project = var.project_id

  region           = var.region
  database_version = "POSTGRES_15"

  settings {
    tier            = "db-f1-micro"
    disk_size       = 10
    disk_type       = "PD_SSD"
    availability_type = "ZONAL"

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    # maintenance_window {
    #   day  = 7  # dimanche
    #   hour = 3
    # }

    ip_configuration {
      ipv4_enabled = true

      # ✅ Correct: authorized_networks doit être un bloc interne
      dynamic "authorized_networks" {
        for_each = var.authorized_ip != "" ? [var.authorized_ip] : []
        content {
          name  = "allowed-network"
          value = authorized_networks.value
        }
      }
    }
  }

  deletion_protection = false
}

##########################################################
# 🗃️ Base de données principale
##########################################################
resource "google_sql_database" "adn_database" {
    project = var.project_id
    name     = "adn_emergency_db"
    instance = google_sql_database_instance.adn_postgres_instance.name
}

##########################################################
# 👤 Utilisateur PostgreSQL
##########################################################
resource "google_sql_user" "adn_db_user" {
    project = var.project_id
    name     = var.db_user
    instance = google_sql_database_instance.adn_postgres_instance.name
    password = var.db_password
}

##########################################################
# Initialisation Tables
##########################################################
resource "null_resource" "initialize_db" {
  provisioner "local-exec" {
    command = "psql postgresql://${var.db_user}:${var.db_password}@${google_sql_database_instance.adn_postgres_instance.public_ip_address}/${google_sql_database.adn_database.name} -f ./init_db.sql"
  }
  depends_on = [google_sql_database.adn_database]
}


##########################################################
# 📤 Sorties utiles
##########################################################
output "db_connection_name" {
    value = google_sql_database_instance.adn_postgres_instance.connection_name
}

output "db_public_ip" {
    value = google_sql_database_instance.adn_postgres_instance.public_ip_address
}

output "db_user" {
    value = google_sql_user.adn_db_user.name
}

output "db_name" {
    value = google_sql_database.adn_database.name
}
