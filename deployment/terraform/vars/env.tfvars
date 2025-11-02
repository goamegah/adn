# Project name used for resource naming
project_name = "adn-app"

# Your Production Google Cloud project id
prod_project_id = "adn-app-chn-prod"

# Your Staging / Test Google Cloud project id
staging_project_id = "adn-app-chn-staging"

# Your Google Cloud project ID that will be used to host the Cloud Build pipelines.
cicd_runner_project_id = "adn-app-chn-cicd"
# Name of the host connection you created in Cloud Build
host_connection_name = "adn-app-cloudbuild-github-host-connect"
github_pat_secret_id = "adn-app-cloudbuild-github-host-connect-github-oauthtoken-4dce8e"

repository_owner = "goamegah"

# Name of the repository you added to Cloud Build
repository_name = "adn"

# The Google Cloud region you will use to deploy the infrastructure
region = "europe-west1"