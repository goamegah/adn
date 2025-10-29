# Project name used for resource naming
project_name = "adn-agent"

# Your Production Google Cloud project id
prod_project_id = "adn-chn-prod"

# Your Staging / Test Google Cloud project id
staging_project_id = "adn-chn-staging"

# Your Google Cloud project ID that will be used to host the Cloud Build pipelines.
cicd_runner_project_id = "adn-chn-cicd"

# Name of the host connection you created in Cloud Build
host_connection_name = "adn-cloudbuild-github-connect"
github_pat_secret_id = "adn-cloudbuild-github-connect-github-oauthtoken-f816b5"

repository_owner = "goamegah"

# Name of the repository you added to Cloud Build
repository_name = "adn"

# The Google Cloud region you will use to deploy the infrastructure
region = "europe-west1"

# Cloud SQL Configuration
postgres_version = "POSTGRES_15"
db_tier          = "db-g1-small"
db_disk_size     = 10
database_name    = "app_db"
database_user    = "app_user"
enable_public_ip = true  # ⚠️ AJOUTÉ - Important pour l'accès initial