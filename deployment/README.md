# Deployment

This directory contains the Terraform configurations for provisioning the necessary Google Cloud infrastructure for ADN agent.

## Deployment process overview

![alt text](../assets/deployment_overview.png)


1. CI Pipeline (`.cloudbuild/pr_checks.yaml`):

    - Triggered on pull request creation/update.
    - Runs unit and integration tests to ensure code quality.

2. Staging CD Pipeline (`.cloudbuild/staging.yaml`):

    - Triggered on merge to the main branch.
    - Builds and pushes the application container to Artifact Registry.
    - Deploys the new version to the staging environment.
    - Performs automated load testing against the staging environment.

3. Production Deployment (`.cloudbuild/deploy-to-prod.yaml`):

    - Triggered after a successful staging deployment.
    - Requires manual approval before proceeding to production.
    - Deploys the same container image that was tested in staging to the production environment.

## Resources Provisioning and Deployment

#### Provision Google Cloud resources with Terraform:

```bash
cd deployment/terraform
terraform init --var-file=vars/env.tfvars
terraform plan --var-file=vars/env.tfvars
terraform apply --var-file=vars/env.tfvars
```

#### Upload MIMIC Data
Upload the MIMIC data you can obtain via Kaggle: https://www.kaggle.com/datasets/atamazian/mimic-iii-clinical-dataset-demo, into the Cloud Storage bucket (`adn-app-chn-staging-mimic-data`) created during resource provisioning in the staging project.
Once done, you can:

- Trigger the `import-mimic.yaml` pipeline from `Cloud Build` to import the data into Cloud SQL (for the staging project). This pipeline uses the `import_mimic.py` script located in the `/scripts/` directory.

- Trigger the `staging.yml` pipeline from Cloud Build to deploy the agent and frontend in `Cloud Run` of the staging project.

![alt text](../assets/image.png)

You can then access the Next.js web interface of the ADN agent via the URL provided by Cloud Run once the deployment is complete.

![alt text](../assets/image-4.png)
To do this:
- Give public access to the ADN agent backend from the Cloud Run interface of the staging project.

![alt text](../assets/image-3.png)
- Do the same for the frontend.

The link to the frontend will take you to the following page:

![alt text](../assets/image-2.png)

You can now interact with the ADN agent via this Next.js web interface.

![alt text](../assets/adn_usage.png)
You will find an additional list of ids in the mimic3_ids.csv file with which you can test the ADN agent.
