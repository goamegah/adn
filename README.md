# ADN - AI Diagnostic Navigator

> 🏥 **Medical decision support system for emergency situations based on multi-agent artificial intelligence**

[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-1.15.0-4285F4?style=flat)](https://github.com/google/adk-python)


## Architecture Overview

![alt text](assets/architecture_overview.png)

## Agent tools

### Collecteur Agent
**Retrieving patient medical records**: Access and fetch patient data from the MIMIC-III clinical database.

### Synthetiseur Agent  
**Summarizing patient data**: Generate concise summaries of patient medical histories and current conditions.

### Expert Agent
**Providing medical recommendations**: Analyze patient data and offer diagnostic and treatment suggestions based on established medical guidelines.

## Getting Started

### Prerequisites
- Python 3.10+
- GCloud CLI and GCP Account
- Terraform installed
- Agent Development Kit Required Python packages (see pyproject.toml)
- Node.js and npm installed

### Installation

1. **Clone the repository and Install dependencies**:
```bash
git clone https://github.com/goamegah/adn
cd adn
```

2. **Set up Google Cloud SDK and authenticate**:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```
Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

3. **Install Python dependencies for the ADN agent**:
```bash
uv sync
```

3. **Install Node.js dependencies for the Next.js frontend**:
```bash
cd frontend
npm install
```

### Resources Provisioning and Deployment
Please refer to the [Deployment process overview](deployment/README.md#deployment-process-overview) section in the deployment/README.md file for detailed instructions on provisioning Google Cloud resources with Terraform and deploying the ADN agent and frontend.

### Quick Start

#### Clinical Agent
```bash
cd app
adk web
```

## Usage Examples

### ADN Agent

Note: You will find an additional list of ids in the mimic3_ids.csv file with which you can test the ADN agent.


![alt text](assets/adn_usage.png)